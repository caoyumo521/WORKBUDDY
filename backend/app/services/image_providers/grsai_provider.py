"""GRsai 生图 Provider（draw/completions 流式接口）。

GRsai 的生图接口不是 OpenAI 兼容的 /images/generations，而是自建的流式任务接口：
  POST {base_url}/draw/completions
  body: {"model": "gpt-image-2", "prompt": "...", "n": 1, "size": "WxH"}
  返回: SSE 流式，每行 `data: {json}`；中间事件 status="running" + progress(1..100)，
        终态事件 status="succeeded"（results=[{"url": "..."}]）或 status="failed"。
        若 model 缺失/不支持，返回单个 JSON（非流式）：{"code":-1,"data":null,"msg":"model not found"}

本 provider 解析流式响应，等任务 succeeded 后从 results[0].url 取图。
注意：GRsai draw/completions 为文生图接口，暂不支持参考图编辑（reference_images）。
"""
import asyncio
import json
import logging
from typing import Any, Dict, List, Optional

import httpx

from app.services.image_service import ImageGenerationProvider
from app.services.image_providers.openai_provider import ImageAPIError

logger = logging.getLogger(__name__)

# 生成超时（GRsai 实测 ~37-60s，留足余量）
TIMEOUT = 180


class GrsaiProvider(ImageGenerationProvider):
    name = "grsai"

    def __init__(self, base_url: str, api_key: str, model: str):
        self.base_url = (base_url or "").rstrip("/")
        self.api_key = api_key
        self.model = model or "gpt-image-2"

    @property
    def endpoint(self) -> str:
        # base_url 形如 https://grsai.dakka.com.cn/v1，路径为 /draw/completions
        return f"{self.base_url}/draw/completions"

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
            raise RuntimeError("GRsai API Key 未配置")
        if not self.base_url:
            raise RuntimeError("GRsai base_url 未配置")

        # GRsai 为文生图接口，不支持参考图编辑：有参考图时显式跳过，交给 MultiRelay 的下一个中转
        if reference_images:
            raise RuntimeError("GRsai 中转暂不支持参考图编辑，已跳过")

        size = f"{width}x{height}"
        payload: Dict[str, Any] = {
            "model": self.model,
            "prompt": prompt,
            "n": 1,
            "size": size,
        }
        if negative_prompt:
            payload["negative_prompt"] = negative_prompt
        if seed is not None:
            payload["seed"] = seed

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        last_event: Optional[Dict[str, Any]] = None
        data_events: List[Dict[str, Any]] = []
        raw_lines: List[str] = []

        try:
            async with httpx.AsyncClient(timeout=TIMEOUT) as client:
                async with client.stream(
                    "POST", self.endpoint, json=payload, headers=headers
                ) as resp:
                    if resp.status_code != 200:
                        body = await resp.aread()
                        raise ImageAPIError(
                            f"HTTP {resp.status_code}: {body[:200].decode('utf-8', 'ignore')}",
                            status_code=resp.status_code,
                        )
                    async for line in resp.aiter_lines():
                        if not line:
                            continue
                        if line.startswith("data:"):
                            chunk = line[5:].strip()
                            if not chunk:
                                continue
                            try:
                                od = json.loads(chunk)
                            except Exception:
                                logger.warning("GRsai 非 JSON 流片段: %s", chunk[:120])
                                continue
                            data_events.append(od)
                            last_event = od
                        else:
                            raw_lines.append(line)
        except httpx.TimeoutException as e:
            raise ImageAPIError(f"GRsai 请求超时: {e}", status_code=0)
        except httpx.ConnectError as e:
            raise ImageAPIError(f"GRsai 连接失败: {e}", status_code=0)

        # 情况 A：非流式单 JSON（如 model 缺失/不支持）
        if not data_events:
            text = "\n".join(raw_lines).strip()
            if not text:
                raise ImageAPIError("GRsai 返回为空", status_code=0)
            try:
                obj = json.loads(text)
                code = obj.get("code")
                msg = obj.get("msg") or obj.get("message") or ""
                if code not in (0, None) or obj.get("error"):
                    raise ImageAPIError(
                        f"GRsai 错误: {msg or obj.get('error')}", status_code=0
                    )
            except ImageAPIError:
                raise
            except Exception:
                raise ImageAPIError(f"GRsai 返回无法解析: {text[:200]}", status_code=0)

        # 情况 B：流式事件
        if last_event is None:
            raise ImageAPIError("GRsai 流未返回任何事件", status_code=0)

        status = last_event.get("status")
        if status == "failed":
            reason = last_event.get("error") or last_event.get("failure_reason") or "未知失败"
            raise ImageAPIError(f"GRsai 生图失败: {reason}", status_code=0)

        results = last_event.get("results") or []
        if status != "succeeded" or not results:
            raise ImageAPIError(
                f"GRsai 未成功（status={status}）", status_code=0
            )

        first = results[0] if isinstance(results, list) else results
        url = first.get("url", "") if isinstance(first, dict) else ""
        if not url:
            raise ImageAPIError("GRsai 返回成功但无图片 URL", status_code=0)

        return {
            "url": url,
            "b64": "",
            "width": width,
            "height": height,
            "model": self.model,
            "provider": self.name,
            "raw": last_event,
        }
