"""Pydantic Schemas - API 进出数据契约。"""
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ---------- Project ----------
class ProjectBase(BaseModel):
    name: str
    industry: str = ""
    target_market: str = ""
    target_platform: str = ""
    language: str = "zh-CN"
    visual_style: str = ""
    resolution: str = "2K"
    aspect_ratio: str = "3:4"
    product_name: str = ""
    product_selling_points: Optional[str] = ""
    product_target_audience: str = ""
    product_description: Optional[str] = ""
    extra_requirements: Optional[str] = ""
    module_plan: List[Dict[str, Any]] = Field(default_factory=list)


class ProjectCreate(ProjectBase):
    id: Optional[str] = None


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    industry: Optional[str] = None
    target_market: Optional[str] = None
    target_platform: Optional[str] = None
    language: Optional[str] = None
    visual_style: Optional[str] = None
    resolution: Optional[str] = None
    aspect_ratio: Optional[str] = None
    product_name: Optional[str] = None
    product_selling_points: Optional[str] = None
    product_target_audience: Optional[str] = None
    product_description: Optional[str] = None
    extra_requirements: Optional[str] = None
    module_plan: Optional[List[Dict[str, Any]]] = None
    status: Optional[str] = None


class ProjectOut(ProjectBase):
    id: str
    workdir: str = ""
    status: str = "draft"
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ---------- Asset ----------
class AssetOut(BaseModel):
    id: int
    project_id: str
    asset_type: str
    module_key: str
    seq: int
    language: str
    file_path: str
    url: str
    thumbnail_url: str = ""
    width: int
    height: int
    file_size: int
    prompt: Optional[str] = ""
    negative_prompt: Optional[str] = ""
    model: str = ""
    resolution: str = ""
    status: str
    error_message: Optional[str] = ""
    created_at: datetime

    class Config:
        from_attributes = True


# ---------- Generation Task ----------
class GenerationTaskOut(BaseModel):
    id: int
    project_id: str
    module_key: str
    language: str
    status: str
    progress: int
    message: Optional[str] = ""
    asset_id: Optional[int] = None
    prompt: Optional[str] = ""
    model: str = ""
    resolution: str = ""
    aspect_ratio: str = ""
    created_at: datetime
    finished_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class GenerateRequest(BaseModel):
    module_keys: Optional[List[str]] = None  # 为空则全量重生成
    language: Optional[str] = None
    resolution: Optional[str] = None
    aspect_ratio: Optional[str] = None


# ---------- Wizard ----------
class DraftPayload(BaseModel):
    """快速创建草稿项目（不上传图片、不做 AI 规划）"""
    name: str
    industry: str = ""
    target_market: str = ""
    target_platform: str = ""
    language: str = "zh-CN"
    visual_style: str = ""
    resolution: str = "2K"
    aspect_ratio: str = "3:4"
    product_name: str = ""
    product_selling_points: str = ""
    product_target_audience: str = ""
    product_description: str = ""
    extra_requirements: str = ""


class WizardPayload(BaseModel):
    """创建项目向导最终提交的数据"""
    name: str
    industry: str
    target_market: str = ""
    target_platform: str = ""
    language: str = "zh-CN"
    visual_style: str = ""
    resolution: str = "2K"
    aspect_ratio: str = "3:4"
    product_name: str = ""
    product_selling_points: str = ""
    product_target_audience: str = ""
    product_description: str = ""
    extra_requirements: str = ""
    module_keys: List[str] = Field(default_factory=list)
    module_quantities: Dict[str, int] = Field(default_factory=dict)


class AIHelpRequest(BaseModel):
    product_name: str = ""
    product_selling_points: str = ""
    product_target_audience: str = ""
    industry: str = ""
    target_market: str = ""
    visual_style: str = ""
    language: str = "zh-CN"


class AIHelpResponse(BaseModel):
    selling_points: str
    target_audience: str
    visual_direction: str
    suggested_modules: List[str]
