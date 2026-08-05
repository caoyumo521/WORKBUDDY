"""文字版式契约：A 层（生图 prompt）与 B 层（PIL 叠字）共享的唯一坐标来源。

设计核心
--------
详情页上的文字分两类，分别由两套机制负责，但共用同一份坐标定义：

1. role="ai"      —— 交给生图模型直接画进画面（通常是主标题）。
                     好处是文字带光影/材质/透视，真正融进版式，像设计稿。
                     风险是中文可能出错 → 由视觉质检兜底，错了就用 B 层覆盖修正。

2. role="overlay" —— 由 PIL 精确叠加（副标题、卖点条、参数、角标）。
                     这些信息字数多、必须 100% 准确，绝不能让模型画。

因为两者共用本文件的 box 坐标：
- 生成 prompt 时，overlay 槽位会被翻译成"这块区域必须保持干净留白"的英文约束；
- 叠字时，PIL 直接按同一 box 落字。
这样才不会出现"字叠在产品脸上"或"AI 把留白区画满了"。

坐标系
------
所有 box 均为相对比例 (x, y, w, h)，取值 0~1，相对整张图。
字号 size 亦为相对比例，基准是图片**宽度**（width * size）。
"""
from __future__ import annotations

from typing import Dict, List, Optional

# ---------------------------------------------------------------- 槽位定义
# name  : 槽位名，对应文案字典的 key
# box   : (x, y, w, h) 相对坐标
# role  : "ai" 交给生图模型画 / "overlay" 由 PIL 叠加
# align : 水平对齐 left | center | right
# valign: 垂直对齐 top | middle | bottom
# size  : 字号相对宽度比例
# weight: bold | regular
# max_chars: 文案字数上限（用于约束 LLM 输出，超出会被截断）
# style : 渲染样式 plain | plate（半透明底衬）| bar（色条）| pill（胶囊标签）
#         plate/bar/pill 用于保证在复杂背景上的可读性

_DEFAULT_LAYOUT: Dict = {
    "slots": [
        {"name": "title", "box": (0.08, 0.06, 0.84, 0.10), "role": "ai",
         "align": "center", "valign": "top", "size": 0.068, "weight": "bold",
         "max_chars": 10, "style": "plain"},
        {"name": "subtitle", "box": (0.10, 0.175, 0.80, 0.055), "role": "overlay",
         "align": "center", "valign": "top", "size": 0.030, "weight": "regular",
         "max_chars": 20, "style": "plain"},
        {"name": "bullets", "box": (0.08, 0.755, 0.84, 0.185), "role": "overlay",
         "align": "left", "valign": "top", "size": 0.030, "weight": "regular",
         "max_chars": 16, "max_items": 3, "style": "plate"},
    ],
}


MODULE_TEXT_LAYOUT: Dict[str, Dict] = {
    # 首屏：大标题居上，卖点一句话收在下方，中部完全让给产品
    "hero": {
        "slots": [
            {"name": "title", "box": (0.08, 0.055, 0.84, 0.115), "role": "ai",
             "align": "center", "valign": "top", "size": 0.078, "weight": "bold",
             "max_chars": 10, "style": "plain"},
            {"name": "subtitle", "box": (0.12, 0.185, 0.76, 0.055), "role": "overlay",
             "align": "center", "valign": "top", "size": 0.032, "weight": "regular",
             "max_chars": 20, "style": "plain"},
            {"name": "badge", "box": (0.30, 0.885, 0.40, 0.058), "role": "overlay",
             "align": "center", "valign": "middle", "size": 0.028, "weight": "bold",
             "max_chars": 12, "style": "pill"},
        ],
    },

    # 核心卖点：标题在上，3 条卖点排在下方 1/4
    "core_selling": {
        "slots": [
            {"name": "title", "box": (0.07, 0.055, 0.86, 0.10), "role": "ai",
             "align": "center", "valign": "top", "size": 0.070, "weight": "bold",
             "max_chars": 10, "style": "plain"},
            {"name": "bullets", "box": (0.07, 0.715, 0.86, 0.225), "role": "overlay",
             "align": "left", "valign": "top", "size": 0.032, "weight": "regular",
             "max_chars": 18, "max_items": 3, "style": "plate"},
        ],
    },

    # 使用场景：标题压在顶部，场景描述贴底
    "scenario": {
        "slots": [
            {"name": "title", "box": (0.07, 0.06, 0.86, 0.095), "role": "ai",
             "align": "center", "valign": "top", "size": 0.066, "weight": "bold",
             "max_chars": 10, "style": "plain"},
            {"name": "subtitle", "box": (0.10, 0.845, 0.80, 0.095), "role": "overlay",
             "align": "center", "valign": "middle", "size": 0.031, "weight": "regular",
             "max_chars": 24, "style": "plate"},
        ],
    },

    # 细节图：以质感为主，只在底部压一条说明
    "detail": {
        "slots": [
            {"name": "title", "box": (0.07, 0.055, 0.86, 0.09), "role": "ai",
             "align": "center", "valign": "top", "size": 0.062, "weight": "bold",
             "max_chars": 8, "style": "plain"},
            {"name": "subtitle", "box": (0.08, 0.855, 0.84, 0.085), "role": "overlay",
             "align": "center", "valign": "middle", "size": 0.030, "weight": "regular",
             "max_chars": 22, "style": "plate"},
        ],
    },

    # SKU：顶部标题 + 底部规格说明
    "sku": {
        "slots": [
            {"name": "title", "box": (0.07, 0.055, 0.86, 0.09), "role": "ai",
             "align": "center", "valign": "top", "size": 0.064, "weight": "bold",
             "max_chars": 8, "style": "plain"},
            {"name": "bullets", "box": (0.08, 0.795, 0.84, 0.145), "role": "overlay",
             "align": "left", "valign": "top", "size": 0.030, "weight": "regular",
             "max_chars": 16, "max_items": 2, "style": "plate"},
        ],
    },

    # 尺寸图：大量数字标注，留给 overlay 的空间要足
    "size_chart": {
        "slots": [
            {"name": "title", "box": (0.07, 0.05, 0.86, 0.085), "role": "ai",
             "align": "center", "valign": "top", "size": 0.060, "weight": "bold",
             "max_chars": 8, "style": "plain"},
            {"name": "bullets", "box": (0.07, 0.735, 0.86, 0.205), "role": "overlay",
             "align": "left", "valign": "top", "size": 0.031, "weight": "regular",
             "max_chars": 18, "max_items": 4, "style": "plate"},
        ],
    },

    # 规格参数：信息密度最高，底部留 30%
    "spec_param": {
        "slots": [
            {"name": "title", "box": (0.07, 0.05, 0.86, 0.085), "role": "ai",
             "align": "center", "valign": "top", "size": 0.060, "weight": "bold",
             "max_chars": 8, "style": "plain"},
            {"name": "bullets", "box": (0.07, 0.665, 0.86, 0.275), "role": "overlay",
             "align": "left", "valign": "top", "size": 0.031, "weight": "regular",
             "max_chars": 20, "max_items": 5, "style": "plate"},
        ],
    },

    # 售后保障：承诺条目要清楚
    "after_sales": {
        "slots": [
            {"name": "title", "box": (0.07, 0.06, 0.86, 0.095), "role": "ai",
             "align": "center", "valign": "top", "size": 0.066, "weight": "bold",
             "max_chars": 8, "style": "plain"},
            {"name": "bullets", "box": (0.08, 0.695, 0.84, 0.245), "role": "overlay",
             "align": "left", "valign": "top", "size": 0.032, "weight": "regular",
             "max_chars": 18, "max_items": 4, "style": "plate"},
        ],
    },

    # 品牌故事：偏叙事，用一段副文案
    "brand_story": {
        "slots": [
            {"name": "title", "box": (0.08, 0.06, 0.84, 0.10), "role": "ai",
             "align": "center", "valign": "top", "size": 0.068, "weight": "bold",
             "max_chars": 10, "style": "plain"},
            {"name": "subtitle", "box": (0.10, 0.815, 0.80, 0.125), "role": "overlay",
             "align": "center", "valign": "middle", "size": 0.030, "weight": "regular",
             "max_chars": 40, "style": "plate"},
        ],
    },

    # 注意事项
    "notice": {
        "slots": [
            {"name": "title", "box": (0.07, 0.055, 0.86, 0.09), "role": "ai",
             "align": "center", "valign": "top", "size": 0.062, "weight": "bold",
             "max_chars": 8, "style": "plain"},
            {"name": "bullets", "box": (0.08, 0.705, 0.84, 0.235), "role": "overlay",
             "align": "left", "valign": "top", "size": 0.031, "weight": "regular",
             "max_chars": 18, "max_items": 4, "style": "plate"},
        ],
    },

    # 资质认证
    "qualification": {
        "slots": [
            {"name": "title", "box": (0.07, 0.055, 0.86, 0.09), "role": "ai",
             "align": "center", "valign": "top", "size": 0.064, "weight": "bold",
             "max_chars": 8, "style": "plain"},
            {"name": "bullets", "box": (0.08, 0.775, 0.84, 0.165), "role": "overlay",
             "align": "left", "valign": "top", "size": 0.030, "weight": "regular",
             "max_chars": 16, "max_items": 3, "style": "plate"},
        ],
    },

    # 常见问题：Q&A 成对，用 bullets 承载
    "faq": {
        "slots": [
            {"name": "title", "box": (0.07, 0.055, 0.86, 0.09), "role": "ai",
             "align": "center", "valign": "top", "size": 0.062, "weight": "bold",
             "max_chars": 8, "style": "plain"},
            {"name": "bullets", "box": (0.07, 0.675, 0.86, 0.265), "role": "overlay",
             "align": "left", "valign": "top", "size": 0.030, "weight": "regular",
             "max_chars": 24, "max_items": 4, "style": "plate"},
        ],
    },

    # 工厂实力
    "factory": {
        "slots": [
            {"name": "title", "box": (0.07, 0.06, 0.86, 0.095), "role": "ai",
             "align": "center", "valign": "top", "size": 0.066, "weight": "bold",
             "max_chars": 8, "style": "plain"},
            {"name": "bullets", "box": (0.08, 0.775, 0.84, 0.165), "role": "overlay",
             "align": "left", "valign": "top", "size": 0.030, "weight": "regular",
             "max_chars": 16, "max_items": 3, "style": "plate"},
        ],
    },

    # 包装展示
    "package": {
        "slots": [
            {"name": "title", "box": (0.07, 0.055, 0.86, 0.09), "role": "ai",
             "align": "center", "valign": "top", "size": 0.062, "weight": "bold",
             "max_chars": 8, "style": "plain"},
            {"name": "subtitle", "box": (0.08, 0.855, 0.84, 0.085), "role": "overlay",
             "align": "center", "valign": "middle", "size": 0.030, "weight": "regular",
             "max_chars": 22, "style": "plate"},
        ],
    },

    # 物流
    "logistics": {
        "slots": [
            {"name": "title", "box": (0.07, 0.055, 0.86, 0.09), "role": "ai",
             "align": "center", "valign": "top", "size": 0.062, "weight": "bold",
             "max_chars": 8, "style": "plain"},
            {"name": "bullets", "box": (0.08, 0.755, 0.84, 0.185), "role": "overlay",
             "align": "left", "valign": "top", "size": 0.031, "weight": "regular",
             "max_chars": 16, "max_items": 3, "style": "plate"},
        ],
    },

    # 用户痛点：情绪钩子放大
    "pain_point": {
        "slots": [
            {"name": "title", "box": (0.08, 0.055, 0.84, 0.11), "role": "ai",
             "align": "center", "valign": "top", "size": 0.072, "weight": "bold",
             "max_chars": 12, "style": "plain"},
            {"name": "bullets", "box": (0.08, 0.745, 0.84, 0.195), "role": "overlay",
             "align": "left", "valign": "top", "size": 0.031, "weight": "regular",
             "max_chars": 18, "max_items": 3, "style": "plate"},
        ],
    },

    # 生活方式
    "lifestyle": {
        "slots": [
            {"name": "title", "box": (0.08, 0.06, 0.84, 0.10), "role": "ai",
             "align": "center", "valign": "top", "size": 0.068, "weight": "bold",
             "max_chars": 10, "style": "plain"},
            {"name": "subtitle", "box": (0.10, 0.855, 0.80, 0.085), "role": "overlay",
             "align": "center", "valign": "middle", "size": 0.031, "weight": "regular",
             "max_chars": 24, "style": "plate"},
        ],
    },

    # 对比模块
    "comparison": {
        "slots": [
            {"name": "title", "box": (0.07, 0.05, 0.86, 0.09), "role": "ai",
             "align": "center", "valign": "top", "size": 0.062, "weight": "bold",
             "max_chars": 8, "style": "plain"},
            {"name": "bullets", "box": (0.07, 0.705, 0.86, 0.235), "role": "overlay",
             "align": "left", "valign": "top", "size": 0.031, "weight": "regular",
             "max_chars": 20, "max_items": 4, "style": "plate"},
        ],
    },

    # 购买引导：CTA 要有强按钮感
    "cta": {
        "slots": [
            {"name": "title", "box": (0.08, 0.06, 0.84, 0.115), "role": "ai",
             "align": "center", "valign": "top", "size": 0.076, "weight": "bold",
             "max_chars": 10, "style": "plain"},
            {"name": "subtitle", "box": (0.12, 0.195, 0.76, 0.055), "role": "overlay",
             "align": "center", "valign": "top", "size": 0.031, "weight": "regular",
             "max_chars": 20, "style": "plain"},
            {"name": "badge", "box": (0.24, 0.845, 0.52, 0.075), "role": "overlay",
             "align": "center", "valign": "middle", "size": 0.038, "weight": "bold",
             "max_chars": 10, "style": "pill"},
        ],
    },

    # ---- 行业预设里出现、但不在 COMMON_MODULES 的补充模块 ----
    "material": {
        "slots": [
            {"name": "title", "box": (0.07, 0.055, 0.86, 0.09), "role": "ai",
             "align": "center", "valign": "top", "size": 0.062, "weight": "bold",
             "max_chars": 8, "style": "plain"},
            {"name": "bullets", "box": (0.08, 0.765, 0.84, 0.175), "role": "overlay",
             "align": "left", "valign": "top", "size": 0.031, "weight": "regular",
             "max_chars": 16, "max_items": 3, "style": "plate"},
        ],
    },
    "craft": {
        "slots": [
            {"name": "title", "box": (0.07, 0.055, 0.86, 0.09), "role": "ai",
             "align": "center", "valign": "top", "size": 0.062, "weight": "bold",
             "max_chars": 8, "style": "plain"},
            {"name": "subtitle", "box": (0.08, 0.855, 0.84, 0.085), "role": "overlay",
             "align": "center", "valign": "middle", "size": 0.030, "weight": "regular",
             "max_chars": 22, "style": "plate"},
        ],
    },
    "feature": {
        "slots": [
            {"name": "title", "box": (0.07, 0.055, 0.86, 0.095), "role": "ai",
             "align": "center", "valign": "top", "size": 0.066, "weight": "bold",
             "max_chars": 10, "style": "plain"},
            {"name": "bullets", "box": (0.07, 0.715, 0.86, 0.225), "role": "overlay",
             "align": "left", "valign": "top", "size": 0.032, "weight": "regular",
             "max_chars": 18, "max_items": 3, "style": "plate"},
        ],
    },
    "tech": {
        "slots": [
            {"name": "title", "box": (0.07, 0.055, 0.86, 0.095), "role": "ai",
             "align": "center", "valign": "top", "size": 0.066, "weight": "bold",
             "max_chars": 10, "style": "plain"},
            {"name": "bullets", "box": (0.07, 0.725, 0.86, 0.215), "role": "overlay",
             "align": "left", "valign": "top", "size": 0.031, "weight": "regular",
             "max_chars": 18, "max_items": 3, "style": "plate"},
        ],
    },
    "ingredient": {
        "slots": [
            {"name": "title", "box": (0.07, 0.055, 0.86, 0.09), "role": "ai",
             "align": "center", "valign": "top", "size": 0.062, "weight": "bold",
             "max_chars": 8, "style": "plain"},
            {"name": "bullets", "box": (0.08, 0.755, 0.84, 0.185), "role": "overlay",
             "align": "left", "valign": "top", "size": 0.031, "weight": "regular",
             "max_chars": 16, "max_items": 3, "style": "plate"},
        ],
    },
    "review": {
        "slots": [
            {"name": "title", "box": (0.07, 0.055, 0.86, 0.09), "role": "ai",
             "align": "center", "valign": "top", "size": 0.062, "weight": "bold",
             "max_chars": 8, "style": "plain"},
            {"name": "bullets", "box": (0.07, 0.695, 0.86, 0.245), "role": "overlay",
             "align": "left", "valign": "top", "size": 0.030, "weight": "regular",
             "max_chars": 24, "max_items": 3, "style": "plate"},
        ],
    },
}


# 槽位名 → 中文语义（供 LLM 写文案时理解）
SLOT_SEMANTIC: Dict[str, str] = {
    "title": "主标题，最抢眼的一句话，必须短促有力",
    "subtitle": "副标题/一句话说明，补充主标题",
    "bullets": "要点条目，每条一个卖点或参数，简洁具体",
    "badge": "角标/按钮文字，如『立即抢购』『限时特惠』",
}


def get_layout(module_key: str) -> Dict:
    """取模块的文字版式；未定义的模块回退到通用版式。"""
    return MODULE_TEXT_LAYOUT.get(module_key) or _DEFAULT_LAYOUT


def get_slots(module_key: str, role: Optional[str] = None) -> List[Dict]:
    """取模块槽位列表，可按 role 过滤（ai / overlay）。"""
    slots = get_layout(module_key).get("slots", [])
    if role:
        return [s for s in slots if s.get("role") == role]
    return list(slots)


def get_slot(module_key: str, slot_name: str) -> Optional[Dict]:
    for s in get_slots(module_key):
        if s.get("name") == slot_name:
            return s
    return None


def copy_spec(module_key: str) -> Dict[str, Dict]:
    """输出该模块需要哪些文案字段及其约束，供 LLM 写文案时使用。

    返回 {slot_name: {max_chars, max_items, semantic}}
    """
    spec: Dict[str, Dict] = {}
    for s in get_slots(module_key):
        spec[s["name"]] = {
            "max_chars": s.get("max_chars", 16),
            "max_items": s.get("max_items", 1),
            "semantic": SLOT_SEMANTIC.get(s["name"], ""),
        }
    return spec


# ---------------------------------------------------------------- 区域描述
def _describe_box(box) -> str:
    """把相对 box 翻译成人话（英文），用于写进生图 prompt。

    例：(0.08, 0.755, 0.84, 0.185) → "the bottom 25% band of the frame"
    """
    x, y, w, h = box
    bottom = y + h

    # 纵向定位优先，横向次之
    if bottom >= 0.93 and y >= 0.60:
        pct = int(round((1.0 - y) * 100))
        return f"the bottom {pct}% horizontal band"
    if y <= 0.10 and bottom <= 0.42:
        pct = int(round(bottom * 100))
        return f"the top {pct}% horizontal band"
    if w <= 0.55 and x <= 0.10:
        pct = int(round((x + w) * 100))
        return f"the left {pct}% vertical column"
    if w <= 0.55 and (x + w) >= 0.90:
        pct = int(round((1.0 - x) * 100))
        return f"the right {pct}% vertical column"

    y_pct = int(round(y * 100))
    h_pct = int(round(h * 100))
    return f"a horizontal band starting at {y_pct}% height and spanning {h_pct}% of the frame"


def _merge_vertical_bands(boxes: List[tuple]) -> List[tuple]:
    """把纵向相邻/重叠的 box 合并，避免 prompt 里出现一堆碎片化区域描述。"""
    if not boxes:
        return []
    ordered = sorted(boxes, key=lambda b: b[1])
    merged = [list(ordered[0])]
    for b in ordered[1:]:
        last = merged[-1]
        last_bottom = last[1] + last[3]
        # 间隔小于 6% 视为同一条带
        if b[1] <= last_bottom + 0.06:
            # 注意：必须先用旧的 x/w 算出右边界，再更新 x，否则宽度会算错
            last_right = last[0] + last[2]
            new_left = min(last[0], b[0])
            new_right = max(last_right, b[0] + b[2])
            new_bottom = max(last_bottom, b[1] + b[3])
            last[0] = new_left
            last[2] = new_right - new_left
            last[3] = new_bottom - last[1]
        else:
            merged.append(list(b))
    return [tuple(m) for m in merged]


def describe_clean_zones(module_key: str) -> str:
    """生成"这些区域必须留干净"的英文约束，写进生图 prompt。

    对应所有 role=overlay 的槽位——因为那些位置稍后会被 PIL 叠上真实文字，
    如果 AI 在那里堆了产品或复杂纹理，叠出来的字就没法看。
    """
    boxes = [s["box"] for s in get_slots(module_key, role="overlay")]
    if not boxes:
        return ""
    zones = _merge_vertical_bands(boxes)
    descs = [_describe_box(b) for b in zones]
    # 去重且保序
    seen = set()
    uniq = []
    for d in descs:
        if d not in seen:
            seen.add(d)
            uniq.append(d)
    if len(uniq) == 1:
        zone_text = uniq[0]
    else:
        zone_text = ", ".join(uniq[:-1]) + ", and " + uniq[-1]
    return (
        f"TEXT-SAFE AREA: Keep {zone_text} visually calm and uncluttered — "
        "a smooth gradient, soft shadow, blurred background or plain surface is ideal there. "
        "Do NOT place the product, faces, high-contrast patterns or busy detail in those areas, "
        "and do NOT draw any text there. "
        "Real copy will be composited into these zones afterwards, so they must stay clean."
    )


def describe_ai_text(module_key: str, copy: Optional[Dict] = None) -> str:
    """生成"让 AI 把这句中文画在这里"的英文指令。

    copy 为该模块的文案字典，例如 {"title": "24小时持久锁水", ...}。
    未提供文案时返回空串（退化成纯留白模式）。
    """
    ai_slots = get_slots(module_key, role="ai")
    if not ai_slots or not copy:
        return ""

    lines: List[str] = []
    for s in ai_slots:
        text = copy.get(s["name"])
        if not text or not isinstance(text, str):
            continue
        text = text.strip()
        if not text:
            continue
        where = _describe_box(s["box"])
        weight = "heavy bold" if s.get("weight") == "bold" else "regular"
        lines.append(
            f'Render the Chinese headline "{text}" in {where}, '
            f"set in a clean modern {weight} Chinese sans-serif typeface (similar to Source Han Sans / PingFang), "
            "horizontally centered, well-kerned, perfectly legible, integrated into the scene lighting."
        )

    if not lines:
        return ""

    return (
        "[HEADLINE TYPOGRAPHY — render this text as part of the image]\n"
        + "\n".join(lines)
        + "\nTypography rules: reproduce the Chinese characters EXACTLY as given, "
        "stroke by stroke, with correct glyph shapes — no invented, distorted, mirrored or garbled characters. "
        "Do not add any other words, slogans, watermarks, logos or captions beyond the headline above."
    )


def title_text_of(module_key: str, copy: Optional[Dict]) -> Optional[str]:
    """取该模块交给 AI 渲染的标题原文（用于生成后视觉质检比对）。"""
    if not copy:
        return None
    for s in get_slots(module_key, role="ai"):
        t = copy.get(s["name"])
        if isinstance(t, str) and t.strip():
            return t.strip()
    return None
