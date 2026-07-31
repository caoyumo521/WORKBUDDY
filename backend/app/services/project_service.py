"""项目服务：项目生命周期内的所有操作。"""
import base64
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.project import Project
from app.models.asset import Asset
from app.models.generation import GenerationTask
from app.schemas.project import ProjectCreate, ProjectUpdate
from app.utils.file_manager import (
    DIR_PLANNING,
    DIR_PROMPTS,
    gen_project_id,
    make_project_workdir,
)


def list_projects(db: Session) -> List[Project]:
    return db.query(Project).order_by(Project.updated_at.desc()).all()


def get_project(db: Session, project_id: str) -> Optional[Project]:
    return db.query(Project).filter(Project.id == project_id).first()


def create_project(db: Session, payload: ProjectCreate) -> Project:
    pid = payload.id or gen_project_id()
    workdir = make_project_workdir(pid, payload.name)

    project = Project(
        id=pid,
        name=payload.name,
        industry=payload.industry,
        target_market=payload.target_market,
        target_platform=payload.target_platform,
        language=payload.language,
        visual_style=payload.visual_style,
        resolution=payload.resolution,
        aspect_ratio=payload.aspect_ratio,
        product_name=payload.product_name,
        product_selling_points=payload.product_selling_points,
        product_target_audience=payload.product_target_audience,
        product_description=payload.product_description,
        extra_requirements=payload.extra_requirements,
        module_plan=payload.module_plan or [],
        workdir=str(workdir),
        status="draft",
    )
    db.add(project)
    db.commit()
    db.refresh(project)

    # 写入 project.json 快照
    _write_project_json(project)
    return project


def update_project(db: Session, project: Project, payload: ProjectUpdate) -> Project:
    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(project, k, v)
    project.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(project)
    _write_project_json(project)
    return project


def delete_project(db: Session, project: Project) -> None:
    workdir = Path(project.workdir)
    db.delete(project)
    db.commit()
    if workdir.exists():
        shutil.rmtree(workdir, ignore_errors=True)


def _write_project_json(project: Project) -> None:
    p = Path(project.workdir) / "project.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(
        json.dumps(
            {
                "id": project.id,
                "name": project.name,
                "industry": project.industry,
                "target_market": project.target_market,
                "target_platform": project.target_platform,
                "language": project.language,
                "visual_style": project.visual_style,
                "resolution": project.resolution,
                "aspect_ratio": project.aspect_ratio,
                "product": {
                    "name": project.product_name,
                    "selling_points": project.product_selling_points,
                    "target_audience": project.product_target_audience,
                    "description": project.product_description,
                    "extra_requirements": project.extra_requirements,
                },
                "module_plan": project.module_plan,
                "status": project.status,
                "updated_at": project.updated_at.isoformat() if project.updated_at else None,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
