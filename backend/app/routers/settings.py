"""/api/settings - 配置读写 + 连通性测试"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Any, Optional

from app.services import settings_service

router = APIRouter(prefix="/api/settings", tags=["settings"])


class SettingsPayload(BaseModel):
    image: Optional[dict[str, Any]] = None
    text: Optional[dict[str, Any]] = None


@router.get("")
def get_settings():
    """获取当前配置（API Key 已脱敏）。"""
    return settings_service.get_settings()


@router.put("")
def update_settings(payload: SettingsPayload):
    """更新配置到 .env，立即生效。"""
    try:
        return settings_service.update_settings(payload.model_dump(exclude_none=True))
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"保存失败: {e}")


@router.post("/test/{section}")
async def test_connection(section: str):
    """测试 image/text API 连通性。section: image | text

    image 测试用 GET /models（不消耗 credits）。
    """
    return await settings_service.test_connection(section)


@router.post("/test_generation")
async def test_generation():
    """深度测试：实际生成一张小图，验证完整生图链路。

    与 /test/image 不同，这个会真正调用生图 API（消耗少量 credits），
    但能确认渠道是否真的可用。
    """
    return await settings_service.test_generation()