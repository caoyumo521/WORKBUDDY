"""组合预览缓存服务。

设计目标：
- 用户点"组合预览"必须秒级返回（不能每次重新 PIL 拼接）
- 缓存文件存到 `projects/<dir>/_preview/combined_<format>_w<width>.<ext>`
- 后台任务在每次图片生成完成后自动刷新
- 接口路径：get_or_build(project_id, format, width) -> Path | None

触发点：
- generation 任务成功保存图片后，调用 `schedule_refresh(project_id, workdir)` 异步重建
- 用户点"组合预览"时，`get_or_build` 先查缓存，命中且比最新 asset 新 → 直接返回；否则同步重建
"""
from __future__ import annotations

import io
import json
import logging
import threading
import time
from pathlib import Path
from typing import Dict, Optional, Tuple

from PIL import Image

logger = logging.getLogger(__name__)


# 缓存根目录名
_PREVIEW_DIR = "_preview"
_META_FILE = "_meta.json"

# 单张缓存最大宽度（像素）。前端展示用 800 足够清晰，文件小、生成快
_DEFAULT_WIDTH = 800
# JPEG 质量
_JPEG_QUALITY = 88

# 进程级锁字典：每个 project_id 一把锁，防止并发刷新
_locks: Dict[str, threading.Lock] = {}
_locks_guard = threading.Lock()


def _get_lock(project_id: str) -> threading.Lock:
    """获取（懒创建）项目级锁。"""
    with _locks_guard:
        lock = _locks.get(project_id)
        if lock is None:
            lock = threading.Lock()
            _locks[project_id] = lock
        return lock


def _preview_root(workdir: str) -> Path:
    """缓存目录：<workdir>/_preview/"""
    root = Path(workdir) / _PREVIEW_DIR
    root.mkdir(parents=True, exist_ok=True)
    return root


def _cache_paths(workdir: str, fmt: str, width: int) -> Tuple[Path, Path]:
    """返回 (缓存文件路径, 元信息路径)。fmt ∈ {png, jpeg, jpg, webp}"""
    fmt = fmt.lower()
    if fmt == "jpg":
        fmt = "jpeg"
    ext = "jpg" if fmt == "jpeg" else fmt
    root = _preview_root(workdir)
    return root / f"combined_{fmt}_w{width}.{ext}", root / _META_FILE


def _meta_path(workdir: str) -> Path:
    return _preview_root(workdir) / _META_FILE


def _read_meta(workdir: str) -> dict:
    p = _meta_path(workdir)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _write_meta(workdir: str, data: dict) -> None:
    p = _meta_path(workdir)
    try:
        p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as e:
        logger.warning("Failed to write preview meta: %s", e)


def _scan_assets(workdir: str) -> Tuple[list[Path], float]:
    """扫描 06_生成图片/ 下的所有图片文件，返回 (paths, max_mtime)。

    不依赖数据库，纯文件系统扫描，更快且无锁。
    """
    root = Path(workdir) / "06_生成图片"
    if not root.exists():
        return [], 0.0
    paths: list[Path] = []
    max_mtime = 0.0
    for ext in ("*.png", "*.jpg", "*.jpeg", "*.webp"):
        for p in root.rglob(ext):
            try:
                mt = p.stat().st_mtime
            except OSError:
                continue
            if mt > max_mtime:
                max_mtime = mt
            paths.append(p)
    return sorted(paths), max_mtime


def _stitch(images: list[Path], width: int, gap: int, fmt: str) -> bytes:
    """核心拼接逻辑。返回图片字节。

    性能关键：
    - max_w 默认 800（够用且文件小）
    - PNG 不开 optimize（optimize=True 慢 10x+）
    - 内部统一用 RGB，避免 RGBA 转换开销
    """
    fmt = fmt.lower()
    if fmt == "jpg":
        fmt = "jpeg"

    # 1. 打开 + 统一宽度
    pil_imgs: list[Image.Image] = []
    for p in images:
        try:
            img = Image.open(p)
            img.load()  # 强制解码，释放文件句柄
        except Exception as e:
            logger.warning("Skip unreadable image %s: %s", p, e)
            continue
        if img.size[0] != width:
            ratio = width / img.size[0]
            new_h = max(1, int(img.size[1] * ratio))
            img = img.resize((width, new_h), Image.LANCZOS)
        pil_imgs.append(img)

    if not pil_imgs:
        raise ValueError("No loadable images")

    # 2. 拼接
    total_h = sum(i.size[1] for i in pil_imgs) + gap * (len(pil_imgs) - 1)
    canvas = Image.new("RGB", (width, total_h), (255, 255, 255))
    y = 0
    for img in pil_imgs:
        if img.mode != "RGB":
            img = img.convert("RGB")
        canvas.paste(img, (0, y))
        y += img.size[1] + gap

    # 3. 编码
    buf = io.BytesIO()
    if fmt == "jpeg":
        canvas.save(buf, format="JPEG", quality=_JPEG_QUALITY)
    elif fmt == "webp":
        canvas.save(buf, format="WEBP", quality=85, method=4)
    else:  # png
        # 不开 optimize！optimize=True 在大画布上会慢 10-20x
        canvas.save(buf, format="PNG")
    return buf.getvalue()


def _build_and_save(workdir: str, fmt: str, width: int) -> Optional[Path]:
    """重建缓存。返回缓存文件路径，失败返回 None。"""
    fmt = fmt.lower()
    if fmt == "jpg":
        fmt = "jpeg"
    cache_path, _ = _cache_paths(workdir, fmt, width)
    images, max_mtime = _scan_assets(workdir)
    if not images:
        # 没有图片，删除旧缓存
        if cache_path.exists():
            try:
                cache_path.unlink()
            except OSError:
                pass
        return None

    t0 = time.time()
    try:
        data = _stitch(images, width=width, gap=8, fmt=fmt)
    except Exception as e:
        logger.error("Stitch failed: %s", e)
        return None
    elapsed = time.time() - t0
    logger.info("Stitch %d images: %.2fs, size=%dKB", len(images), elapsed, len(data) // 1024)

    # 原子写：先写 .tmp，再 rename，避免读到半截文件
    tmp = cache_path.with_suffix(cache_path.suffix + ".tmp")
    try:
        tmp.write_bytes(data)
        tmp.replace(cache_path)
    except Exception as e:
        logger.error("Failed to save cache: %s", e)
        if tmp.exists():
            try:
                tmp.unlink()
            except OSError:
                pass
        return None

    # 写元信息
    _write_meta(
        workdir,
        {
            "updated_at": time.time(),
            "asset_mtime": max_mtime,
            "image_count": len(images),
            "format": fmt,
            "width": width,
            "size_kb": len(data) // 1024,
        },
    )
    return cache_path


def get_or_build(workdir: str, fmt: str = "jpeg", width: int = _DEFAULT_WIDTH) -> Optional[Path]:
    """获取缓存。命中且新鲜直接返回，否则重建（同步）。

    缓存判定逻辑：
    - 缓存文件存在
    - 缓存文件的 mtime >= 最新 asset 的 mtime
    满足以上两条 → 直接返回缓存文件，不需要 meta。
    """
    fmt = fmt.lower()
    if fmt == "jpg":
        fmt = "jpeg"
    cache_path, _ = _cache_paths(workdir, fmt, width)

    # 快速路径：先扫描 assets 拿到 max_mtime
    images, max_mtime = _scan_assets(workdir)
    if not images:
        return None

    # 缓存命中：文件存在且 mtime >= 最新 asset mtime
    try:
        if cache_path.exists() and cache_path.stat().st_mtime >= max_mtime:
            return cache_path
    except OSError:
        pass

    # 缓存过期或不存在：加锁重建
    lock = _get_lock(workdir)
    with lock:
        # double-check（拿锁后可能别的线程刚建好）
        try:
            if cache_path.exists() and cache_path.stat().st_mtime >= max_mtime:
                return cache_path
        except OSError:
            pass
        return _build_and_save(workdir, fmt, width)


def schedule_refresh(workdir: str) -> None:
    """后台异步刷新缓存（不阻塞调用方）。

    在生成任务成功保存图片后调用。启动一个新线程重建缓存。
    """
    if not workdir:
        return
    t = threading.Thread(
        target=_background_refresh,
        args=(workdir,),
        daemon=True,
        name=f"preview-refresh-{Path(workdir).name}",
    )
    t.start()


def _background_refresh(workdir: str) -> None:
    """后台线程入口。同时刷新 jpeg + png 两个缓存。"""
    try:
        lock = _get_lock(workdir)
        if not lock.acquire(blocking=False):
            # 已有刷新在跑，跳过
            return
        try:
            for fmt in ("jpeg", "png"):
                try:
                    _build_and_save(workdir, fmt, _DEFAULT_WIDTH)
                except Exception as e:
                    logger.error("Background refresh %s failed: %s", fmt, e)
        finally:
            lock.release()
    except Exception as e:
        logger.error("Background refresh crashed: %s", e)


def invalidate(workdir: str) -> None:
    """删除某个项目的所有缓存（图片被删除时调用）。"""
    root = _preview_root(workdir)
    for p in root.glob("*"):
        try:
            p.unlink()
        except OSError:
            pass
