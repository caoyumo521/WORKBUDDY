"""/api/files - 静态文件服务（项目工作目录下的图片）"""
import io
import re
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse, Response

from app.config import settings

router = APIRouter(prefix="/api/files", tags=["files"])


@router.get("")
def get_file(
    path: str,
    format: str | None = Query(None, description="目标格式 png | jpeg | webp，原格式已是则不转码"),
):
    """返回项目文件。支持 format 参数实时转码为 jpeg/webp。

    - 不传 format：原文件返回（用于直接展示）
    - format=jpeg：转码为 JPG（白色背景合并 alpha）
    - format=webp：转码为 WebP
    """
    p = Path(path).resolve()
    root = Path(settings.projects_root).resolve()
    try:
        p.relative_to(root)
    except ValueError:
        raise HTTPException(403, "Forbidden")

    if not p.exists() or not p.is_file():
        raise HTTPException(404, "Not found")

    # 已经是目标格式或未指定 → 直接返回
    if not format or format.lower() == "auto":
        return FileResponse(p)

    target = format.lower()
    if target not in {"png", "jpeg", "jpg", "webp"}:
        raise HTTPException(400, "format must be png | jpeg | webp")
    if target == "jpg":
        target = "jpeg"

    # 如果源文件本身就是目标格式且未指定尺寸变更 → 直返
    src_suffix = p.suffix.lower().lstrip(".")
    src_ext = "jpeg" if src_suffix == "jpg" else src_suffix
    if src_ext == target:
        return FileResponse(p)

    # 转码
    try:
        from PIL import Image
    except ImportError:
        raise HTTPException(500, "PIL not available")

    img = Image.open(p)
    if img.mode in ("RGBA", "LA", "P") and target == "jpeg":
        # JPEG 不支持透明，合并到白底
        bg = Image.new("RGB", img.size, (255, 255, 255))
        img = img.convert("RGBA")
        bg.paste(img, mask=img.split()[-1])
        img = bg
    elif img.mode != "RGB" and target == "jpeg":
        img = img.convert("RGB")

    buf = io.BytesIO()
    save_kwargs: dict = {}
    if target == "jpeg":
        save_kwargs["quality"] = 92
        save_kwargs["optimize"] = True
    elif target == "webp":
        save_kwargs["quality"] = 90
    img.save(buf, format=target.upper(), **save_kwargs)
    buf.seek(0)

    media = "image/jpeg" if target == "jpeg" else f"image/{target}"
    return Response(content=buf.getvalue(), media_type=media)


@router.get("/preview/{project_id}")
def preview_combined(
    project_id: str,
    format: str = Query("jpeg", description="png | jpeg | webp"),
    gap: int = Query(8, description="图与图之间的间距（px，预留）"),
    bg: str = Query("#ffffff", description="背景色，预留"),
):
    """把项目所有生成图按模块顺序拼成一张长图（详情页预览图）。

    默认返回 JPEG（秒级），通过 ?format=png 获取 PNG 版本（首次较慢，会缓存）。

    性能：第一次请求按需生成（同步），后续直接 FileResponse 返回缓存文件。
    """
    from app.database import SessionLocal
    from app.models.project import Project
    from app.services import preview_cache

    target = format.lower()
    if target not in {"png", "jpeg", "jpg", "webp"}:
        raise HTTPException(400, "format must be png | jpeg | webp")
    if target == "jpg":
        target = "jpeg"

    db = SessionLocal()
    try:
        proj = db.get(Project, project_id)
        if not proj:
            raise HTTPException(404, "Project not found")
        workdir = proj.workdir
    finally:
        db.close()

    if not workdir or not Path(workdir).exists():
        raise HTTPException(404, "Project workdir not found")

    # 命中缓存 → 直接返回（毫秒级）；否则同步重建
    try:
        cache_file = preview_cache.get_or_build(workdir, target, width=800)
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(500, f"预览生成失败: {e}")

    if not cache_file or not cache_file.exists():
        raise HTTPException(404, "No generated images yet")

    media = "image/jpeg" if target == "jpeg" else f"image/{target}"
    return FileResponse(
        path=str(cache_file),
        media_type=media,
        headers={"Cache-Control": "private, max-age=60"},
    )