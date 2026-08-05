"""PIL 叠字引擎（B 层）。

职责
----
按 `app.utils.text_layout` 的坐标契约，把中文文案精确合成到生成图上。
这是"并集方案"里保证 **文字 100% 准确** 的一半。

三个关键设计
------------
1. 自动对比度：先采样目标区域的背景亮度，再决定用深色还是浅色文字、
   配什么底衬。这样无论 AI 生成的是白墙还是黑丝绒，字都清晰可读。

2. 自适应排版：字号会根据 box 尺寸自动收缩，中文按字断行、英文按词断行，
   保证文字永远落在预留的安全区内，不会溢出压到产品。

3. 磨砂覆盖修正：当视觉质检发现 AI 把中文标题画错时，对该区域做
   高斯模糊 + 半透明色罩（磨砂玻璃效果）盖掉错字，再叠上正确文字。
   比直接糊一块纯色矩形自然得多。
"""
from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from app.utils.prompts import get_style_profile
from app.utils.text_layout import get_slots

logger = logging.getLogger(__name__)

RGB = Tuple[int, int, int]
RGBA = Tuple[int, int, int, int]

# ---------------------------------------------------------------- 字体
# 按优先级探测；Windows 优先微软雅黑，其次等线；macOS/Linux 给出常见回退
_FONT_CANDIDATES: Dict[str, List[str]] = {
    "bold": [
        "C:/Windows/Fonts/msyhbd.ttc",
        "C:/Windows/Fonts/Dengb.ttf",
        "C:/Windows/Fonts/simhei.ttf",
        "/System/Library/Fonts/PingFang.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
        "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
    ],
    "regular": [
        "C:/Windows/Fonts/msyh.ttc",
        "C:/Windows/Fonts/Deng.ttf",
        "C:/Windows/Fonts/simsun.ttc",
        "/System/Library/Fonts/PingFang.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
    ],
}

_font_path_cache: Dict[str, Optional[str]] = {}
_font_obj_cache: Dict[Tuple[str, int], ImageFont.FreeTypeFont] = {}


def _resolve_font_path(weight: str) -> Optional[str]:
    """找到可用的中文字体文件路径。支持 .env 覆盖。"""
    if weight in _font_path_cache:
        return _font_path_cache[weight]

    # .env 覆盖优先
    override = None
    try:
        from app.config import settings
        override = (
            settings.text_overlay_font_bold if weight == "bold" else settings.text_overlay_font_regular
        )
    except Exception:
        override = None

    candidates = ([override] if override else []) + _FONT_CANDIDATES.get(weight, [])
    found: Optional[str] = None
    for c in candidates:
        if c and Path(c).exists():
            found = c
            break
    if not found:
        logger.warning("未找到 %s 中文字体，将回退到 PIL 默认字体（中文可能显示为方块）", weight)
    _font_path_cache[weight] = found
    return found


def _get_font(weight: str, size: int) -> ImageFont.FreeTypeFont:
    size = max(8, int(size))
    key = (weight, size)
    cached = _font_obj_cache.get(key)
    if cached is not None:
        return cached
    path = _resolve_font_path(weight)
    try:
        font = ImageFont.truetype(path, size) if path else ImageFont.load_default()
    except Exception as e:
        logger.warning("字体加载失败 %s: %s", path, e)
        font = ImageFont.load_default()
    _font_obj_cache[key] = font
    return font


def has_cjk_font() -> bool:
    """是否具备中文渲染能力（供上层决定要不要走叠字）。"""
    return _resolve_font_path("regular") is not None


# ---------------------------------------------------------------- 颜色
def _hex_to_rgb(h: str) -> RGB:
    h = h.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def _luminance(c: Sequence[int]) -> float:
    """感知亮度 0~255。"""
    return 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]


def _palette(visual_style: str) -> List[RGB]:
    profile = get_style_profile(visual_style or "")
    hexes = re.findall(r"#[0-9A-Fa-f]{6}", profile.get("palette", ""))
    return [_hex_to_rgb(h) for h in hexes]


def _accent_color(visual_style: str) -> RGB:
    """挑一个最适合做强调（按钮/标记）的颜色：饱和度高且不过暗。"""
    colors = _palette(visual_style)
    if not colors:
        return (198, 122, 74)  # 温暖赭色兜底
    best = None
    best_score = -1.0
    for c in colors:
        mx, mn = max(c), min(c)
        sat = (mx - mn) / mx if mx else 0.0
        lum = _luminance(c)
        # 偏好：饱和度高、亮度适中
        score = sat * 2.0 - abs(lum - 140) / 255.0
        if score > best_score:
            best_score = score
            best = c
    return best or colors[0]


def _sample_bg(img: Image.Image, box_px: Tuple[int, int, int, int]) -> RGB:
    """采样区域平均色（缩略图加速）。"""
    x, y, w, h = box_px
    x = max(0, x); y = max(0, y)
    w = max(1, min(w, img.size[0] - x)); h = max(1, min(h, img.size[1] - y))
    region = img.crop((x, y, x + w, y + h)).convert("RGB")
    region = region.resize((16, 16), Image.BILINEAR)
    pixels = list(region.getdata())
    n = len(pixels)
    return (
        sum(p[0] for p in pixels) // n,
        sum(p[1] for p in pixels) // n,
        sum(p[2] for p in pixels) // n,
    )


def _bg_contrast_scheme(bg: RGB, visual_style: str) -> Dict:
    """根据背景亮度决定文字色 / 底衬色 / 描边色。"""
    lum = _luminance(bg)
    colors = _palette(visual_style)
    darkest = min(colors, key=_luminance) if colors else (32, 32, 32)
    lightest = max(colors, key=_luminance) if colors else (250, 248, 244)

    if lum >= 145:
        # 浅背景 → 深字
        text = darkest if _luminance(darkest) < 110 else (34, 32, 30)
        plate = (255, 255, 255, 165)
        halo = (255, 255, 255, 200)
    else:
        # 深背景 → 浅字
        text = lightest if _luminance(lightest) > 190 else (250, 249, 246)
        plate = (18, 18, 20, 150)
        halo = (0, 0, 0, 170)
    return {"text": text, "plate": plate, "halo": halo, "bg_lum": lum}


# ---------------------------------------------------------------- 排版
def _is_cjk(ch: str) -> bool:
    o = ord(ch)
    return (
        0x4E00 <= o <= 0x9FFF or 0x3400 <= o <= 0x4DBF
        or 0x3000 <= o <= 0x303F or 0xFF00 <= o <= 0xFFEF
    )


def _text_w(font: ImageFont.FreeTypeFont, s: str) -> int:
    if not s:
        return 0
    bbox = font.getbbox(s)
    return bbox[2] - bbox[0]


def _wrap(text: str, font: ImageFont.FreeTypeFont, max_w: int) -> List[str]:
    """中文按字断行、英文按词断行的混合换行。"""
    text = (text or "").strip()
    if not text:
        return []
    lines: List[str] = []
    cur = ""
    i = 0
    while i < len(text):
        ch = text[i]
        if ch == "\n":
            lines.append(cur)
            cur = ""
            i += 1
            continue
        # 英文/数字：整词处理，避免把单词劈开
        if not _is_cjk(ch) and not ch.isspace():
            j = i
            while j < len(text) and not _is_cjk(text[j]) and not text[j].isspace():
                j += 1
            token = text[i:j]
        else:
            token = ch
            j = i + 1

        trial = cur + token
        if _text_w(font, trial) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur.rstrip())
            cur = token.lstrip() if token.isspace() else token
        i = j
    if cur.strip():
        lines.append(cur.rstrip())
    return lines


def _fit_lines(
    text: str, weight: str, base_size: int, max_w: int, max_h: int, line_ratio: float = 1.32
) -> Tuple[ImageFont.FreeTypeFont, List[str], int]:
    """自动收缩字号，直到整段文字塞进 (max_w, max_h)。返回 (font, lines, line_height)。"""
    size = max(10, base_size)
    min_size = max(9, int(base_size * 0.5))
    while size >= min_size:
        font = _get_font(weight, size)
        lines = _wrap(text, font, max_w)
        lh = int(size * line_ratio)
        if lines and lh * len(lines) <= max_h:
            return font, lines, lh
        size -= max(1, int(size * 0.06))
    font = _get_font(weight, min_size)
    lines = _wrap(text, font, max_w)
    lh = int(min_size * line_ratio)
    # 实在放不下就截断行数，保证不溢出
    max_lines = max(1, max_h // lh)
    return font, lines[:max_lines], lh


# ---------------------------------------------------------------- 绘制原语
def _draw_text_with_halo(
    draw: ImageDraw.ImageDraw,
    xy: Tuple[int, int],
    text: str,
    font: ImageFont.FreeTypeFont,
    fill: RGB,
    halo: RGBA,
    halo_width: int = 2,
) -> None:
    """带柔光描边的文字，保证复杂背景上依然可读。"""
    x, y = xy
    if halo_width > 0:
        for dx in range(-halo_width, halo_width + 1):
            for dy in range(-halo_width, halo_width + 1):
                if dx == 0 and dy == 0:
                    continue
                draw.text((x + dx, y + dy), text, font=font, fill=halo)
    draw.text((x, y), text, font=font, fill=fill)


def _align_x(align: str, box_x: int, box_w: int, text_w: int) -> int:
    if align == "center":
        return box_x + (box_w - text_w) // 2
    if align == "right":
        return box_x + box_w - text_w
    return box_x


def _frost_area(img: Image.Image, box_px: Tuple[int, int, int, int], tint: RGBA) -> None:
    """磨砂玻璃覆盖：高斯模糊 + 半透明色罩。用于盖掉 AI 画错的文字。"""
    x, y, w, h = box_px
    x = max(0, x); y = max(0, y)
    w = max(1, min(w, img.size[0] - x)); h = max(1, min(h, img.size[1] - y))
    region = img.crop((x, y, x + w, y + h))
    blurred = region.filter(ImageFilter.GaussianBlur(radius=max(6, w // 28)))
    img.paste(blurred, (x, y))
    veil = Image.new("RGBA", (w, h), tint)
    img.alpha_composite(veil, (x, y))


# ---------------------------------------------------------------- 槽位渲染
def _render_plate(
    img: Image.Image, box_px: Tuple[int, int, int, int], color: RGBA, radius_ratio: float = 0.10
) -> None:
    x, y, w, h = box_px
    layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    r = max(4, int(min(w, h) * radius_ratio))
    d.rounded_rectangle([0, 0, w - 1, h - 1], radius=r, fill=color)
    img.alpha_composite(layer, (x, y))


def _render_single_text(
    img: Image.Image,
    slot: Dict,
    text: str,
    visual_style: str,
    frost: bool = False,
) -> None:
    """渲染 title / subtitle / badge 这类单段文字槽位。"""
    W, H = img.size
    bx, by, bw, bh = slot["box"]
    box_px = (int(bx * W), int(by * H), int(bw * W), int(bh * H))
    x, y, w, h = box_px

    style = slot.get("style", "plain")
    if frost:
        # 覆盖修正：先磨砂盖掉原有错字
        bg0 = _sample_bg(img, box_px)
        veil = (255, 255, 255, 150) if _luminance(bg0) >= 145 else (16, 16, 18, 150)
        _frost_area(img, box_px, veil)

    bg = _sample_bg(img, box_px)
    scheme = _bg_contrast_scheme(bg, visual_style)

    pad_x = int(w * 0.04)
    pad_y = int(h * 0.12)

    if style == "pill":
        accent = _accent_color(visual_style)
        _render_plate(img, box_px, (*accent, 235), radius_ratio=0.5)
        # 胶囊上的字用与强调色对比的颜色
        text_color: RGB = (255, 255, 255) if _luminance(accent) < 150 else (28, 26, 24)
        halo: RGBA = (0, 0, 0, 0)
        halo_w = 0
    elif style == "plate":
        _render_plate(img, box_px, scheme["plate"], radius_ratio=0.14)
        text_color = scheme["text"]
        halo = (0, 0, 0, 0)
        halo_w = 0
    else:  # plain
        text_color = scheme["text"]
        halo = scheme["halo"]
        halo_w = max(1, int(min(w, h) * 0.012))

    base_size = int(W * slot.get("size", 0.03))
    font, lines, lh = _fit_lines(
        text, slot.get("weight", "regular"), base_size, w - pad_x * 2, h - pad_y * 2
    )
    if not lines:
        return

    draw = ImageDraw.Draw(img)
    block_h = lh * len(lines)
    valign = slot.get("valign", "top")
    if valign == "middle":
        cy = y + (h - block_h) // 2
    elif valign == "bottom":
        cy = y + h - block_h - pad_y
    else:
        cy = y + pad_y

    for ln in lines:
        tw = _text_w(font, ln)
        tx = _align_x(slot.get("align", "left"), x + pad_x, w - pad_x * 2, tw)
        _draw_text_with_halo(draw, (tx, cy), ln, font, text_color, halo, halo_w)
        cy += lh


def _render_bullets(
    img: Image.Image, slot: Dict, items: Sequence[str], visual_style: str
) -> None:
    """渲染要点条目：每条前置强调色圆点，逐条排布。"""
    items = [str(i).strip() for i in items if str(i).strip()]
    if not items:
        return
    max_items = int(slot.get("max_items", 3) or 3)
    items = items[:max_items]

    W, H = img.size
    bx, by, bw, bh = slot["box"]
    box_px = (int(bx * W), int(by * H), int(bw * W), int(bh * H))
    x, y, w, h = box_px

    bg = _sample_bg(img, box_px)
    scheme = _bg_contrast_scheme(bg, visual_style)
    accent = _accent_color(visual_style)

    if slot.get("style") == "plate":
        _render_plate(img, box_px, scheme["plate"], radius_ratio=0.09)

    pad_x = int(w * 0.045)
    pad_y = int(h * 0.10)
    inner_w = w - pad_x * 2
    inner_h = h - pad_y * 2

    # 每条目分到的高度
    slot_h = inner_h // len(items)
    base_size = int(W * slot.get("size", 0.03))
    # 圆点占位
    dot_gap = int(W * 0.022)
    text_w_avail = inner_w - dot_gap

    draw = ImageDraw.Draw(img)
    cy = y + pad_y
    for item in items:
        font, lines, lh = _fit_lines(
            item, slot.get("weight", "regular"), base_size, text_w_avail, slot_h
        )
        if not lines:
            cy += slot_h
            continue
        block_h = lh * len(lines)
        ty = cy + max(0, (slot_h - block_h) // 2)

        # 强调色圆点，与首行文字垂直居中
        dot_r = max(3, int(lh * 0.16))
        dot_cx = x + pad_x + dot_r
        dot_cy = ty + lh // 2
        draw.ellipse(
            [dot_cx - dot_r, dot_cy - dot_r, dot_cx + dot_r, dot_cy + dot_r],
            fill=(*accent, 255),
        )

        tx0 = x + pad_x + dot_gap
        yy = ty
        halo = (0, 0, 0, 0) if slot.get("style") == "plate" else scheme["halo"]
        halo_w = 0 if slot.get("style") == "plate" else max(1, int(lh * 0.05))
        for ln in lines:
            _draw_text_with_halo(draw, (tx0, yy), ln, font, scheme["text"], halo, halo_w)
            yy += lh
        cy += slot_h


# ---------------------------------------------------------------- 对外接口
def render_overlay(
    src_path: str | Path,
    out_path: str | Path,
    module_key: str,
    copy: Dict,
    visual_style: str = "",
    fix_slots: Optional[Sequence[str]] = None,
) -> Path:
    """把文案合成到图片上，输出成品图。

    参数
    ----
    src_path    原始生成图
    out_path    成品图输出路径
    module_key  模块 key，决定用哪套版式契约
    copy        文案字典 {"title","subtitle","bullets":[...],"badge"}
    visual_style 视觉风格 key，用于自动配色
    fix_slots   需要"磨砂覆盖修正"的槽位名列表。
                视觉质检发现 AI 把标题画错时传入 ["title"]，
                该区域会被模糊盖掉后重新用 PIL 写正确的字。

    返回成品图路径。
    """
    src_path = Path(src_path)
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    img = Image.open(src_path)
    img.load()
    if img.mode != "RGBA":
        img = img.convert("RGBA")

    fix = set(fix_slots or [])

    for slot in get_slots(module_key):
        name = slot["name"]
        role = slot.get("role", "overlay")
        needs_fix = name in fix

        # AI 负责的槽位：只有在质检判定画错时才由我们接管
        if role == "ai" and not needs_fix:
            continue

        value = copy.get(name)
        if value is None:
            continue

        if name == "bullets" or isinstance(value, (list, tuple)):
            items = value if isinstance(value, (list, tuple)) else [value]
            _render_bullets(img, slot, items, visual_style)
        else:
            text = str(value).strip()
            if not text:
                continue
            _render_single_text(img, slot, text, visual_style, frost=needs_fix)

    final = img.convert("RGB")
    suffix = out_path.suffix.lower()
    if suffix in (".jpg", ".jpeg"):
        final.save(out_path, format="JPEG", quality=94)
    elif suffix == ".webp":
        final.save(out_path, format="WEBP", quality=92)
    else:
        final.save(out_path, format="PNG")
    return out_path


def has_renderable_copy(module_key: str, copy: Optional[Dict]) -> bool:
    """该模块是否有需要 PIL 叠加的内容（用于跳过无意义的合成）。"""
    if not copy:
        return False
    for slot in get_slots(module_key, role="overlay"):
        v = copy.get(slot["name"])
        if isinstance(v, (list, tuple)) and any(str(i).strip() for i in v):
            return True
        if isinstance(v, str) and v.strip():
            return True
    return False
