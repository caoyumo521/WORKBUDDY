"""/api/projects - 项目 CRUD"""
from typing import List

import base64
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.project import ProjectCreate, ProjectOut, ProjectUpdate, WizardPayload
from app.services import project_service
from app.services.ai_service import analyze_product_image, plan_detail_page

router = APIRouter(prefix="/api/projects", tags=["projects"])


@router.get("", response_model=List[ProjectOut])
def list_projects(db: Session = Depends(get_db)):
    return project_service.list_projects(db)


@router.post("", response_model=ProjectOut)
def create_project(payload: ProjectCreate, db: Session = Depends(get_db)):
    return project_service.create_project(db, payload)


@router.post("/from-wizard", response_model=ProjectOut)
async def create_project_from_wizard(payload: WizardPayload, db: Session = Depends(get_db)):
    """从创建向导直接提交：先调用 AI 规划，再用结果建项目。"""
    plan = await plan_detail_page(
        product_name=payload.product_name,
        industry=payload.industry,
        target_market=payload.target_market,
        target_platform=payload.target_platform,
        language=payload.language,
        visual_style=payload.visual_style,
        selling_points=payload.product_selling_points,
        target_audience=payload.product_target_audience,
        product_description=payload.product_description,
        extra=payload.extra_requirements,
    )

    # 用户自选模块优先；没填再用 AI 推荐
    chosen_keys = payload.module_keys or [m["key"] for m in plan.get("modules", [])]
    name_map = {m["key"]: m["name_zh"] for m in plan.get("modules", [])}
    module_plan = []
    for k in chosen_keys:
        qty = int(payload.module_quantities.get(k) or 1)
        module_plan.append({
            "key": k,
            "name_zh": name_map.get(k, k),
            "quantity": max(1, qty),
        })

    selling_points = payload.product_selling_points or plan.get("selling_points", "")
    target_audience = payload.product_target_audience or plan.get("target_audience", "")
    visual_direction = plan.get("visual_direction", "")

    project_in = ProjectCreate(
        name=payload.name,
        industry=payload.industry,
        target_market=payload.target_market,
        target_platform=payload.target_platform,
        language=payload.language,
        visual_style=payload.visual_style,
        resolution=payload.resolution,
        aspect_ratio=payload.aspect_ratio,
        product_name=payload.product_name,
        product_selling_points=selling_points,
        product_target_audience=target_audience,
        product_description=payload.product_description,
        extra_requirements=(payload.extra_requirements or "") + "\n[AI 视觉方向] " + visual_direction,
        module_plan=module_plan,
    )
    return project_service.create_project(db, project_in)


@router.get("/{project_id}", response_model=ProjectOut)
def get_project(project_id: str, db: Session = Depends(get_db)):
    project = project_service.get_project(db, project_id)
    if not project:
        raise HTTPException(404, "Project not found")
    return project


@router.patch("/{project_id}", response_model=ProjectOut)
def update_project(project_id: str, payload: ProjectUpdate, db: Session = Depends(get_db)):
    project = project_service.get_project(db, project_id)
    if not project:
        raise HTTPException(404, "Project not found")
    return project_service.update_project(db, project, payload)


@router.delete("/{project_id}")
def delete_project(project_id: str, db: Session = Depends(get_db)):
    project = project_service.get_project(db, project_id)
    if not project:
        raise HTTPException(404, "Project not found")
    project_service.delete_project(db, project)
    return {"ok": True}


@router.post("/analyze-image")
async def analyze_image(
    file: UploadFile = File(...),
    product_name: str = Form(""),
    industry: str = Form(""),
    language: str = Form("zh-CN"),
    visual_style: str = Form(""),
):
    """上传一张产品图，用视觉 LLM 提炼卖点/特点/描述，返回结构化结果（前端可编辑后保存）。

    上下文（产品名/行业/语言/风格）作为表单字段传入，使该接口既可在详情页（已有项目）
    使用，也可在新建向导（项目尚未创建）阶段使用。
    """
    data = await file.read()
    if not data:
        raise HTTPException(400, "空文件")
    if len(data) > 10 * 1024 * 1024:
        raise HTTPException(400, "图片过大（>10MB），请压缩后再上传")

    ext = (file.filename or "image.png").rsplit(".", 1)[-1].lower()
    mime = (
        "image/png" if ext == "png"
        else "image/webp" if ext == "webp"
        else "image/jpeg"
    )
    b64 = base64.b64encode(data).decode("ascii")
    image_b64 = f"data:{mime};base64,{b64}"

    result = await analyze_product_image(
        image_b64=image_b64,
        product_name=product_name,
        industry=industry,
        language=language,
        visual_style=visual_style,
    )
    return result


@router.get("/{project_id}/preview-sources")
def preview_sources(project_id: str, db: Session = Depends(get_db)):
    """返回按 module_plan 顺序排列的所有生成图信息，前端用来渲染组合预览面板。

    返回结构：
    {
      "project": {...},
      "modules": [
        {
          "key": "hero",
          "name_zh": "首屏",
          "quantity": 1,
          "images": [
            {"id": 1, "url": "/api/files?path=...", "width": 1024, "height": 1024, ...}
          ]
        }
      ],
      "combined_url": "/api/files/preview/{project_id}?format=png"
    }
    """
    from app.models.asset import Asset

    project = project_service.get_project(db, project_id)
    if not project:
        raise HTTPException(404, "Project not found")

    assets = (
        db.query(Asset)
        .filter(Asset.project_id == project_id, Asset.asset_type == "generated")
        .order_by(Asset.module_key, Asset.seq, Asset.id)
        .all()
    )

    by_module: dict = {m["key"]: [] for m in project.module_plan}
    for a in assets:
        if a.module_key not in by_module:
            by_module[a.module_key] = []
        by_module[a.module_key].append(
            {
                "id": a.id,
                "url": f"/api/files?path={a.file_path}",
                "png_url": f"/api/files?path={a.file_path}",
                "jpg_url": f"/api/files?path={a.file_path}&format=jpeg",
                "webp_url": f"/api/files?path={a.file_path}&format=webp",
                "width": a.width,
                "height": a.height,
                "model": a.model,
                "resolution": a.resolution,
            }
        )

    modules = []
    for m in project.module_plan:
        modules.append(
            {
                "key": m["key"],
                "name_zh": m["name_zh"],
                "quantity": m.get("quantity", 1),
                "images": by_module.get(m["key"], []),
            }
        )

    return {
        "project": {
            "id": project.id,
            "name": project.name,
            "industry": project.industry,
            "language": project.language,
        },
        "modules": modules,
        "combined_url": f"/api/files/preview/{project_id}",
    }
