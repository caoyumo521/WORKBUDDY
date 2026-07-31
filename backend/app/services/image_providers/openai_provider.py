"""OpenAI Image API Provider

同时支持：
  - DALL·E 3 (dall-e-3): 经典文生图
  - GPT Image 2 (gpt-image-2): 最新一代多模态生图，支持参考图编辑
  - GPT Image 1 (gpt-image-1): 新一代多模态生图，支持参考图编辑

两种模型 API 差异：
  ┌──────────────┬────────────────────────────┬──────────────────────────────────┐
  │              │ dall-e-3                   │ gpt-image-2 / gpt-image-1        │
  ├──────────────┼────────────────────────────┼──────────────────────────────────┤
  │ size         │ 1024x1024 / 1792x1024 /    │ 1024x1024 / 1024x1536 /          │
  │              │ 1024x1792                  │ 1536x1024 / auto                 │
  │ quality      │ standard / hd             │ low / medium / high / auto       │
  │ output       │ url / b64_json            │ b64_json（固定，不支持 url）      │
  │ response_fmt │ 支持 response_format       │ 不支持 response_format（会报错）  │
  │ 参考图       │ 不支持                    │ 支持 via /images/edits 端点      │
  │ output_fmt   │ 不支持                    │ png / jpeg / webp                │
  └──────────────┴────────────────────────────┴──────────────────────────────────┘

错误处理 & 重试：
  - 5xx 错误（渠道不可用、服务端临时故障）自动重试，指数退避
  - 4xx 错误（参数错误、鉴权失败）不重试，直接抛出
  - 上游返回的 error.message 会被提取并传递到前端
"""
import asyncio
import base64
import io
import logging
from typing import Any, Dict, List, Optional

import httpx

from app.services.image_service import ImageGenerationProvider

logger = logging.getLogger(__name__)

# 5xx 重试配置
MAX_RETRIES = 3
RETRY_BASE_DELAY = 2.0  # 秒，指数退避基数
RETRY_STATUS_CODES = {500, 502, 503, 504}


class ImageAPIError(RuntimeError):
    """生图 API 错误，携带上游返回的详细信息。"""

    def __init__(self, message: str, status_code: int = 0, raw_body: str = ""):
        self.status_code = status_code
        self.raw_body = raw_body
        super().__init__(message)


def _extract_api_error(resp: httpx.Response) -> ImageAPIError:
    """从 HTTP 错误响应中提取可读错误信息。"""
    status = resp.status_code
    body_text = resp.text[:500] if resp.text else ""

    # 尝试解析 JSON 格式的错误体
    err_msg = ""
    try:
        body = resp.json()
        err_obj = body.get("error", body)
        if isinstance(err_obj, dict):
            err_msg = err_obj.get("message", "")
            err_code = err_obj.get("code", "")
            if err_code and err_code not in err_msg:
                err_msg = f"[{err_code}] {err_msg}" if err_msg else err_code
        elif isinstance(err_obj, str):
            err_msg = err_obj
    except Exception:
        err_msg = body_text

    if not err_msg:
        err_msg = f"HTTP {status}"

    return ImageAPIError(err_msg, status_code=status, raw_body=body_text)


class OpenAIProvider(ImageGenerationProvider):
    name = "openai"

    def __init__(self, base_url: str, api_key: str, model: str):
        self.base_url = base_url.rstrip("/") or "https://api.openai.com/v1"
        self.api_key = api_key
        self.model = model or "dall-e-3"

    @property
    def is_gpt_image(self) -> bool:
        """判断是否为 gpt-image 系列模型（gpt-image-1 / gpt-image-2）。"""
        return "gpt-image" in self.model.lower()

    def _map_size_dalle3(self, width: int, height: int) -> str:
        """DALL·E 3 只支持 3 种尺寸，找最近的。"""
        candidates = [(1024, 1024), (1792, 1024), (1024, 1792)]
        best = min(candidates, key=lambda c: abs(c[0] - width) + abs(c[1] - height))
        return f"{best[0]}x{best[1]}"

    def _map_size_gpt_image(self, width: int, height: int) -> str:
        """gpt-image 支持 1024x1024 / 1024x1536 / 1536x1024 / auto。"""
        if width == height:
            return "1024x1024"
        # 竖版
        if height > width:
            return "1024x1536"
        # 横版
        return "1536x1024"

    def _map_quality(self, extra: Optional[Dict[str, Any]] = None) -> str:
        """resolution → quality 映射。

        1K → low (最快)
        2K → medium (标准)
        4K → high (最高清)
        """
        if extra and extra.get("quality"):
            return extra["quality"]
        resolution = (extra or {}).get("resolution", "2K")
        return {"1K": "low", "2K": "medium", "4K": "high"}.get(resolution, "medium")

    async def generate(
        self,
        prompt: str,
        *,
        negative_prompt: str = "",
        width: int = 1024,
        height: int = 1024,
        reference_images: Optional[List[str]] = None,
        seed: Optional[int] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        if not self.api_key:
            raise RuntimeError("IMAGE_API_KEY 未配置")

        extra = extra or {}

        # ---- 路由：有参考图 + gpt-image-1 → 走 /images/edits ----
        if reference_images and self.is_gpt_image:
            return await self._generate_with_edit(
                prompt, reference_images, width, height, extra
            )

        # ---- 常规文生图 ----
        if self.is_gpt_image:
            return await self._generate_gpt_image(prompt, width, height, extra)
        else:
            return await self._generate_dalle3(prompt, width, height, extra)

    # ==================== gpt-image-1 文生图 ====================

    async def _generate_gpt_image(
        self,
        prompt: str,
        width: int,
        height: int,
        extra: Dict[str, Any],
    ) -> Dict[str, Any]:
        """gpt-image 系列文生图（gpt-image-1 / gpt-image-2）。"""
        size = self._map_size_gpt_image(width, height)
        quality = self._map_quality(extra)
        output_format = extra.get("output_format", "png")

        payload: Dict[str, Any] = {
            "model": self.model,
            "prompt": prompt,
            "n": 1,
            "size": size,
            "quality": quality,
            "output_format": output_format,
        }
        # gpt-image 支持 background 参数
        if extra.get("background"):
            payload["background"] = extra["background"]

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        data = await self._post_with_retry(
            f"{self.base_url}/images/generations",
            json_payload=payload,
            headers=headers,
        )

        first = (data.get("data") or [{}])[0]
        w, h = (int(x) for x in size.split("x"))
        b64 = first.get("b64_json", "")
        url = first.get("url", "")

        return {
            "url": url,
            "b64": b64,
            "width": w,
            "height": h,
            "model": self.model,
            "raw": data,
        }

    # ==================== gpt-image-1 图生图（参考图编辑） ====================

    async def _generate_with_edit(
        self,
        prompt: str,
        reference_images: List[str],
        width: int,
        height: int,
        extra: Dict[str, Any],
    ) -> Dict[str, Any]:
        """gpt-image 系列参考图编辑 - 走 /images/edits 端点。

        reference_images 中的每项可以是：
          - data:image/png;base64,xxxx  （完整 data URI）
          - 纯 base64 字符串
          - 本地文件路径（会自动读取）
        """
        size = self._map_size_gpt_image(width, height)
        quality = self._map_quality(extra)
        output_format = extra.get("output_format", "png")

        # 准备 multipart form
        files = []
        for i, img in enumerate(reference_images[:4]):  # 最多 4 张参考图
            img_bytes = self._resolve_image_bytes(img)
            files.append(("image[]", (f"ref_{i}.png", img_bytes, "image/png")))

        data = {
            "model": self.model,
            "prompt": prompt,
            "n": "1",
            "size": size,
            "quality": quality,
            "output_format": output_format,
        }

        headers = {"Authorization": f"Bearer {self.api_key}"}

        result = await self._post_with_retry(
            f"{self.base_url}/images/edits",
            data_payload=data,
            files_payload=files,
            headers=headers,
        )

        first = (result.get("data") or [{}])[0]
        w, h = (int(x) for x in size.split("x"))
        b64 = first.get("b64_json", "")
        url = first.get("url", "")

        return {
            "url": url,
            "b64": b64,
            "width": w,
            "height": h,
            "model": self.model,
            "raw": result,
        }

    @staticmethod
    def _resolve_image_bytes(img: str) -> bytes:
        """将各种格式的图片引用统一转为 bytes。"""
        if img.startswith("data:"):
            # data:image/png;base64,xxxx
            header, b64 = img.split(",", 1)
            return base64.b64decode(b64)
        if img.startswith("/"):
            # 本地文件路径
            with open(img, "rb") as f:
                return f.read()
        # 纯 base64
        return base64.b64decode(img)

    # ==================== 统一 POST + 重试 ====================

    async def _post_with_retry(
        self,
        url: str,
        *,
        json_payload: Optional[Dict[str, Any]] = None,
        data_payload: Optional[Dict[str, Any]] = None,
        files_payload: Optional[list] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: int = 300,
    ) -> Dict[str, Any]:
        """带自动重试的 POST 请求。

        - 5xx 错误：指数退避重试（最多 MAX_RETRIES 次）
        - 4xx 错误：不重试，直接抛 ImageAPIError
        - 网络超时/连接错误：重试
        - 成功：返回 JSON dict

        所有错误都会提取上游 error.message，抛出 ImageAPIError。
        """
        last_error: Optional[Exception] = None

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                async with httpx.AsyncClient(timeout=timeout) as client:
                    if json_payload is not None:
                        resp = await client.post(url, json=json_payload, headers=headers)
                    else:
                        resp = await client.post(
                            url,
                            data=data_payload,
                            files=files_payload,
                            headers=headers,
                        )

                if resp.status_code < 400:
                    return resp.json()

                # 提取上游错误信息
                api_err = _extract_api_error(resp)

                # 4xx 不重试
                if resp.status_code not in RETRY_STATUS_CODES:
                    raise api_err

                # 5xx 可重试
                last_error = api_err
                logger.warning(
                    "生图 API 返回 %d (attempt %d/%d): %s",
                    resp.status_code, attempt, MAX_RETRIES, api_err.args[0],
                )

            except httpx.TimeoutException as e:
                last_error = ImageAPIError(f"请求超时: {e}", status_code=0)
                logger.warning("生图 API 超时 (attempt %d/%d)", attempt, MAX_RETRIES)
            except httpx.ConnectError as e:
                last_error = ImageAPIError(f"连接失败: {e}", status_code=0)
                logger.warning("生图 API 连接失败 (attempt %d/%d)", attempt, MAX_RETRIES)
            except ImageAPIError:
                raise  # 4xx 直接抛
            except Exception as e:
                last_error = ImageAPIError(f"未知错误: {e}", status_code=0)
                logger.warning("生图 API 未知错误 (attempt %d/%d): %s", attempt, MAX_RETRIES, e)

            # 最后一次不再等待
            if attempt < MAX_RETRIES:
                delay = RETRY_BASE_DELAY * (2 ** (attempt - 1))
                logger.info("等待 %.1fs 后重试...", delay)
                await asyncio.sleep(delay)

        # 所有重试用完
        if last_error:
            raise last_error
        raise ImageAPIError("重试次数已用完", status_code=0)

    # ==================== DALL·E 3 文生图（兼容旧模型） ====================

    async def _generate_dalle3(
        self,
        prompt: str,
        width: int,
        height: int,
        extra: Dict[str, Any],
    ) -> Dict[str, Any]:
        """DALL·E 3 文生图。"""
        size = self._map_size_dalle3(width, height)
        quality = "hd" if (extra or {}).get("resolution", "2K") in ("4K",) else "standard"

        payload: Dict[str, Any] = {
            "model": self.model,
            "prompt": prompt,
            "n": 1,
            "size": size,
            "quality": quality,
            "response_format": "b64_json",
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        data = await self._post_with_retry(
            f"{self.base_url}/images/generations",
            json_payload=payload,
            headers=headers,
            timeout=180,
        )

        first = (data.get("data") or [{}])[0]
        w, h = (int(x) for x in size.split("x"))
        return {
            "url": first.get("url", ""),
            "b64": first.get("b64_json", ""),
            "width": w,
            "height": h,
            "model": self.model,
            "raw": data,
        }
