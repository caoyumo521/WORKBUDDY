"""/api/upload - 文件上传（产品图、参考图、竞品图）"""
import shutil
import uuid
from pathlib import Path
from typing import List

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.asset import Asset
from app.models.project import Project
from app.utils.file_manager import DIR_PRODUCT_MATERIAL, DIR_REFERENCE, safe_filename

router = APIRouter(prefix="/api/upload", tags=["upload"])

ALLOWED_EXT = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
MAX_SIZE = 10 * 1024 * 1024  # 10MB


@router.post("/project/{project_id}")
async def upload_files(
    project_id: str,
    files: List[UploadFile] = File(...),
    asset_type: str = Form("product_image"),  # product_image | reference | competitor
    db: Session = Depends(get_db),
):
    project: Project | None = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, "Project not found")

    if asset_type == "product_image":
        sub = DIR_PRODUCT_MATERIAL
    else:
        sub = DIR_REFERENCE

    base = Path(project.workdir) / sub
    base.mkdir(parents=True, exist_ok=True)

    saved = []
    for f in files:
        if not f.filename:
            continue
        ext = Path(f.filename).suffix.lower()
        if ext not in ALLOWED_EXT:
            raise HTTPException(400, f"不支持的文件类型: {ext}")

        # 流式读取，避免 OOM
        content = await f.read()
        if len(content) > MAX_SIZE:
            raise HTTPException(400, f"{f.filename} 超过 10MB 限制")

        new_name = f"{safe_filename(Path(f.filename).stem)}_{uuid.uuid4().hex[:6]}{ext}"
        dest = base / new_name
        dest.write_bytes(content)

        asset = Asset(
            project_id=project.id,
            asset_type=asset_type,
            module_key="",
            file_path=str(dest),
            url=f"/api/files?path={dest}",
            file_size=len(content),
            status="success",
        )
        db.add(asset)
        saved.append(asset)

    db.commit()
    for a in saved:
        db.refresh(a)
    return [
        {
            "id": a.id,
            "file_path": a.file_path,
            "url": a.url,
            "file_size": a.file_size,
        }
        for a in saved
    ]


@router.delete("/asset/{asset_id}")
def delete_asset(asset_id: int, db: Session = Depends(get_db)):
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(404, "Asset not found")
    p = Path(asset.file_path)
    if p.exists():
        try:
            p.unlink()
        except Exception:
            pass
    db.delete(asset)
    db.commit()
    return {"ok": True}
