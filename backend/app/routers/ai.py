"""/api/ai - AI 帮写相关接口"""
from fastapi import APIRouter

from app.schemas.project import AIHelpRequest, AIHelpResponse
from app.services.ai_service import ai_help_requirements

router = APIRouter(prefix="/api/ai", tags=["ai"])


@router.post("/help", response_model=AIHelpResponse)
async def ai_help(payload: AIHelpRequest):
    return await ai_help_requirements(payload.model_dump())
