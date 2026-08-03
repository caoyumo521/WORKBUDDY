"""Prompt 模板库：每个行业、每个模块都对应一份生成提示词模板。"""
from typing import Dict, List

# 通用 19 大模块（对应 51aic / yilaitu 通用模块）
COMMON_MODULES: List[Dict] = [
    {"key": "hero", "name_zh": "首屏海报图", "desc_zh": "快速抓住用户注意力，传递产品核心定位"},
    {"key": "core_selling", "name_zh": "核心卖点图", "desc_zh": "直击产品核心优势，突出亮点"},
    {"key": "scenario", "name_zh": "场景展示图", "desc_zh": "展示真实使用场景，直观感受产品价值"},
    {"key": "detail", "name_zh": "细节展示图", "desc_zh": "放大核心细节，直观呈现工艺品质与精致做工"},
    {"key": "sku", "name_zh": "SKU展示图", "desc_zh": "清晰展示规格 SKU、颜色、款式、型号"},
    {"key": "size_chart", "name_zh": "尺寸图", "desc_zh": "标注产品尺寸数据"},
    {"key": "spec_param", "name_zh": "规格参数图", "desc_zh": "呈现规格参数，清晰展示产品硬核信息"},
    {"key": "after_sales", "name_zh": "售后保障图", "desc_zh": "展示售后政策，质保退换运费险说明"},
    {"key": "brand_story", "name_zh": "品牌故事图", "desc_zh": "讲述品牌理念与历程"},
    {"key": "notice", "name_zh": "注意事项图", "desc_zh": "明确使用与保养注意事项"},
    {"key": "qualification", "name_zh": "资质认证图", "desc_zh": "展示权威资质认证，保障正品"},
    {"key": "faq", "name_zh": "常见问题图", "desc_zh": "解答常见疑问"},
    {"key": "factory", "name_zh": "工厂实力图", "desc_zh": "展示生产实力与工艺"},
    {"key": "package", "name_zh": "包装展示图", "desc_zh": "展示产品包装全貌"},
    {"key": "logistics", "name_zh": "发货物流图", "desc_zh": "发货流程与物流时效"},
    {"key": "pain_point", "name_zh": "用户痛点", "desc_zh": "目标用户在当前场景下的核心痛点"},
    {"key": "lifestyle", "name_zh": "生活方式", "desc_zh": "产品融入美好生活方式"},
    {"key": "comparison", "name_zh": "对比模块", "desc_zh": "对比同类产品突出优势"},
    {"key": "cta", "name_zh": "购买引导", "desc_zh": "促单转化模块"},
]

# 各行业推荐模块
INDUSTRY_MODULE_PRESET: Dict[str, List[str]] = {
    "apparel": ["hero", "pain_point", "core_selling", "material", "detail", "craft", "scenario", "size_chart", "after_sales", "cta"],
    "shoes": ["hero", "core_selling", "material", "detail", "scenario", "lifestyle", "size_chart", "after_sales", "cta"],
    "bag": ["hero", "core_selling", "material", "craft", "detail", "scenario", "size_chart", "qualification", "after_sales", "cta"],
    "pet": ["hero", "pain_point", "core_selling", "feature", "scenario", "material", "qualification", "after_sales", "cta"],
    "makeup": ["hero", "core_selling", "feature", "scenario", "detail", "ingredient", "review", "qualification", "cta"],
    "skincare": ["hero", "pain_point", "ingredient", "core_selling", "feature", "scenario", "review", "qualification", "cta"],
    "3c": ["hero", "core_selling", "tech", "feature", "detail", "scenario", "spec_param", "after_sales", "cta"],
    "home": ["hero", "pain_point", "core_selling", "scenario", "detail", "size_chart", "spec_param", "after_sales", "cta"],
    "outdoor": ["hero", "pain_point", "core_selling", "scenario", "material", "craft", "detail", "spec_param", "cta"],
    "sports": ["hero", "core_selling", "tech", "feature", "scenario", "detail", "size_chart", "cta"],
    "baby": ["hero", "core_selling", "material", "qualification", "scenario", "feature", "notice", "after_sales", "cta"],
    "food": ["hero", "pain_point", "core_selling", "ingredient", "scenario", "qualification", "factory", "logistics", "cta"],
    "jewelry": ["hero", "core_selling", "material", "craft", "detail", "scenario", "package", "qualification", "cta"],
    "auto": ["hero", "core_selling", "tech", "feature", "scenario", "spec_param", "after_sales", "cta"],
}

# 各行业风格 prompt 偏好
INDUSTRY_STYLE_HINT: Dict[str, str] = {
    "apparel": "fashion editorial photography, soft natural light, premium fabric texture",
    "shoes": "studio product photography, dynamic angle, athletic lifestyle",
    "bag": "luxury product still life, dramatic lighting, leather grain detail",
    "pet": "warm friendly scene, shallow depth of field, pet lifestyle",
    "makeup": "high-end beauty close-up, soft studio light, glossy finish",
    "skincare": "clean clinical aesthetic, fresh dewy textures, water drops",
    "3c": "futuristic tech background, neon glow, minimalist product shot",
    "home": "cozy interior scene, natural daylight, lifestyle warmth",
    "outdoor": "epic outdoor landscape, golden hour, adventure atmosphere",
    "sports": "high-energy motion, dynamic blur, athlete action",
    "baby": "soft pastel palette, tender scene, safety focus",
    "food": "appetizing food photography, steam, fresh ingredients, top-down",
    "jewelry": "macro product photography, black velvet background, sparkle highlights",
    "auto": "studio car photography, dramatic reflections, sleek and powerful",
}

# 平台
PLATFORMS = [
    {"key": "auto", "name_zh": "智能匹配", "icon": "AI"},
    {"key": "1688", "name_zh": "1688", "icon": "1688"},
    {"key": "taobao", "name_zh": "淘宝", "icon": "TB"},
    {"key": "tmall", "name_zh": "天猫", "icon": "TM"},
    {"key": "pdd", "name_zh": "拼多多", "icon": "PDD"},
    {"key": "jd", "name_zh": "京东", "icon": "JD"},
    {"key": "douyin", "name_zh": "抖音", "icon": "DY"},
    {"key": "amazon", "name_zh": "亚马逊", "icon": "AZ"},
    {"key": "shopify", "name_zh": "Shopify", "icon": "SH"},
    {"key": "tiktok_shop", "name_zh": "TikTok Shop", "icon": "TT"},
    {"key": "xiaohongshu", "name_zh": "小红书", "icon": "XHS"},
    {"key": "independent", "name_zh": "独立站", "icon": "WEB"},
]

# 行业
INDUSTRIES = [
    {"key": "apparel", "name_zh": "服装"},
    {"key": "shoes", "name_zh": "鞋类"},
    {"key": "bag", "name_zh": "箱包"},
    {"key": "pet", "name_zh": "宠物"},
    {"key": "makeup", "name_zh": "美妆"},
    {"key": "skincare", "name_zh": "护肤"},
    {"key": "3c", "name_zh": "3C电子"},
    {"key": "home", "name_zh": "家居"},
    {"key": "outdoor", "name_zh": "户外"},
    {"key": "sports", "name_zh": "运动"},
    {"key": "baby", "name_zh": "母婴"},
    {"key": "food", "name_zh": "食品"},
    {"key": "jewelry", "name_zh": "珠宝配饰"},
    {"key": "auto", "name_zh": "汽车用品"},
]

# 语言
LANGUAGES = [
    {"key": "zh-CN", "name_zh": "简体中文", "flag": "🇨🇳"},
    {"key": "zh-TW", "name_zh": "繁体中文", "flag": "🇭🇰"},
    {"key": "en-US", "name_zh": "英语", "flag": "🇺🇸"},
    {"key": "ja-JP", "name_zh": "日语", "flag": "🇯🇵"},
    {"key": "ko-KR", "name_zh": "韩语", "flag": "🇰🇷"},
    {"key": "de-DE", "name_zh": "德语", "flag": "🇩🇪"},
    {"key": "fr-FR", "name_zh": "法语", "flag": "🇫🇷"},
    {"key": "es-ES", "name_zh": "西班牙语", "flag": "🇪🇸"},
    {"key": "ar", "name_zh": "阿拉伯语", "flag": "🇦🇪"},
    {"key": "pt-BR", "name_zh": "葡萄牙语", "flag": "🇧🇷"},
    {"key": "ru-RU", "name_zh": "俄语", "flag": "🇷🇺"},
    {"key": "th-TH", "name_zh": "泰语", "flag": "🇹🇭"},
    {"key": "vi-VN", "name_zh": "越南语", "flag": "🇻🇳"},
]

# 比例
ASPECT_RATIOS = [
    {"key": "1:1", "name_zh": "1:1 正方形"},
    {"key": "2:3", "name_zh": "2:3 竖版"},
    {"key": "3:2", "name_zh": "3:2 横版"},
    {"key": "3:4", "name_zh": "3:4 竖版"},
    {"key": "4:3", "name_zh": "4:3 横版"},
    {"key": "4:5", "name_zh": "4:5 竖版"},
    {"key": "5:4", "name_zh": "5:4 横版"},
    {"key": "9:16", "name_zh": "9:16 手机竖版"},
    {"key": "16:9", "name_zh": "16:9 横屏"},
    {"key": "21:9", "name_zh": "21:9 宽屏"},
]

# 视觉风格
VISUAL_STYLES = [
    {"key": "minimal", "name_zh": "极简留白"},
    {"key": "warm", "name_zh": "温暖生活"},
    {"key": "luxury", "name_zh": "轻奢质感"},
    {"key": "tech", "name_zh": "科技未来"},
    {"key": "fresh", "name_zh": "清新自然"},
    {"key": "vibrant", "name_zh": "高饱和活力"},
    {"key": "magazine", "name_zh": "杂志大片"},
    {"key": "japanese", "name_zh": "日系治愈"},
    {"key": "street", "name_zh": "潮流街头"},
    {"key": "retro", "name_zh": "复古怀旧"},
]

# 视觉调性锁定：每种风格一套「贯穿整个详情页」的统一视觉规范。
# 关键：同一项目内所有模块共用【同一份】规范，从而解决「上下调性不一致」。
# 字段：
#   palette   —— 强制统一的配色���色值/色名）
#   lighting  —— 强制统一的光影方向
#   mood      —— 强制统一的氛围/情绪
#   treatment —— 统一的摄影质感/处理方式
#   negative  —— 负向约束（避免风格跑偏）
STYLE_PROFILES: Dict[str, Dict[str, str]] = {
    "minimal": {
        "name_en": "Minimal & Whitespace",
        "palette": "warm ivory #F6F3ED, soft taupe #B8AFA2, charcoal #2B2B2B; only one muted accent color allowed",
        "lighting": "soft diffused daylight from upper-left, even illumination, barely-there shadow, seamless clean backdrop",
        "mood": "calm, refined, premium, restrained, breathable",
        "treatment": "minimalist studio product photography, generous negative space, ultra-clean light-grey background",
        "negative": "busy patterns, heavy contrast, saturated neon, grunge, 3D render, cartoon, cluttered background, lens flare",
    },
    "warm": {
        "name_en": "Warm Lifestyle",
        "palette": "cream #FBF3E7, terracotta #C97B5A, olive #7A7A52, warm wood tones; cozy earth palette",
        "lighting": "golden-hour window light, warm tone, soft shadows, lived-in atmosphere",
        "mood": "warm, inviting, homely, heartfelt, approachable",
        "treatment": "lifestyle product photography in a real home setting, shallow depth of field, natural grain",
        "negative": "cold blue light, sterile studio, neon, flat illustration, harsh flash, clinical look",
    },
    "luxury": {
        "name_en": "Luxury & Premium",
        "palette": "champagne gold #C9A24B, deep espresso #3A2E25, ivory #F3ECE0, onyx black; restrained metallic accents",
        "lighting": "soft directional studio light with a subtle rim light, deep elegant shadows, dramatic contrast",
        "mood": "elegant, exclusive, sophisticated, opulent yet restrained",
        "treatment": "high-end product still life, fine detail, shallow depth of field, magazine-grade retouching",
        "negative": "cheap look, clashing colors, neon, cartoon, cluttered, overexposed, flat lighting",
    },
    "tech": {
        "name_en": "Tech & Futuristic",
        "palette": "deep space blue #0B1020, electric cyan #38E1FF, neutral graphite #1F2430, white highlights",
        "lighting": "cool directional light with cyan rim glow, subtle volumetric haze, crisp reflections",
        "mood": "futuristic, precise, innovative, confident, sleek",
        "treatment": "minimalist tech product shot, dark gradient backdrop, sharp reflections, slight glow",
        "negative": "warm cozy tones, hand-drawn, cartoon, cluttered, soft pastel, vintage grain",
    },
    "fresh": {
        "name_en": "Fresh & Natural",
        "palette": "mint #CFE8DC, sky #BFE3F2, leaf green #7FB069, white; airy natural palette",
        "lighting": "bright soft natural daylight, airy and even, gentle shadow",
        "mood": "fresh, clean, healthy, pure, uplifting",
        "treatment": "clean bright product photography, dewy textures, white/light backdrop, crisp and simple",
        "negative": "dark moody tones, heavy grunge, neon, cluttered, greasy look, oversaturation",
    },
    "vibrant": {
        "name_en": "Vibrant & Energetic",
        "palette": "coral #FF6B5E, sunshine yellow #FFD23F, electric blue #3DA5FF, magenta #E25BD6; bold saturated blocks",
        "lighting": "bright even studio light, punchy highlights, vivid and clean",
        "mood": "energetic, playful, bold, youthful, confident",
        "treatment": "high-saturation product photography, solid color backgrounds, graphic and punchy",
        "negative": "muted desaturated tones, gloomy, cluttered, grainy, monochrome, low contrast",
    },
    "magazine": {
        "name_en": "Editorial Magazine",
        "palette": "off-white #F2EFE9, ink black #1A1A1A, camel #C19A6B; refined editorial palette",
        "lighting": "fashion studio lighting, soft key with gentle fill, elegant long shadow",
        "mood": "editorial, sophisticated, aspirational, chic",
        "treatment": "fashion-editorial product photography, large negative space, refined composition, film-like",
        "negative": "cheap look, neon, cartoon, cluttered, harsh flash, oversaturated",
    },
    "japanese": {
        "name_en": "Japanese Healing",
        "palette": "rice white #F7F4EF, matcha #A7B894, muted clay #C9B7A4, soft grey-blue #9AA7AD; muted gentle palette",
        "lighting": "soft diffuse daylight, calm and even, no harsh shadow",
        "mood": "tranquil, gentle, healing, minimal, mindful",
        "treatment": "quiet still-life product photography, lots of breathing room, soft matte texture",
        "negative": "loud colors, neon, busy patterns, harsh contrast, cluttered, cartoon",
    },
    "street": {
        "name_en": "Urban Street",
        "palette": "concrete grey #8C8C8C, brick #A85A45, acid green #B6FF3C, black; gritty urban palette",
        "lighting": "mixed urban light, directional hard-soft contrast, urban reflections",
        "mood": "cool, rebellious, authentic, youthful, edgy",
        "treatment": "street-style product photography, urban backdrop, dynamic angle, raw texture",
        "negative": "overly clean studio, pastel, romantic, soft vintage, cluttered",
    },
    "retro": {
        "name_en": "Retro & Nostalgic",
        "palette": "faded mustard #D9A441, burnt orange #C4622D, teal #3E8E8A, cream #EDE3D0; washed vintage palette",
        "lighting": "warm soft light, slight film halation, gentle vignette",
        "mood": "nostalgic, warm, timeless, characterful",
        "treatment": "retro film photography, soft grain, slightly faded color, vintage tones",
        "negative": "ultra-modern neon, crisp digital clean, cartoon, cluttered, high-contrast clinical",
    },
    # 兜底：未指定风格时使用
    "_default": {
        "name_en": "Cohesive E-commerce",
        "palette": "neutral commercial palette; brand primary color as the only accent",
        "lighting": "soft even studio lighting, lightly directional, clean backdrop",
        "mood": "clean, trustworthy, professional, inviting",
        "treatment": "professional e-commerce product photography, crisp and commercial",
        "negative": "inconsistent style, mixed lighting, cartoon, 3D render, cluttered, harsh shadow",
    },
}


def get_style_profile(visual_style: str) -> Dict[str, str]:
    """根据视觉风格 key 取统一规范；未命中则回退到 _default。"""
    return STYLE_PROFILES.get(visual_style) or STYLE_PROFILES["_default"]


def build_style_lock(visual_style: str, industry: str = "") -> str:
    """生成一份「视觉调性锁定」段落。

    同一项目的所有模块必须共用【同一份】返回内容，才能保证整页调性统一。
    以英文输出（gpt-image 系列对英文理解最佳）。
    """
    profile = get_style_profile(visual_style)
    industry_style = INDUSTRY_STYLE_HINT.get(industry, "")

    block = (
        "[UNIFIED VISUAL IDENTITY — IDENTICAL for every image in this product series]\n"
        f"- Color palette (must stay identical across all panels): {profile['palette']}\n"
        f"- Lighting (must stay identical across all panels): {profile['lighting']}\n"
        f"- Mood & tone (must stay identical across all panels): {profile['mood']}\n"
        f"- Photographic treatment: {profile['treatment']}\n"
    )
    if industry_style:
        block += f"- Product context & genre: {industry_style}\n"
    block += (
        "CONSISTENCY RULE: This image is ONE panel of a single e-commerce detail page. "
        "It MUST share the EXACT same color scheme, lighting direction, mood, composition rhythm, "
        "and brand tone as every other panel. Do NOT shift style, saturation, color temperature, "
        "or atmosphere between panels — they must read as one continuous, cohesive page.\n"
        f"Avoid (do not include): {profile['negative']}."
    )
    return block.strip()


def build_module_prompt(
    module_key: str,
    product_name: str,
    industry: str,
    language: str,
    visual_style: str,
    extra: str = "",
    product_description: str = "",
    product_selling_points: str = "",
    style_lock: str = "",
) -> str:
    """根据模块和上下文拼装一个生图 prompt。

    此处为通用模板，未来可被 AI 改写。
    style_lock 为「视觉调性锁定」段落（来自 build_style_lock），由调用方统一注入，
    保证同一项目所有模块共用同一套调性规范。
    product_selling_points 来自产品分析/用户提炼，确保卖点融入每张图。
    """
    module = next((m for m in COMMON_MODULES if m["key"] == module_key), None)
    if not module:
        module = {"key": module_key, "name_zh": module_key, "desc_zh": ""}

    style_text = ""
    if visual_style:
        style = next((v for v in VISUAL_STYLES if v["key"] == visual_style), None)
        if style:
            style_text = f", {style['name_zh']} 风格"

    industry_style = INDUSTRY_STYLE_HINT.get(industry, "")

    base = (
        f"Product: {product_name}. "
        f"Module: {module['name_zh']} - {module['desc_zh']}. "
        f"Goal: e-commerce detail page image for {language} market, "
        f"high quality, professional product photography{style_text}. "
    )
    if industry_style:
        base += f"Industry visual hint: {industry_style}. "
    if product_description:
        base += f"Product description: {product_description}. "
    if product_selling_points:
        base += f"Key selling points to feature in the image: {product_selling_points}. "
    if extra:
        base += f"Additional: {extra}. "
    base += "Sharp focus, well-lit, no text overlay, no watermark, 8K, high detail."
    if style_lock:
        base = (base.rstrip(". \n") + ". " + style_lock).strip()
    return base
