"""/api/generation - 详情页生成、查询、重试"""
import asyncio
import base64
import shutil
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import httpx
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.asset import Asset
from app.models.generation import GenerationTask
from app.models.project import Project
from app.schemas.project import GenerateRequest
from app.services.image_service import get_image_provider, resolution_to_size
from app.utils.file_manager import (
    DIR_PROMPTS,
    module_dir,
    timestamp_str,
)
from app.utils.prompts import COMMON_MODULES, VISUAL_STYLES, build_design_guide_block, build_module_prompt, build_style_lock

router = APIRouter(prefix="/api/generation", tags=["generation"])


@router.post("/project/{project_id}/run")
async def run_generation(
    project_id: str,
    req: GenerateRequest,
    background: BackgroundTasks,
    db: Session = Depends(get_db),
):
    project: Project | None = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, "Project not found")

    module_keys = req.module_keys
    if not module_keys:
        module_keys = [m.get("key") for m in (project.module_plan or []) if m.get("key")]
    if not module_keys:
        raise HTTPException(400, "项目尚未规划模块")

    language = req.language or project.language
    resolution = req.resolution or project.resolution
    aspect_ratio = req.aspect_ratio or project.aspect_ratio

    # 创建任务记录
    task_ids: List[int] = []
    plan_index = {m.get("key"): m for m in (project.module_plan or [])}
    for k in module_keys:
        qty = int(plan_index.get(k, {}).get("quantity", 1) or 1)
        for seq in range(1, qty + 1):
            task = GenerationTask(
                project_id=project.id,
                module_key=k,
                language=language,
                status="pending",
                progress=0,
                resolution=resolution,
                aspect_ratio=aspect_ratio,
            )
            db.add(task)
            db.flush()
            task_ids.append(task.id)
    db.commit()

    # 异步执行
    background.add_task(
        _run_all_tasks,
        project_id=project.id,
        task_ids=task_ids,
        language=language,
        resolution=resolution,
        aspect_ratio=aspect_ratio,
    )

    return {"queued": len(task_ids), "task_ids": task_ids}


@router.get("/project/{project_id}/tasks")
def list_tasks(project_id: str, db: Session = Depends(get_db)):
    tasks = (
        db.query(GenerationTask)
        .filter(GenerationTask.project_id == project_id)
        .order_by(GenerationTask.id.desc())
        .all()
    )
    return tasks


@router.get("/task/{task_id}")
def get_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(GenerationTask).filter(GenerationTask.id == task_id).first()
    if not task:
        raise HTTPException(404, "Task not found")
    return task


@router.post("/task/{task_id}/retry")
def retry_task(task_id: int, background: BackgroundTasks, db: Session = Depends(get_db)):
    task = db.query(GenerationTask).filter(GenerationTask.id == task_id).first()
    if not task:
        raise HTTPException(404, "Task not found")
    task.status = "pending"
    task.progress = 0
    task.message = ""
    db.commit()
    project = db.query(Project).filter(Project.id == task.project_id).first()
    background.add_task(
        _run_all_tasks,
        project_id=project.id,
        task_ids=[task.id],
        language=task.language,
        resolution=task.resolution,
        aspect_ratio=task.aspect_ratio,
    )
    return {"ok": True, "task_id": task.id}


# ---------------- 内部执行逻辑 ----------------

def _run_all_tasks(project_id: str, task_ids: List[int], language: str, resolution: str, aspect_ratio: str):
    """同步执行所有任务（在 BackgroundTasks 中跑在线程池）。"""
    from app.database import SessionLocal

    db = SessionLocal()
    try:
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return

        provider = get_image_provider()
        width, height = resolution_to_size(resolution, aspect_ratio)

        # 视觉调性锁定：同一项目所有模块共用【同一份】，保证整页调性统一
        style_lock = build_style_lock(project.visual_style or "", project.industry or "")

        for tid in task_ids:
            task = db.query(GenerationTask).filter(GenerationTask.id == tid).first()
            if not task:
                continue
            try:
                _do_one_task(db, project, task, provider, language, resolution, aspect_ratio, width, height, style_lock)
            except Exception as e:
                task.status = "failed"
                # 提取上游 API 的实际错误信息，避免只显示 "Server error '500'"
                err_msg = str(e)
                # ImageAPIError 已经包含上游 message，直接用
                task.message = f"生图失败：{err_msg}"
                task.finished_at = datetime.utcnow()
                db.commit()
    finally:
        db.close()


def _do_one_task(db, project: Project, task: GenerationTask, provider, language: str, resolution: str, aspect_ratio: str, width: int, height: int, style_lock: str = ""):
    task.status = "running"
    task.progress = 10
    task.message = "构造 Prompt"
    db.commit()

    module_name = next(
        (m["name_zh"] for m in COMMON_MODULES if m["key"] == task.module_key),
        task.module_key,
    )
    extra = project.extra_requirements or ""

    # 优先使用知识库 Prompt 模板，回退到通用模板
    from app.services.ai_service import get_prompt_template
    template = get_prompt_template(project.industry, task.module_key)
    if template:
        try:
            style_name = ""
            for v in VISUAL_STYLES:
                if v["key"] == (project.visual_style or ""):
                    style_name = v["name_zh"]
                    break
            prompt = template.format(
                product_name=project.product_name or "",
                visual_style=style_name or project.visual_style or "professional",
                language=language,
                scenario_location="modern lifestyle setting",
                color="neutral",
                brand_color="#333333",
                unit="cm" if language.startswith("zh") else "inches",
                pet_type="pet",
            )
            # 即使走了知识库模板，也要追加：产品描述、卖点、设计感约束、调性锁定
            # 避免旧模板只出“模特穿着图”或“白底产品图”
            additions = []
            if project.product_description:
                additions.append(f"Product description: {project.product_description}")
            if project.product_selling_points:
                additions.append(f"Key selling points to feature in the image: {project.product_selling_points}")
            design_guide = build_design_guide_block(task.module_key)
            if design_guide:
                additions.append(design_guide)
            if additions:
                prompt = (prompt.rstrip(". \n") + ". " + " ".join(additions)).strip()
        except (KeyError, IndexError):
            prompt = build_module_prompt(
                module_key=task.module_key,
                product_name=project.product_name,
                industry=project.industry,
                language=language,
                visual_style=project.visual_style,
                extra=extra,
                product_description=project.product_description or "",
                product_selling_points=project.product_selling_points or "",
            )
    else:
        prompt = build_module_prompt(
            module_key=task.module_key,
            product_name=project.product_name,
            industry=project.industry,
            language=language,
            visual_style=project.visual_style,
            extra=extra,
            product_description=project.product_description or "",
            product_selling_points=project.product_selling_points or "",
        )
    # 注入「视觉调性锁定」：所有模块共用同一份，保证整页调性统一
    if style_lock:
        prompt = (prompt.rstrip(". \n") + ". " + style_lock).strip()

    task.prompt = prompt
    task.model = getattr(provider, "model", "") or provider.name
    db.commit()

    # 落盘 prompt
    prompt_dir = Path(project.workdir) / DIR_PROMPTS
    prompt_dir.mkdir(parents=True, exist_ok=True)
    (prompt_dir / f"{task.module_key}_{task.language}_{timestamp_str()}.txt").write_text(prompt, encoding="utf-8")

    # 收集参考图：风格参考图（锚定统一调性，优先级最高）→ 产品原图
    reference_images = []
    style_ref_assets = (
        db.query(Asset)
        .filter(Asset.project_id == project.id, Asset.asset_type == "style_reference")
        .order_by(Asset.id.asc())
        .all()
    )
    for a in style_ref_assets:
        p = Path(a.file_path)
        if p.exists():
            ext = p.suffix.lower()
            mime = "image/png" if ext == ".png" else "image/jpeg"
            b64 = base64.b64encode(p.read_bytes()).decode("ascii")
            reference_images.append(f"data:{mime};base64,{b64}")

    product_assets = (
        db.query(Asset)
        .filter(Asset.project_id == project.id, Asset.asset_type == "product_image")
        .order_by(Asset.id.asc())
        .limit(2)
        .all()
    )
    for a in product_assets:
        p = Path(a.file_path)
        if p.exists():
            ext = p.suffix.lower()
            mime = "image/png" if ext == ".png" else "image/jpeg"
            b64 = base64.b64encode(p.read_bytes()).decode("ascii")
            reference_images.append(f"data:{mime};base64,{b64}")

    # 调生图
    task.progress = 30
    task.message = "调用生图 API"
    db.commit()

    result = asyncio.run(
        provider.generate(
            prompt=prompt,
            width=width,
            height=height,
            reference_images=reference_images or None,
            extra={
                "resolution": resolution,
                "output_format": settings.image_output_format,
                "quality": settings.image_quality,
                "background": settings.image_background,
            },
        )
    )

    # 落盘
    task.progress = 70
    task.message = "保存图片"
    db.commit()

    dest_dir = module_dir(project.workdir, task.module_key)
    dest_dir.mkdir(parents=True, exist_ok=True)

    # 同模块下用 seq 自增
    existing = (
        db.query(Asset)
        .filter(Asset.project_id == project.id, Asset.module_key == task.module_key, Asset.asset_type == "generated")
        .count()
    )
    seq = existing + 1
    file_name = f"{task.module_key}_{language}_{timestamp_str()}_v{seq}.png"
    dest_path = dest_dir / file_name

    if result.get("b64"):
        dest_path.write_bytes(base64.b64decode(result["b64"]))
    elif result.get("url"):
        # 下载到本地
        with httpx.Client(timeout=120) as client:
            r = client.get(result["url"])
            r.raise_for_status()
            dest_path.write_bytes(r.content)
    else:
        raise RuntimeError("生图结果既无 url 也无 b64")

    # 写 Asset
    asset = Asset(
        project_id=project.id,
        asset_type="generated",
        module_key=task.module_key,
        seq=seq,
        language=language,
        file_path=str(dest_path),
        url=f"/api/files?path={dest_path}",
        thumbnail_url=f"/api/files?path={dest_path}",
        width=result.get("width", width),
        height=result.get("height", height),
        file_size=dest_path.stat().st_size,
        prompt=prompt,
        model=result.get("model", task.model),
        resolution=resolution,
        status="success",
    )
    db.add(asset)
    db.flush()
    task.asset_id = asset.id
    task.status = "success"
    task.progress = 100
    task.message = "完成"
    task.finished_at = datetime.utcnow()
    db.commit()

    # 异步刷新组合预览缓存（不阻塞当前任务）
    try:
        from app.services import preview_cache
        workdir = project.workdir
        if workdir:
            preview_cache.schedule_refresh(workdir)
    except Exception:
        pass  # 缓存刷新失败不影响生成结果


@router.get("/project/{project_id}/assets")
def list_assets(project_id: str, db: Session = Depends(get_db)):
    return (
        db.query(Asset)
        .filter(Asset.project_id == project_id)
        .order_by(Asset.id.asc())
        .all()
    )
