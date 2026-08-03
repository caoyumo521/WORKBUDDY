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
import json
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


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
    """工厂方法：根据 .env 决定用哪个 provider。

    优先使用多中转配置 IMAGE_RELAYS（依次尝试，哪个可用用哪个）；
    未配置时回退到单 Key（IMAGE_PROVIDER=openai + IMAGE_API_KEY）。
    """
    from app.config import settings
    from app.services.image_providers.custom_provider import CustomProvider
    from app.services.image_providers.openai_provider import OpenAIProvider, MultiRelayProvider
    from app.services.image_providers.flux_provider import FluxProvider
    from app.services.image_providers.mock_provider import MockProvider

    # 1) 多中转（容灾）
    relays: List[OpenAIProvider] = []
    raw = (settings.image_relays or "").strip()
    if raw:
        try:
            arr = json.loads(raw)
            for item in arr:
                bu = item.get("base_url") or settings.image_base_url
                ak = item.get("api_key") or ""
                mdl = item.get("model") or settings.image_model
                if ak:
                    relays.append(OpenAIProvider(bu, ak, mdl))
        except Exception as e:
            logger.warning("解析 IMAGE_RELAYS 失败，回退单 Key: %s", e)

    # 2) 单 Key 兜底（未配置 IMAGE_RELAYS 时）
    if not relays and settings.image_provider.lower() == "openai" and settings.image_api_key:
        relays.append(OpenAIProvider(settings.image_base_url, settings.image_api_key, settings.image_model))

    if relays:
        if len(relays) == 1:
            return relays[0]
        logger.info("生图多中转已启用，共 %d 个中转", len(relays))
        return MultiRelayProvider(relays)

    # 3) 其他 provider（flux / custom / mock）
    provider = settings.image_provider.lower()
    if provider == "flux":
        return FluxProvider(settings.image_base_url, settings.image_api_key, settings.image_model)
    if provider == "mock":
        return MockProvider()
    return CustomProvider(settings.image_base_url, settings.image_api_key, settings.image_model)
