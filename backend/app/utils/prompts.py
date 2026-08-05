"""Prompt 模板库：每个行业、每个模块都对应一份生成提示词模板。"""
from typing import Dict, List, Optional

from app.config import settings
from app.utils.text_layout import describe_ai_text, describe_clean_zones

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

# 模块级「设计感」指导：每个模块该用什么版式、元素、叙事方式。
# 目标：让 AI 不再只出“模特穿着图”或“白底产品图”，而是生成有信息层级、
# 有版式构图、有场景叙事的电商详情页分镜。
MODULE_DESIGN_GUIDE: Dict[str, Dict[str, str]] = {
    "hero": {
        "composition": "full-bleed hero banner with cinematic composition; product as the absolute focal point, placed slightly off-center or centrally with strong negative space; avoid a plain model standing still",
        "visual_elements": "soft atmospheric background (gradient, fabric, natural scene or abstract texture), subtle light rays or lens bloom, elegant product shadow; no cluttered props",
        "information_hierarchy": "one dominant product, generous whitespace, premium headline area left blank for later text overlay",
        "mood": "immersive, aspirational, high-end editorial, like the opening frame of a luxury brand campaign",
        "avoid": "busy backgrounds, multiple models, price tags, hard-sell graphics, cluttered text, snapshot look",
    },
    "core_selling": {
        "composition": "graphic layout: product on one side, visualized benefit icons/blocks on the other; clean grid or asymmetrical editorial layout",
        "visual_elements": "abstract geometric shapes, soft color blocks, line icons rendered as physical objects, close-up detail callouts with elegant leader lines",
        "information_hierarchy": "product + 2-4 selling-point zones, each with an icon/shape and a blank caption area; clear visual rhythm",
        "mood": "confident, benefit-driven, modern DTC brand look",
        "avoid": "plain product-only shot, unstructured collage, tiny unreadable labels, crowded corners",
    },
    "scenario": {
        "composition": "wide lifestyle scene where the product sits naturally within a desirable moment; rule-of-thirds, environmental storytelling",
        "visual_elements": "authentic interior or outdoor setting, natural props that match the product, soft bokeh, human presence only as subtle interaction (hands, silhouette) rather than a full model pose",
        "information_hierarchy": "environment first, product as the hero within the scene; blank upper or lower area for scene caption",
        "mood": "relatable, aspirational, solution-oriented — show the life the product enables",
        "avoid": "white background, product floating in void, stiff model pose, unrelated stock scenery",
    },
    "detail": {
        "composition": "macro or close-up filling most of the frame; extreme detail of fabric weave, stitching, hardware, texture, or material finish",
        "visual_elements": "shallow depth of field, directional light grazing the surface to reveal texture, subtle reflection, soft gradient backdrop",
        "information_hierarchy": "one hero detail with possible secondary detail inset; no text, let material speak",
        "mood": "craftsmanship, precision, tactile quality, premium materials",
        "avoid": "full product flat lay, softbox glare, oversaturated colors, blurry details",
    },
    "sku": {
        "composition": "organized product matrix or color lineup on a continuous surface; consistent angle and lighting across all variants",
        "visual_elements": "identical soft background, neatly spaced variants (colors/sizes/styles), subtle shadows grounding each item",
        "information_hierarchy": "grid of 3-6 variants, visually aligned, equal visual weight; blank labels implied by spacing",
        "mood": "clean, decisive, easy to shop, like a curated lookbook spread",
        "avoid": "random angles, mismatched lighting, overlapping items, chaotic collage",
    },
    "size_chart": {
        "composition": "product shown with a stylized figure, mannequin, or dimensional diagram; generous negative space for measurements",
        "visual_elements": "thin elegant measurement lines, soft human silhouette or wireframe mannequin, product worn or placed beside the scale reference",
        "information_hierarchy": "product + scale reference + clean annotation zones; numbers should feel spacious",
        "mood": "helpful, trustworthy, minimalist technical illustration",
        "avoid": "cramped tables, realistic faces on models, distorted proportions, heavy grids",
    },
    "spec_param": {
        "composition": "information-graphics layout: product image integrated into a clean grid of spec blocks; modern dashboard feel",
        "visual_elements": "rounded rectangles, thin iconography, subtle separators, consistent accent color, product peeking from one side",
        "information_hierarchy": "product photo + 4-6 spec zones (material, weight, dimensions, origin, care); clear modular blocks",
        "mood": "transparent, credible, organized — turn specs into a visual story",
        "avoid": "plain text table screenshot, overcrowded labels, low-contrast gray text",
    },
    "after_sales": {
        "composition": "trust-badge wall or guarantee card layout; symmetrical or centered reassurance design",
        "visual_elements": "seal/badge motifs rendered as soft 3D shapes, shield icons, checkmarks, gentle ribbon or certificate texture",
        "information_hierarchy": "one central promise (e.g., guarantee badge) surrounded by 3-4 support icons; blank areas for policy text",
        "mood": "reassuring, official-but-friendly, risk-free purchase confidence",
        "avoid": "legal-document aesthetic, dense paragraphs, aggressive red warning colors",
    },
    "brand_story": {
        "composition": "narrative split-frame or layered scene: product + raw material + maker/environment detail; editorial magazine spread",
        "visual_elements": "natural raw ingredients or craftsmanship details, soft landscape or workshop ambience, handwritten-style texture (no real text), warm analog grain",
        "information_hierarchy": "visual story arc from origin to product; image should feel like a magazine photo essay",
        "mood": "authentic, emotional, heritage or purpose-driven",
        "avoid": "generic brand stock photo, logo-only image, disconnected collage",
    },
    "notice": {
        "composition": "calm instructional layout: one central product or icon with 2-4 care symbols arranged around it",
        "visual_elements": "soft iconography (wash, iron, dry, store), gentle color-coded circles, clean line art",
        "information_hierarchy": "product/icon at center + care symbols in a clear ring or list; breathable spacing",
        "mood": "gentle guidance, easy to follow, premium customer care",
        "avoid": "dense warning labels, alarming icons, red caution signs, hard-to-read small text",
    },
    "qualification": {
        "composition": "authority wall: certificates/license cards arranged in a refined gallery grid, product as anchor",
        "visual_elements": "elegant frames or embossed seals, subtle gold foil accents, clean document-like cards with soft shadows",
        "information_hierarchy": "product or brand mark + 2-4 qualification badges; formal but not bureaucratic",
        "mood": "certified, trustworthy, premium quality assurance",
        "avoid": "pixelated certificate screenshots, stacked unreadable documents, gaudy gold backgrounds",
    },
    "faq": {
        "composition": "Q&A conversation layout: soft chat bubbles or accordion panels floating around a small product still life",
        "visual_elements": "rounded speech bubbles, minimal line icons (question mark, checkmark), product placed unobtrusively",
        "information_hierarchy": "product + 2-3 question/answer zones; friendly visual rhythm",
        "mood": "approachable, helpful, conversational",
        "avoid": "plain text screenshot, wall of text, no visual anchors",
    },
    "factory": {
        "composition": "wide-angle or detail shot of a clean production environment; product in foreground with craft process behind",
        "visual_elements": "modern machinery, artisan hands at work, raw materials, clean workshop lighting, shallow depth of field",
        "information_hierarchy": "process + product + environment; show capability without clutter",
        "mood": "professional, capable, behind-the-scenes authenticity",
        "avoid": "messy factory floor, unrelated machinery, dark gritty look, stock photos of strangers",
    },
    "package": {
        "composition": "flat-lay unboxing scene or gift-style arrangement: box, wrapping, product, and a small accessory",
        "visual_elements": "premium packaging with subtle branding area, tissue paper, ribbon or seal, soft surface texture",
        "information_hierarchy": "package as hero + product partially revealed; all elements aligned to a refined grid",
        "mood": "gift-worthy, premium unboxing experience, attention to presentation",
        "avoid": "crushed boxes, messy background, excessive plastic, random props",
    },
    "logistics": {
        "composition": "journey visualization: stylized map route, package in motion, timeline or checkpoint layout",
        "visual_elements": "soft map abstraction, truck/plane/warehouse icons rendered as clean shapes, delivery package with product branding",
        "information_hierarchy": "package + route/timeline + 2-3 milestone icons; blank zones for speed claims",
        "mood": "fast, reliable, transparent, global-but-friendly",
        "avoid": "realistic map screenshots, crowded shipping labels, confusing arrows",
    },
    "pain_point": {
        "composition": "before/after or problem-to-solution split frame; emotional hook on one side, relief on the other",
        "visual_elements": "soft visual metaphor (wrinkled vs smooth, dark vs bright), one small product as the solution, subtle color temperature shift",
        "information_hierarchy": "pain scenario → product → relief outcome; story in one frame",
        "mood": "empathetic, transformational, relatable without being negative",
        "avoid": "gross or distressing imagery, aggressive red X marks, cluttered before/after collage",
    },
    "lifestyle": {
        "composition": "aspirational scene with product naturally in use: morning routine, travel moment, social gathering, or cozy corner",
        "visual_elements": "warm natural light, authentic environment, human interaction implied, complementary props that reinforce the mood",
        "information_hierarchy": "scene mood first, product as the enabler; blank headline area for lifestyle copy",
        "mood": "content, aspirational, 'this could be my life' — emotional sell",
        "avoid": "studio product-only shot, stiff model pose, unrelated luxury backdrop",
    },
    "comparison": {
        "composition": "clean comparison table or split-screen: our product on the left, generic alternative on the right, advantage markers on our side",
        "visual_elements": "two columns with subtle divider, checkmark vs minimal dot, product hero shots at top of each column, soft brand accent color highlighting the winner",
        "information_hierarchy": "product vs competitor + 3-5 comparison rows + clear visual winner cue",
        "mood": "confident, factual, premium-but-fair",
        "avoid": "crowded spreadsheet screenshot, mocking competitor design, unreadable small rows",
    },
    "cta": {
        "composition": "bold final-frame layout: product hero + large clear button area + urgency element (subtle badge or countdown shape)",
        "visual_elements": "soft gradient background, product floating or placed with confidence, rounded button-shaped block, trust micro-badges",
        "information_hierarchy": "product + value statement zone + prominent CTA block + 1-2 trust signals",
        "mood": "decisive, exciting-but-premium, final nudge to purchase",
        "avoid": "garish sale graphics, flashing colors, too many badges, cheap discount aesthetic",
    },
}

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


def build_design_guide_block(
    module_key: str,
    copy: Optional[Dict] = None,
    ai_render_headline: Optional[bool] = None,
) -> str:
    """返回模块级设计指导文本（用于追加到已有 prompt 末尾，确保模板 prompt 也带设计感约束）。

    copy 为该模块结构化文案；ai_render_headline 控制是否让 AI 直接画中文主标题。
    """
    guide = MODULE_DESIGN_GUIDE.get(module_key)
    if not guide:
        return ""

    ai_render = ai_render_headline if ai_render_headline is not None else settings.ai_render_headline
    blocks: List[str] = [
        "",
        "[DESIGN ENFORCEMENT — this panel must look like a designed e-commerce detail-page section]",
        f"Composition: {guide['composition']}.",
        f"Visual elements: {guide['visual_elements']}.",
        f"Information hierarchy: {guide['information_hierarchy']}.",
        f"Mood: {guide['mood']}.",
        f"Avoid: {guide['avoid']}.",
    ]

    if ai_render and copy:
        ai_text = describe_ai_text(module_key, copy)
        if ai_text:
            blocks.append(ai_text)

    clean_zones = describe_clean_zones(module_key)
    if clean_zones:
        blocks.append(clean_zones)
    else:
        # 没有明确 overlay 区域时，至少保留“不要画额外文字”的兜底
        blocks.append(
            "Do NOT render any extra readable text, letters, watermarks, or logos beyond the headline specified above."
        )

    return "\n".join(blocks)


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
    copy: Optional[Dict] = None,
    ai_render_headline: Optional[bool] = None,
) -> str:
    """根据模块和上下文拼装一个生图 prompt。

    此处为通用模板，未来可被 AI 改写。
    style_lock 为「视觉调性锁定」段落（来自 build_style_lock），由调用方统一注入，
    保证同一项目所有模块共用同一套调性规范。
    product_selling_points 来自产品分析/用户提炼，确保卖点融入每张图。
    copy 为该模块结构化文案；ai_render_headline 控制是否让 AI 直接画中文主标题。
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

    # 模块设计感指导
    guide = MODULE_DESIGN_GUIDE.get(module_key) or MODULE_DESIGN_GUIDE.get("hero")

    ai_render = ai_render_headline if ai_render_headline is not None else settings.ai_render_headline

    base = (
        f"Product: {product_name}. "
        f"Module: {module['name_zh']} - {module['desc_zh']}. "
        f"Goal: design-driven e-commerce detail page panel for {language} market, "
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

    # 注入设计感版式与叙事约束（解决“只是模特穿着图”的问题）
    blocks: List[str] = [
        "",
        "[DESIGN DIRECTION — this is a designed e-commerce panel, not a plain product photo]",
        f"Composition: {guide['composition']}.",
        f"Visual elements: {guide['visual_elements']}.",
        f"Information hierarchy: {guide['information_hierarchy']}.",
        f"Mood: {guide['mood']}.",
        f"Avoid: {guide['avoid']}.",
    ]

    if ai_render and copy:
        ai_text = describe_ai_text(module_key, copy)
        if ai_text:
            blocks.append(ai_text)

    clean_zones = describe_clean_zones(module_key)
    if clean_zones:
        blocks.append(clean_zones)
    else:
        blocks.append(
            "Do NOT render any extra readable text, letters, watermarks, or logos beyond the headline specified above."
        )

    base = base.rstrip(". \n") + "." + "\n".join(blocks)

    base += "\nTechnical: sharp focus, well-lit, 8K, high detail, photorealistic."
    if style_lock:
        base = (base.rstrip(". \n") + ". " + style_lock).strip()
    return base
