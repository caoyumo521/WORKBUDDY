"""配置读写服务。

支持：
1. 把当前生效的配置脱敏返回给前端
2. 把前端提交的表单写回 .env
3. 不重启即可生效（因为 Settings 是单例 lazy reload，下次请求自然重读）

注意：
- API Key 不会原样返回，只返回前 4 位 + "***" + 后 4 位
- 写入 .env 时保持 KEY=VALUE 格式，使用 UTF-8
- 已有字段覆盖，未在白名单的字段不写入
"""
from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Dict, List

from app.config import BACKEND_DIR, settings

ENV_PATH = BACKEND_DIR / ".env"

# 前端可读写白名单（避免误改其他字段）
WRITABLE_KEYS: List[str] = [
    # 生图 API
    "image_provider",
    "image_api_key",
    "image_base_url",
    "image_model",
    "image_quality",
    "image_output_format",
    "image_background",
    # 文案/思考 API
    "text_provider",
    "text_api_key",
    "text_base_url",
    "text_model",
]


def _mask(value: str) -> str:
    """脱敏 API Key。空值返回空串。"""
    if not value:
        return ""
    if len(value) <= 8:
        return "***"
    return f"{value[:4]}***{value[-4:]}"


def get_settings() -> Dict:
    """返回当前生效配置 + 脱敏后的 API Key。"""
    s = settings
    return {
        "image": {
            "provider": s.image_provider,
            "base_url": s.image_base_url,
            "model": s.image_model,
            "api_key_masked": _mask(s.image_api_key),
            "has_api_key": bool(s.image_api_key),
            "quality": s.image_quality,
            "output_format": s.image_output_format,
            "background": s.image_background,
            "providers": ["openai", "flux", "custom", "mock"],
            "output_formats": ["png", "jpeg", "webp"],
            "qualities": ["low", "medium", "high", "auto"],
            "backgrounds": ["transparent", "opaque", "auto"],
        },
        "text": {
            "provider": s.text_provider,
            "base_url": s.text_base_url,
            "model": s.text_model,
            "api_key_masked": _mask(s.text_api_key),
            "has_api_key": bool(s.text_api_key),
            "providers": ["openai", "workbuddy", "none"],
        },
        "app": {
            "host": s.app_host,
            "port": s.app_port,
            "debug": s.app_debug,
            "cors_origins": s.cors_origins,
        },
        "storage": {
            "projects_root": str(s.projects_root),
            "knowledge_root": str(s.knowledge_root),
        },
    }


def update_settings(payload: Dict) -> Dict:
    """把前端提交的表单写回 .env，返回更新后的配置。

    约定：
    - payload["image"]["api_key"]: 若前端传 "__KEEP__" 表示不变
    - payload["image"]["api_key"]: 若前端传 "__CLEAR__" 表示清空
    - 其他字段为空字符串则不变
    """
    if not ENV_PATH.exists():
        # 第一次：拷贝 .env.example
        example = BACKEND_DIR / ".env.example"
        if example.exists():
            ENV_PATH.write_text(example.read_text(encoding="utf-8"), encoding="utf-8")
        else:
            ENV_PATH.write_text("", encoding="utf-8")

    text = ENV_PATH.read_text(encoding="utf-8")
    sections = {"image": [], "text": []}

    img = payload.get("image") or {}
    txt = payload.get("text") or {}

    # 组装要写入的 key=value
    updates: Dict[str, str] = {}

    # image
    if "provider" in img and img["provider"]:
        updates["IMAGE_PROVIDER"] = img["provider"]
    if "base_url" in img and img["base_url"]:
        updates["IMAGE_BASE_URL"] = img["base_url"]
    if "model" in img and img["model"]:
        updates["IMAGE_MODEL"] = img["model"]
    if "api_key" in img:
        if img["api_key"] == "__KEEP__":
            pass
        elif img["api_key"] == "__CLEAR__":
            updates["IMAGE_API_KEY"] = ""
        elif img["api_key"]:
            updates["IMAGE_API_KEY"] = img["api_key"]
    if "quality" in img and img["quality"]:
        updates["IMAGE_QUALITY"] = img["quality"]
    if "output_format" in img and img["output_format"]:
        updates["IMAGE_OUTPUT_FORMAT"] = img["output_format"]
    if "background" in img and img["background"]:
        updates["IMAGE_BACKGROUND"] = img["background"]

    # text
    if "provider" in txt and txt["provider"]:
        updates["TEXT_PROVIDER"] = txt["provider"]
    if "base_url" in txt and txt["base_url"]:
        updates["TEXT_BASE_URL"] = txt["base_url"]
    if "model" in txt and txt["model"]:
        updates["TEXT_MODEL"] = txt["model"]
    if "api_key" in txt:
        if txt["api_key"] == "__KEEP__":
            pass
        elif txt["api_key"] == "__CLEAR__":
            updates["TEXT_API_KEY"] = ""
        elif txt["api_key"]:
            updates["TEXT_API_KEY"] = txt["api_key"]

    # 写入/更新 .env
    new_lines = []
    written = set()
    # 先把 updates 拷贝一份（避免 .pop() 破坏后续 __dict__ 更新）
    all_updates = dict(updates)
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            new_lines.append(line)
            continue
        m = re.match(r"^([A-Z0-9_]+)\s*=", line)
        if m and m.group(1) in updates:
            new_lines.append(f"{m.group(1)}={updates.pop(m.group(1))}")
            written.add(m.group(1))
        else:
            new_lines.append(line)

    # 追加新的
    for k, v in updates.items():
        new_lines.append(f"{k}={v}")

    ENV_PATH.write_text("\n".join(new_lines) + "\n", encoding="utf-8")

    # 立即更新内存里的 settings（不需要重启）。
    # pydantic-settings v2 用 model_config 缓存了字段值，所以用 __dict__ 直接覆盖
    # 同时更新 os.environ 保证后续 reload 也能拿到新值
    # 用 all_updates 包含所有字段（无论是修改还是新增的）
    for k, v in all_updates.items():
        os.environ[k] = v
        k_lower = k.lower()
        if hasattr(settings, k_lower):
            try:
                settings.__dict__[k_lower] = v
            except Exception:
                try:
                    setattr(settings, k_lower, v)
                except Exception:
                    pass

    return get_settings()


async def test_connection(section: str) -> Dict:
    """测试某个 API 是否连通。

    section: 'image' | 'text'
    返回 {ok: bool, message: str, latency_ms?: int}

    image 测试用 /models 端点（不实际生图，避免浪费 credits），
    并检查用户配置的 model 是否在可用列表中。
    text 测试用 /chat/completions 发一条最小请求。
    """
    import time
    import httpx

    if section == "image":
        base = settings.image_base_url
        key = settings.image_api_key
        model = settings.image_model or "gpt-image-2"
        url = base.rstrip("/") + "/models"
    elif section == "text":
        base = settings.text_base_url
        key = settings.text_api_key
        body = {
            "model": settings.text_model or "gpt-4o-mini",
            "messages": [{"role": "user", "content": "ping"}],
            "max_tokens": 5,
        }
        url = base.rstrip("/") + "/chat/completions"
    else:
        return {"ok": False, "message": f"unknown section: {section}"}

    if not key:
        return {"ok": False, "message": "API Key 未配置"}

    t0 = time.time()
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            if section == "image":
                # 用 GET /models 测试连通性 + 检查模型可用性
                r = await client.get(
                    url,
                    headers={"Authorization": f"Bearer {key}"},
                )
                latency = int((time.time() - t0) * 1000)
                if r.status_code in (200, 201):
                    # 检查 model 是否在可用列表中
                    try:
                        data = r.json()
                        available = [m.get("id", "") for m in data.get("data", [])]
                        if available and model not in available:
                            return {
                                "ok": False,
                                "message": f"连通成功，但模型 '{model}' 不在可用列表中。可用模型：{', '.join(available[:10])}",
                                "latency_ms": latency,
                            }
                    except Exception:
                        pass  # 无法解析模型列表，只报连通成功
                    return {"ok": True, "message": f"连通成功，模型 {model} 可用", "latency_ms": latency}
                return {
                    "ok": False,
                    "message": f"HTTP {r.status_code}: {r.text[:200]}",
                    "latency_ms": latency,
                }
            else:
                r = await client.post(
                    url,
                    json=body,
                    headers={"Authorization": f"Bearer {key}"},
                )
                latency = int((time.time() - t0) * 1000)
                if r.status_code in (200, 201):
                    return {"ok": True, "message": f"连通成功", "latency_ms": latency}
                return {
                    "ok": False,
                    "message": f"HTTP {r.status_code}: {r.text[:200]}",
                    "latency_ms": latency,
                }
    except Exception as e:
        return {"ok": False, "message": f"连接失败：{e}"}


async def test_generation() -> Dict:
    """深度测试：实际生成一张小图，验证完整生图链路。

    与 test_connection('image') 不同，这个会真正调用生图 API。
    如果成功，返回测试图片的 base64 缩略图。
    如果失败，返回上游的详细错误信息。
    """
    import asyncio
    import time
    from app.services.image_service import get_image_provider
    from app.services.image_providers.openai_provider import ImageAPIError

    if not settings.image_api_key:
        return {"ok": False, "message": "API Key 未配置"}

    provider = get_image_provider()
    t0 = time.time()

    try:
        result = await provider.generate(
            prompt="a simple red circle on white background, minimal, product photography",
            width=1024,
            height=1024,
            extra={
                "resolution": "1K",
                "output_format": "png",
                "quality": "low",
                "background": "opaque",
            },
        )
        latency = int((time.time() - t0) * 1000)

        b64 = result.get("b64", "")
        url = result.get("url", "")

        if not b64 and not url:
            return {
                "ok": False,
                "message": "API 返回成功，但结果中没有图片数据（无 b64 也无 url）",
                "latency_ms": latency,
            }

        return {
            "ok": True,
            "message": f"生图成功！模型: {result.get('model', settings.image_model)}, 尺寸: {result.get('width', '?')}×{result.get('height', '?')}",
            "latency_ms": latency,
            "has_preview": bool(b64),
        }

    except ImageAPIError as e:
        latency = int((time.time() - t0) * 1000)
        return {
            "ok": False,
            "message": f"生图失败（HTTP {e.status_code}）: {e.args[0]}",
            "latency_ms": latency,
        }
    except Exception as e:
        latency = int((time.time() - t0) * 1000)
        return {
            "ok": False,
            "message": f"生图失败: {e}",
            "latency_ms": latency,
        }