"""Flux provider (Black Forest Labs API) 占位实现。"""
from typing import Any, Dict, List, Optional

import httpx

from app.services.image_service import ImageGenerationProvider


class FluxProvider(ImageGenerationProvider):
    name = "flux"

    def __init__(self, base_url: str, api_key: str, model: str):
        # BFL 默认 https://api.bfl.ml/v1
        self.base_url = (base_url or "https://api.bfl.ml/v1").rstrip("/")
        self.api_key = api_key
        self.model = model or "flux-pro-1.1"

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

        payload: Dict[str, Any] = {
            "prompt": prompt,
            "width": width,
            "height": height,
        }
        if seed is not None:
            payload["seed"] = seed

        headers = {"x-key": self.api_key, "Content-Type": "application/json"}

        async with httpx.AsyncClient(timeout=180) as client:
            r = await client.post(
                f"{self.base_url}/{self.model}", json=payload, headers=headers
            )
            r.raise_for_status()
            data = r.json()

        # Flux 异步返回 task_url，需轮询
        task_url = data.get("task_url") or data.get("id")
        if not task_url:
            raise RuntimeError(f"Flux 返回结构异常: {data}")

        # 简单轮询
        for _ in range(60):
            pr = await client.get(task_url, headers=headers)
            pd = pr.json()
            status = pd.get("status")
            if status == "Ready":
                sample = pd.get("result", {}).get("sample") or pd.get("sample")
                return {
                    "url": sample or "",
                    "b64": "",
                    "width": width,
                    "height": height,
                    "model": self.model,
                    "raw": pd,
                }
            if status in ("Error", "Failed"):
                raise RuntimeError(f"Flux 任务失败: {pd}")
            import asyncio
            await asyncio.sleep(2)
        raise RuntimeError("Flux 任务超时")
