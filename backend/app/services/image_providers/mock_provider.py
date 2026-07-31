"""Mock provider - 没有任何真实 API 时使用，返回一张渐变占位图。"""
import base64
import io
from typing import Any, Dict, List, Optional

from PIL import Image, ImageDraw, ImageFont

from app.services.image_service import ImageGenerationProvider


class MockProvider(ImageGenerationProvider):
    """用于本地无 API 时跑通整条链路。"""

    name = "mock"

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
        # 限制最大尺寸，避免占内存
        w, h = min(width, 1024), min(height, 1024)
        img = Image.new("RGB", (w, h), (245, 247, 250))
        d = ImageDraw.Draw(img)
        # 渐变
        for y in range(h):
            r = int(180 + (y / h) * 60)
            g = int(200 + (y / h) * 30)
            b = int(230 - (y / h) * 30)
            d.line([(0, y), (w, y)], fill=(r, g, b))
        # 文字
        try:
            font = ImageFont.truetype("arial.ttf", 36)
        except Exception:
            font = ImageFont.load_default()
        text = (prompt[:40] + "...") if len(prompt) > 40 else prompt
        d.rectangle([(20, 20), (w - 20, h - 20)], outline=(60, 90, 180), width=4)
        d.text((40, h // 2 - 30), "Mock Image", fill=(60, 90, 180), font=font)
        d.text((40, h // 2 + 20), text, fill=(60, 90, 180), font=font)

        buf = io.BytesIO()
        img.save(buf, format="PNG")
        b64 = base64.b64encode(buf.getvalue()).decode("ascii")
        return {
            "url": "",
            "b64": b64,
            "width": w,
            "height": h,
            "model": "mock",
            "raw": {"mock": True, "prompt": prompt},
        }
