"""模块文案生成器：为详情页每个模块生成结构化中文文案。

输出格式
--------
{ "module_key": { "title": "...", "subtitle": "...", "bullets": [...], "badge": "..." } }

所有字段均为可选；只有对应模块版式里存在同名槽位时才会生成。
字数会被截断到 text_layout 中 slot.max_chars 以内，保证 PIL 不会溢出。

调用方式
--------
    copy = await generate_module_copy(project)
    project.module_copy = copy
"""
from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, List, Optional

import httpx

from app.config import settings
from app.utils.prompts import COMMON_MODULES
from app.utils.text_layout import MODULE_TEXT_LAYOUT, SLOT_SEMANTIC

logger = logging.getLogger(__name__)

COPY_SYSTEM = """你是一名资深电商文案，擅长为详情页每个模块撰写短促有力、卖点突出的中文文案。
请严格按 JSON 格式输出，不要写任何解释。"""

COPY_USER_TEMPLATE = """请为以下产品撰写详情页各模块文案。

【产品信息】
- 产品名称: {product_name}
- 行业: {industry}
- 目标市场: {target_market}
- 目标平台: {target_platform}
- 视觉风格: {visual_style}
- 核心卖点: {selling_points}
- 目标用户: {target_audience}
- 产品描述: {product_description}
- 附加要求: {extra}

【模块与字数约束】
{modules}

【输出格式】
输出一个 JSON 对象，key 是模块 key，value 是文案对象。只包含上表列出的 key：
{{
  "模块key": {{
    "title": "主标题，不超过字数",
    "subtitle": "副标题/一句话说明",
    "bullets": ["卖点1", "卖点2", "卖点3"],
    "badge": "角标或按钮文字"
  }},
  ...
}}

要求：
1. 标题要短促、有画面感和购买驱动力，适合被 AI 直接画进画面。
2. 卖点条要具体、口语化，避免空泛形容词；每条尽量押韵或对仗。
3. 严格遵循上表的字数上限，超出会被截断。
4. 不要输出 Markdown 代码块，只输出纯 JSON。"""


# ---------------------------------------------------------------- 模板回退
_FALLBACK_TITLE_TEMPLATES: Dict[str, List[str]] = {
    "hero": ["{name}", "全新{name}", "遇见{name}"],
    "core_selling": ["核心卖点", "为什么选{name}", "一枪心动"],
    "scenario": ["真实场景", "每天的美好", "{name}在身边"],
    "detail": ["细节见真章", "精工细作", "放大看品质"],
    "sku": ["多色可选", "随心搭配", "找到你的款"],
    "size_chart": ["尺寸指南", "合身更自在", "选对尺码"],
    "spec_param": ["硬核参数", "专业配置", "一目了然"],
    "after_sales": ["售后无忧", "买得放心", "全程保障"],
    "brand_story": ["品牌故事", "我们的初心", "关于我们"],
    "notice": ["使用须知", "温馨提示", "注意这件事"],
    "qualification": ["权威认证", "品质背书", "值得信赖"],
    "faq": ["常见问题", "你可能想问", "一键解惑"],
    "factory": ["工厂实力", "源头好货", "匠心制造"],
    "package": ["包装展示", "开箱惊喜", "完好送达"],
    "logistics": ["发货物流", "极速送达", "全程可查"],
    "pain_point": ["你也有这烦恼？", "告别这些困扰", "痛点终结者"],
    "lifestyle": ["理想生活", "品质日常", "生活方式"],
    "comparison": ["对比见真章", "为什么选择我", "优势明显"],
    "cta": ["立即抢购", "限时特惠", "马上拥有"],
    "material": ["精选材质", "好材料会说话", "材质解析"],
    "craft": ["匠心工艺", "工艺揭秘", "精工细作"],
    "feature": ["产品亮点", "功能一览", "特色功能"],
    "tech": ["核心技术", "黑科技揭秘", "技术领先"],
    "ingredient": ["成分揭秘", "天然配方", "安心成分"],
    "review": ["用户好评", "真实反馈", "口碑见证"],
}

_FALLBACK_BULLETS: Dict[str, List[str]] = {
    "hero": [],
    "core_selling": ["精选材质，触感升级", "匠心工艺，细节满分", "用心设计，体验更佳"],
    "scenario": ["居家场景舒适自然", "外出携带轻松方便", "送礼自用两相宜"],
    "detail": ["精密缝线，牢固耐穿", "细腻纹理，质感在线", "严选配件，经久耐用"],
    "sku": ["经典款百搭不挑人", "限量色个性出众", "组合装更划算"],
    "size_chart": ["对照身高体重选码", "详细尺码一图看懂", "不确定可咨询客服"],
    "spec_param": ["核心参数真实标注", "通过国家质量检测", "厂家直供品质稳定"],
    "after_sales": ["7天无理由退换", "正品保证假一赔十", "专属客服快速响应"],
    "brand_story": [],
    "notice": ["按说明正确使用", "避免长时间暴晒", "定期清洁保养"],
    "qualification": ["国家质量认证", "行业检测报告", "品牌授权正品"],
    "faq": ["是否支持退换？支持", "多久发货？48小时内", "如何保养？详见说明"],
    "factory": ["自建工厂直供", "标准化生产流程", "质检层层把关"],
    "package": ["独立包装防挤压", "附赠使用说明书", "礼品级开箱体验"],
    "logistics": ["现货48小时发货", "全国包邮到家", "物流轨迹实时查"],
    "pain_point": ["告别粗糙廉价感", "解决使用中的不便", "省心不踩雷"],
    "lifestyle": ["融入品质日常", "提升生活仪式感", "简单也能很高级"],
    "comparison": ["材质更优更耐用", "设计更懂用户需求", "售后更有保障"],
    "cta": ["限时优惠", "库存紧张", "点击立即购买"],
    "material": ["亲肤透气不闷热", "环保材质无异味", "耐磨抗皱易打理"],
    "craft": ["传统工艺与现代设计结合", "多道工序精心打磨", "细节处见匠心"],
    "feature": ["功能实用不花哨", "操作简单上手快", "效果看得见"],
    "tech": ["核心技术自主研发", "性能稳定功耗低", "智能体验再升级"],
    "ingredient": ["天然植萃更温和", "无添加更安心", "科学配比更有效"],
    "review": ["买家真实好评", "复购率超高", "口碑看得见"],
}


# ---------------------------------------------------------------- 内部工具
def _module_name_map() -> Dict[str, str]:
    return {m["key"]: m["name_zh"] for m in COMMON_MODULES}


def _schema_for_module(module_key: str) -> Dict[str, Any]:
    """把 text_layout 中的 slot 约束转成给 LLM 的字段说明。"""
    layout = MODULE_TEXT_LAYOUT.get(module_key) or {"slots": []}
    fields: Dict[str, Any] = {}
    for slot in layout.get("slots", []):
        name = slot["name"]
        if name in fields:
            continue
        max_chars = int(slot.get("max_chars", 20))
        semantic = SLOT_SEMANTIC.get(name, name)
        if name == "bullets":
            max_items = int(slot.get("max_items", 3))
            fields[name] = {
                "type": "array",
                "max_items": max_items,
                "item_max_chars": max_chars,
                "description": f"{semantic}，最多 {max_items} 条，每条不超过 {max_chars} 字",
            }
        else:
            fields[name] = {
                "type": "string",
                "max_chars": max_chars,
                "description": f"{semantic}，不超过 {max_chars} 字",
            }
    return fields


def _truncate(text: str, max_chars: int) -> str:
    """硬截断到指定字数（中文按字符计）。"""
    if not text:
        return ""
    text = str(text).strip()
    return text[:max(max_chars, 1)]


def _truncate_copy(module_key: str, copy: Dict[str, Any]) -> Dict[str, Any]:
    """按版式约束截断文案，防止叠字溢出。"""
    schema = _schema_for_module(module_key)
    out: Dict[str, Any] = {}
    for name, spec in schema.items():
        value = copy.get(name)
        if value is None:
            continue
        if spec["type"] == "array" and isinstance(value, (list, tuple)):
            items = [str(i).strip() for i in value if str(i).strip()]
            items = items[: spec.get("max_items", 3)]
            out[name] = [_truncate(i, spec["item_max_chars"]) for i in items]
        elif spec["type"] == "string":
            out[name] = _truncate(value, spec["max_chars"])
    return out


def _build_modules_block(module_keys: List[str]) -> str:
    lines: List[str] = []
    name_map = _module_name_map()
    for key in module_keys:
        fields = _schema_for_module(key)
        if not fields:
            continue
        field_lines = []
        for name, spec in fields.items():
            if spec["type"] == "array":
                field_lines.append(
                    f'  - {name}: {spec["description"]}'
                )
            else:
                field_lines.append(
                    f'  - {name}: {spec["description"]}'
                )
        lines.append(f"- {key}（{name_map.get(key, key)}）\n" + "\n".join(field_lines))
    return "\n\n".join(lines) or "（无模块）"


def _fallback_copy_for_module(module_key: str, product_name: str) -> Dict[str, Any]:
    """无 LLM 时的模板文案。"""
    name = product_name or "本产品"
    titles = _FALLBACK_TITLE_TEMPLATES.get(module_key, ["{name}"])
    title = titles[0].format(name=name)
    bullets = list(_FALLBACK_BULLETS.get(module_key, []))

    result: Dict[str, Any] = {"title": title}
    schema = _schema_for_module(module_key)

    # 根据模块类型填充可选字段
    if "subtitle" in schema:
        result["subtitle"] = f"专注细节，只为更好的{name}体验"
    if "bullets" in schema and bullets:
        max_items = schema["bullets"].get("max_items", 3)
        result["bullets"] = bullets[:max_items]
    if "badge" in schema:
        result["badge"] = "立即抢购" if module_key == "cta" else "新品上市"

    return _truncate_copy(module_key, result)


def _try_parse_json(text: str) -> Optional[Dict[str, Any]]:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    try:
        return json.loads(text)
    except Exception:
        m = re.search(r"\{[\s\S]*\}", text)
        if m:
            try:
                return json.loads(m.group(0))
            except Exception:
                return None
    return None


# ---------------------------------------------------------------- 对外接口
async def generate_module_copy(project) -> Dict[str, Any]:
    """为项目生成所有模块的结构化文案。

    返回：{ module_key: { title, subtitle, bullets, badge } }
    """
    module_keys = [m.get("key") for m in (project.module_plan or []) if m.get("key")]
    if not module_keys:
        return {}

    product_name = project.product_name or ""
    industry = project.industry or ""
    selling_points = project.product_selling_points or ""
    target_audience = project.product_target_audience or ""
    product_description = project.product_description or ""

    raw: Optional[Dict[str, Any]] = None
    if settings.has_text_llm:
        user_prompt = COPY_USER_TEMPLATE.format(
            product_name=product_name or "（未提供）",
            industry=industry or "通用",
            target_market=project.target_market or "通用",
            target_platform=project.target_platform or "通用",
            visual_style=project.visual_style or "通用",
            selling_points=selling_points or "（未提供）",
            target_audience=target_audience or "（未提供）",
            product_description=product_description or "（未提供）",
            extra=project.extra_requirements or "（无）",
            modules=_build_modules_block(module_keys),
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
                            {"role": "system", "content": COPY_SYSTEM},
                            {"role": "user", "content": user_prompt},
                        ],
                        "temperature": 0.75,
                        "response_format": {"type": "json_object"},
                    },
                )
                r.raise_for_status()
                data = r.json()
                raw = _try_parse_json(data["choices"][0]["message"]["content"])
        except Exception as e:
            logger.warning("模块文案 LLM 生成失败，使用模板回退: %s", e)
            raw = None

    if not raw:
        raw = {}

    # 组装 + 截断
    result: Dict[str, Any] = {}
    for key in module_keys:
        module_copy = raw.get(key) or {}
        if not isinstance(module_copy, dict):
            module_copy = {}
        # 如果 LLM 输出为空或缺少 title，混入模板兜底
        if not module_copy.get("title"):
            fallback = _fallback_copy_for_module(key, product_name)
            fallback.update({k: v for k, v in module_copy.items() if v})
            module_copy = fallback
        result[key] = _truncate_copy(key, module_copy)

    return result


def apply_module_copy(project, copy: Dict[str, Any]) -> None:
    """把生成好的文案写回 project 对象（不 commit）。"""
    project.module_copy = copy or {}
