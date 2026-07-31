"""通用自定义生图 API - 用户自己的内部 API 走这里。

请求约定（可按你的后端调整）：
POST {base_url}/images/generations
{
  "model": "...",
  "prompt": "...",
  "negative_prompt": "...",
  "width": 1024,
  "height": 1024,
  "n": 1,
  "reference_images": ["data:..."]
}
Response:
{
  "url": "https://...",
  "b64": "...",
  "width": 1024,
  "height": 1024
}
"""
import base64
from typing import Any, Dict, List, Optional

import httpx

from app.services.image_service import ImageGenerationProvider


class CustomProvider(ImageGenerationProvider):
    name = "custom"

    def __init__(self, base_url: str, api_key: str, model: str):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model

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
        if not self.base_url:
            raise RuntimeError("IMAGE_BASE_URL 未配置")
        if not self.api_key:
            raise RuntimeError("IMAGE_API_KEY 未配置")

        payload: Dict[str, Any] = {
            "model": self.model,
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "width": width,
            "height": height,
            "n": 1,
        }
        if reference_images:
            payload["reference_images"] = reference_images
        if seed is not None:
            payload["seed"] = seed
        if extra:
            payload.update(extra)

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=180) as client:
            resp = await client.post(
                f"{self.base_url}/images/generations",
                json=payload,
                headers=headers,
            )
            resp.raise_for_status()
            data = resp.json()

        # 兼容多种返回结构
        first = None
        if isinstance(data, dict):
            if "data" in data and data["data"]:
                first = data["data"][0]
            elif "url" in data or "b64_json" in data or "b64" in data:
                first = data
        if not first:
            raise RuntimeError(f"生图 API 返回结构未识别: {data}")

        result: Dict[str, Any] = {
            "url": first.get("url") or "",
            "b64": first.get("b64_json") or first.get("b64") or "",
            "width": first.get("width") or width,
            "height": first.get("height") or height,
            "model": self.model,
            "raw": data,
        }
        return result
