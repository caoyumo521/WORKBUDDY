"""视觉质检：检查 AI 直接画进画面的中文是否正确。

并集方案里，A 层（AI 画标题）负责版式融合度，但中文可能出错别字；
B 层（PIL 叠字）负责精确信息层。本模块就是两者之间的质检关卡：

1. 把生成图 + 预期文案交给视觉 LLM；
2. LLM 判断画面中 role="ai" 的槽位文字是否与预期一致；
3. 若不一致，返回需要被 PIL 覆盖修正的槽位名列表。

默认只质检 title（主标题），因为那是唯一交给 AI 画的中文。
"""
from __future__ import annotations

import base64
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx
from PIL import Image

from app.config import settings
from app.utils.text_layout import get_slots, title_text_of

logger = logging.getLogger(__name__)

QC_SYSTEM = """你是一名严格的电商详情页文字质检员。请逐字检查图片中由 AI 直接渲染的中文文字是否与用户提供的预期文案完全一致。

检查重点：
1. 是否有错字、漏字、多字、形近字（如「清」写成「青」、「透」写成「诱」）。
2. 是否有笔画扭曲、断裂、镜像、乱码、外星符号。
3. 是否把预期文字写到了错误位置，或完全没出现。

输出严格的 JSON，不要解释。"""

QC_USER_TEMPLATE = """请检查这张详情页图片中的中文标题文字。

【预期标题】
{expected_title}

【标题在画面中的大致位置】
{location}

请输出 JSON：
{{
  "correct": true/false,
  "seen_text": "你在图中实际看到的文字（逐字写出，看不清写空字符串）",
  "issues": ["问题1", "问题2"],
  "fix_slots": ["title"]
}}

要求：
- correct 为 true 当且仅当图中文字与预期标题逐字完全一致。
- 任何微小差异（包括异体字、错别字、缺字、多字、乱码）都必须让 correct 为 false。
- fix_slots 固定填 ["title"]（发现错误时由程序用 PIL 覆盖修正）。"""


def _image_to_b64(path: str | Path, max_pixels: int = 1024 * 1024) -> str:
    """把图片转成 data URI，过大时先缩小以节省 tokens/带宽。"""
    path = Path(path)
    img = Image.open(path)
    img.load()
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")

    # 等比缩放，长边不超过 1024
    w, h = img.size
    scale = min(1024 / max(w, h, 1), 1.0)
    if scale < 1.0:
        new_size = (int(w * scale), int(h * scale))
        img = img.resize(new_size, Image.LANCZOS)

    # JPEG 编码
    import io

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=88)
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    return f"data:image/jpeg;base64,{b64}"


def _describe_location(module_key: str) -> str:
    """描述 title 在画面中的大致位置，帮助视觉模型定位。"""
    slots = get_slots(module_key, role="ai")
    if not slots:
        return "画面顶部居中区域"
    # 通常只有一个 ai 槽位（title），取它的 box
    s = slots[0]
    x, y, w, h = s["box"]
    # 简化成人话
    h_pct = int(round((y + h / 2) * 100))
    return f"画面垂直方向约 {h_pct}% 处，横向居中"


def _try_parse_json(text: str) -> Optional[Dict[str, Any]]:
    text = text.strip()
    if text.startswith("```"):
        import re

        text = re.sub(r"^```[a-zA-Z]*\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    try:
        return json.loads(text)
    except Exception:
        import re

        m = re.search(r"\{[\s\S]*\}", text)
        if m:
            try:
                return json.loads(m.group(0))
            except Exception:
                return None
    return None


async def inspect_ai_text(
    image_path: str | Path,
    module_key: str,
    copy: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """检查生成图中 AI 画的中文标题是否正确。

    返回：
    {
      "correct": bool,
      "seen_text": str,
      "issues": List[str],
      "fix_slots": List[str],
      "skipped": bool,      # 因配置或缺文案未质检
      "reason": str,        # skipped / error 时的说明
    }
    """
    if not settings.text_qc_enabled:
        return {"correct": True, "seen_text": "", "issues": [], "fix_slots": [], "skipped": True, "reason": "质检已关闭"}

    if not settings.ai_render_headline:
        return {"correct": True, "seen_text": "", "issues": [], "fix_slots": [], "skipped": True, "reason": "AI 不画标题，无需质检"}

    expected = title_text_of(module_key, copy)
    if not expected:
        return {"correct": True, "seen_text": "", "issues": [], "fix_slots": [], "skipped": True, "reason": "无预期标题"}

    if not settings.has_text_llm:
        return {"correct": True, "seen_text": "", "issues": [], "fix_slots": [], "skipped": True, "reason": "无可用视觉 LLM"}

    try:
        image_b64 = _image_to_b64(image_path)
    except Exception as e:
        logger.warning("视觉质检图片编码失败: %s", e)
        return {"correct": True, "seen_text": "", "issues": [], "fix_slots": [], "skipped": True, "reason": f"图片编码失败: {e}"}

    user_prompt = QC_USER_TEMPLATE.format(
        expected_title=expected,
        location=_describe_location(module_key),
    )

    try:
        async with httpx.AsyncClient(timeout=90) as client:
            r = await client.post(
                f"{settings.text_base_url.rstrip('/')}/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.text_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": settings.text_model,
                    "messages": [
                        {"role": "system", "content": QC_SYSTEM},
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": user_prompt},
                                {"type": "image_url", "image_url": {"url": image_b64}},
                            ],
                        },
                    ],
                    "temperature": 0.2,
                    "response_format": {"type": "json_object"},
                },
            )
            r.raise_for_status()
            data = r.json()
            raw = data["choices"][0]["message"]["content"]
    except Exception as e:
        logger.warning("视觉质检 LLM 调用失败: %s", e)
        return {"correct": True, "seen_text": "", "issues": [], "fix_slots": [], "skipped": True, "reason": f"LLM 调用失败: {e}"}

    parsed = _try_parse_json(raw)
    if not parsed:
        return {"correct": True, "seen_text": "", "issues": [], "fix_slots": [], "skipped": True, "reason": "LLM 返回无法解析"}

    correct = bool(parsed.get("correct", False))
    fix_slots = [str(s) for s in parsed.get("fix_slots", []) if s]
    # 如果模型说错误但没给 fix_slots，默认修 title
    if not correct and not fix_slots:
        fix_slots = ["title"]

    return {
        "correct": correct,
        "seen_text": str(parsed.get("seen_text") or ""),
        "issues": [str(i) for i in parsed.get("issues", []) if i],
        "fix_slots": fix_slots,
        "skipped": False,
        "reason": "",
    }


def should_fix(result: Dict[str, Any]) -> List[str]:
    """从质检结果提取需要 PIL 覆盖修正的槽位名列表。"""
    if result.get("correct") or result.get("skipped"):
        return []
    return list(result.get("fix_slots", []))
