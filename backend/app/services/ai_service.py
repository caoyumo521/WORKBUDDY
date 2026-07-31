"""AI 文本服务 - 用于详情页结构规划、卖点润色、文案生成。

三种模式：
1. TEXT_PROVIDER=openai  → 调用 OpenAI 兼容 LLM API 实时生成
2. TEXT_PROVIDER=workbuddy → 开发时用 WorkBuddy 预生成策略到 knowledge/，运行时加载
3. TEXT_PROVIDER=none     → 纯模板回退（离线开发测试）

设计原则：
- 不依赖具体 LLM，通过 OpenAI 兼容协议调用，便于未来切换
- 有知识库策略时优先使用策略中的 Prompt 模板和模块结构
- 无 LLM 时仍可运行（降级为模板模式）
"""
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx

from app.config import settings
from app.utils.prompts import (
    COMMON_MODULES,
    INDUSTRY_MODULE_PRESET,
    INDUSTRY_STYLE_HINT,
    VISUAL_STYLES,
)


SYSTEM_PLANNER = """你是一名资深的电商详情页策划专家，熟悉中国/美国/欧洲/日本/东南亚市场。
你的任务是根据产品信息和用户输入，输出详情页的模块规划与文案建议。
输出必须是严格的 JSON 格式，不要包含任何解释性文字。"""


PLANNER_USER_TEMPLATE = """请为以下产品规划详情页结构：

【产品信息】
- 产品名称: {product_name}
- 行业: {industry}
- 目标市场: {target_market}
- 目标平台: {target_platform}
- 目标语言: {language}
- 视觉风格: {visual_style}
- 核心卖点: {selling_points}
- 目标用户: {target_audience}
- 产品描述: {product_description}
- 附加要求: {extra}

【可选模块】
{modules}

【行业策略参考】
{industry_strategy}

【请输出 JSON】
{{
  "selling_points": "精炼后的3-5条核心卖点",
  "target_audience": "目标用户画像 1-2 句话",
  "visual_direction": "视觉方向建议 1-2 句话",
  "modules": [
    {{
      "key": "模块key",
      "name_zh": "模块中文名",
      "name_local": "模块在 {language} 市场下的本地化名称",
      "quantity": 1,
      "rationale": "为什么选这个模块"
    }}
  ]
}}
"""


def load_industry_strategy(industry: str) -> Optional[Dict[str, Any]]:
    """从知识库加载行业策略文件。

    返回 strategy.json 内容，或 None（如果不存在）。
    """
    strategy_path = settings.knowledge_root / industry / "strategy.json"
    if strategy_path.exists():
        try:
            return json.loads(strategy_path.read_text(encoding="utf-8"))
        except Exception:
            return None
    return None


def _format_strategy_for_prompt(strategy: Dict[str, Any]) -> str:
    """将行业策略格式化为 prompt 中的参考文本。"""
    lines = []
    structure = strategy.get("page_structure", {})
    if structure.get("module_order"):
        lines.append(f"推荐模块顺序: {', '.join(structure['module_order'])}")
    if structure.get("typical_length"):
        lines.append(f"典型模块数: {structure['typical_length']}")
    if structure.get("info_density"):
        lines.append(f"信息密度: {structure['info_density']}")

    photo = strategy.get("photography_style", {})
    if photo:
        lines.append(f"摄影风格: {json.dumps(photo, ensure_ascii=False)[:200]}")

    cw = strategy.get("copywriting", {})
    if cw:
        lines.append(f"文案风格: {json.dumps(cw, ensure_ascii=False)[:200]}")

    return "\n".join(lines) if lines else "(无策略文件)"


async def plan_detail_page(
    *,
    product_name: str,
    industry: str,
    target_market: str = "",
    target_platform: str = "",
    language: str = "zh-CN",
    visual_style: str = "",
    selling_points: str = "",
    target_audience: str = "",
    product_description: str = "",
    extra: str = "",
) -> Dict[str, Any]:
    """调用 LLM 规划详情页结构；失败时回退到知识库策略或行业默认模板。"""
    modules_text = "\n".join(
        f"- {m['key']} ({m['name_zh']}): {m['desc_zh']}" for m in COMMON_MODULES
    )

    # 尝试加载行业策略
    strategy = load_industry_strategy(industry)
    strategy_text = _format_strategy_for_prompt(strategy) if strategy else "(无)"

    user_prompt = PLANNER_USER_TEMPLATE.format(
        product_name=product_name or "(未提供)",
        industry=industry or "通用",
        target_market=target_market or "通用",
        target_platform=target_platform or "通用",
        language=language,
        visual_style=visual_style or "通用",
        selling_points=selling_points or "(未提供)",
        target_audience=target_audience or "(未提供)",
        product_description=product_description or "(未提供)",
        extra=extra or "(无)",
        modules=modules_text,
        industry_strategy=strategy_text,
    )

    raw_text: Optional[str] = None
    if settings.has_text_llm:
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                r = await client.post(
                    f"{settings.text_base_url.rstrip('/')}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {settings.text_api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": settings.text_model,
                        "messages": [
                            {"role": "system", "content": SYSTEM_PLANNER},
                            {"role": "user", "content": user_prompt},
                        ],
                        "temperature": 0.6,
                        "response_format": {"type": "json_object"},
                    },
                )
                r.raise_for_status()
                data = r.json()
                raw_text = data["choices"][0]["message"]["content"]
        except Exception:
            raw_text = None

    if raw_text:
        parsed = _try_parse_json(raw_text)
        if parsed and "modules" in parsed:
            return parsed

    # 回退：优先使用知识库策略，其次使用代码内置模板
    return _fallback_plan(industry, language, strategy)


def _try_parse_json(text: str) -> Optional[Dict[str, Any]]:
    text = text.strip()
    # 去除代码块围栏
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    try:
        return json.loads(text)
    except Exception:
        # 提取首个 JSON 块
        m = re.search(r"\{[\s\S]*\}", text)
        if m:
            try:
                return json.loads(m.group(0))
            except Exception:
                return None
    return None


def _fallback_plan(
    industry: str,
    language: str,
    strategy: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """回退方案：优先使用知识库策略，其次使用代码内置模板。"""
    # 1. 尝试从知识库策略获取模块顺序
    if strategy:
        structure = strategy.get("page_structure", {})
        keys = structure.get("module_order", [])
        # 过滤掉不在 COMMON_MODULES 中的 key
        valid_keys = [k for k in keys if any(m["key"] == k for m in COMMON_MODULES)]
        if not valid_keys:
            keys = INDUSTRY_MODULE_PRESET.get(industry, ["hero", "core_selling", "detail", "scenario", "spec_param", "after_sales", "cta"])
        else:
            keys = valid_keys

        # 从策略获取文案建议
        cw = strategy.get("copywriting", {})
        market = strategy.get("market_adaptation", {}).get(language, {})
        selling_points = cw.get("selling_point_style", "AI 暂未连接，请手动填写。")
        if market.get("tone"):
            selling_points = f"{market['tone']}，{cw.get('selling_point_style', '')}"

        target_audience = "通用消费者"
        if market.get("tone"):
            target_audience = f"符合{market['tone']}定位的目标用户"

        visual_direction = strategy.get("photography_style", {}).get("lighting", "")
        if visual_direction:
            visual_direction = f"{visual_direction}, {strategy.get('photography_style', {}).get('background', '')}"
        else:
            visual_direction = INDUSTRY_STYLE_HINT.get(industry, "clean, professional product photography")
    else:
        # 2. 使用代码内置模板
        keys = INDUSTRY_MODULE_PRESET.get(industry, ["hero", "core_selling", "detail", "scenario", "spec_param", "after_sales", "cta"])
        selling_points = "AI 暂未连接，请手动填写。"
        target_audience = "通用消费者"
        visual_direction = INDUSTRY_STYLE_HINT.get(industry, "clean, professional product photography")

    name_map = {m["key"]: m["name_zh"] for m in COMMON_MODULES}
    modules = []
    for k in keys:
        modules.append({
            "key": k,
            "name_zh": name_map.get(k, k),
            "name_local": name_map.get(k, k),
            "quantity": 1,
            "rationale": "行业策略推荐" if strategy else "行业默认模板",
        })
    return {
        "selling_points": selling_points,
        "target_audience": target_audience,
        "visual_direction": visual_direction,
        "modules": modules,
    }


async def ai_help_requirements(payload: Dict[str, Any]) -> Dict[str, Any]:
    """AI 帮写：根据已填信息自动补全卖点/用户/视觉建议/推荐模块。"""
    plan = await plan_detail_page(
        product_name=payload.get("product_name", ""),
        industry=payload.get("industry", ""),
        target_market=payload.get("target_market", ""),
        target_platform=payload.get("target_platform", ""),
        language=payload.get("language", "zh-CN"),
        visual_style=payload.get("visual_style", ""),
        selling_points=payload.get("product_selling_points", ""),
        target_audience=payload.get("product_target_audience", ""),
        product_description=payload.get("product_description", ""),
        extra=payload.get("extra_requirements", ""),
    )
    return {
        "selling_points": plan.get("selling_points", ""),
        "target_audience": plan.get("target_audience", ""),
        "visual_direction": plan.get("visual_direction", ""),
        "suggested_modules": [m["key"] for m in plan.get("modules", [])],
    }


def get_prompt_template(industry: str, module_key: str) -> Optional[str]:
    """从知识库获取指定行业+模块的 Prompt 模板。

    返回模板字符串（含 {product_name} 等占位符），或 None。
    """
    strategy = load_industry_strategy(industry)
    if not strategy:
        return None
    templates = strategy.get("prompt_templates", {})
    return templates.get(module_key)
