"""/api/meta - 静态字典（行业/平台/语言/比例/视觉风格/模块）"""
from fastapi import APIRouter

from app.utils.prompts import (
    ASPECT_RATIOS,
    COMMON_MODULES,
    INDUSTRIES,
    INDUSTRY_MODULE_PRESET,
    LANGUAGES,
    PLATFORMS,
    VISUAL_STYLES,
)

router = APIRouter(prefix="/api/meta", tags=["meta"])


@router.get("/industries")
def industries():
    return INDUSTRIES


@router.get("/platforms")
def platforms():
    return PLATFORMS


@router.get("/languages")
def languages():
    return LANGUAGES


@router.get("/aspect-ratios")
def aspect_ratios():
    return ASPECT_RATIOS


@router.get("/visual-styles")
def visual_styles():
    return VISUAL_STYLES


@router.get("/modules")
def modules():
    return COMMON_MODULES


@router.get("/industry-preset/{industry_key}")
def industry_preset(industry_key: str):
    return {"modules": INDUSTRY_MODULE_PRESET.get(industry_key, [])}
