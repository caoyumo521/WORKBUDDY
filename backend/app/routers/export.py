"""/api/export - 详情页导出 Word / PDF / HTML"""
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.project import Project
from app.services import document_service
from app.routers.generation import list_assets  # 复用 list_assets 的查询

router = APIRouter(prefix="/api/export", tags=["export"])


def _collect_assets(db: Session, project_id: str):
    from app.models.asset import Asset
    return db.query(Asset).filter(Asset.project_id == project_id).all()


@router.post("/project/{project_id}")
def export(
    project_id: str,
    format: Literal["html", "docx", "pdf"] = Query("html"),
    db: Session = Depends(get_db),
):
    project: Project | None = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, "Project not found")
    assets = _collect_assets(db, project_id)
    try:
        if format == "html":
            out = document_service.export_html(project, assets)
        elif format == "docx":
            out = document_service.export_docx(project, assets)
        elif format == "pdf":
            out = document_service.export_pdf(project, assets)
        else:
            raise HTTPException(400, "format 必须为 html/docx/pdf")
    except RuntimeError as e:
        raise HTTPException(500, str(e))
    return FileResponse(out, filename=out.name)
