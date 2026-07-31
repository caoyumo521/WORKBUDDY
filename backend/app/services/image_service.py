"""Image Generation Service - 统一生图接口。

设计原则：
1. 不在调用方代码中写死 provider
2. 通过 .env 切换 IMAGE_PROVIDER
3. 不同 provider 暴露同一组方法

所有实现必须返回 dict 格式：
{
    "url": "...",         # 可选，若返回 base64 则无 url
    "b64": "...",         # 可选
    "width": 1024,
    "height": 1024,
    "model": "...",
    "raw": {...}          # 原始响应，调试用
}
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class ImageGenerationProvider(ABC):
    name: str = "base"

    @abstractmethod
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
        ...


def resolution_to_size(resolution: str, aspect_ratio: str = "1:1") -> tuple[int, int]:
    """将 1K/2K/4K + 比例 换算成像素尺寸。"""
    short_map = {"1K": 1024, "2K": 2048, "4K": 4096}
    base = short_map.get(resolution, 1024)

    try:
        w_ratio, h_ratio = aspect_ratio.split(":")
        w_ratio, h_ratio = float(w_ratio), float(h_ratio)
    except Exception:
        w_ratio, h_ratio = 1, 1

    if w_ratio >= h_ratio:
        width = base
        height = int(base * h_ratio / w_ratio)
    else:
        height = base
        width = int(base * w_ratio / h_ratio)
    return width, height


def get_image_provider() -> ImageGenerationProvider:
    """工厂方法：根据 .env 决定用哪个 provider。"""
    from app.config import settings
    from app.services.image_providers.custom_provider import CustomProvider
    from app.services.image_providers.openai_provider import OpenAIProvider
    from app.services.image_providers.flux_provider import FluxProvider
    from app.services.image_providers.mock_provider import MockProvider

    provider = settings.image_provider.lower()
    if provider == "openai":
        return OpenAIProvider(settings.image_base_url, settings.image_api_key, settings.image_model)
    if provider == "flux":
        return FluxProvider(settings.image_base_url, settings.image_api_key, settings.image_model)
    if provider == "mock":
        return MockProvider()
    return CustomProvider(settings.image_base_url, settings.image_api_key, settings.image_model)
