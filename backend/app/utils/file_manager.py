"""项目文件管理器：统一管理每个项目在磁盘上的目录结构。"""
import shutil
import uuid
from datetime import datetime
from pathlib import Path
from typing import Iterable, Optional

from app.config import settings

# 目录名常量
DIR_PRODUCT_MATERIAL = "01_产品资料"
DIR_REFERENCE = "02_参考案例"
DIR_VISUAL_ANALYSIS = "03_视觉分析"
DIR_PLANNING = "04_页面策划"
DIR_PROMPTS = "05_Prompts"
DIR_IMAGES = "06_生成图片"
DIR_COPYWRITING = "07_文案"
DIR_DOCS = "08_文档"
DIR_EXPORTS = "09_导出"

MODULE_DIRS = {
    "hero": "01_Hero首屏",
    "brand_visual": "02_BrandVisual品牌主视觉",
    "pain_point": "03_PainPoint用户痛点",
    "core_selling": "04_CoreSelling核心卖点",
    "feature": "05_Feature产品功能",
    "detail": "06_Detail产品细节",
    "material": "07_Material面料材质",
    "craft": "08_Craft工艺展示",
    "tech": "09_Tech科技功能",
    "structure": "10_Structure结构拆解",
    "scenario": "11_Scenario使用场景",
    "lifestyle": "12_Lifestyle生活方式",
    "size_spec": "13_SizeSpec尺寸参数",
    "comparison": "14_Comparison对比模块",
    "advantage": "15_Advantage产品优势",
    "review": "16_Review用户评价",
    "faq": "17_FAQ",
    "cta": "18_CTA购买引导",
    "size_chart": "19_SizeChart尺寸图",
    "spec_param": "20_SpecParam规格参数",
    "after_sales": "21_AfterSales售后保障",
    "brand_story": "22_BrandStory品牌故事",
    "notice": "23_Notice注意事项",
    "qualification": "24_Qualification资质认证",
    "factory": "25_Factory工厂实力",
    "package": "26_Package包装展示",
    "logistics": "27_Logistics发货物流",
    "sku": "28_SKUSKU展示",
}


def gen_project_id() -> str:
    return f"proj_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:6]}"


def safe_filename(name: str) -> str:
    """去除 Windows/Unix 都不安全的字符。"""
    bad = '<>:"/\\|?*\n\r\t'
    for ch in bad:
        name = name.replace(ch, "_")
    return name.strip().strip(".") or "untitled"


def make_project_workdir(project_id: str, project_name: str) -> Path:
    """每个项目独立的根目录。"""
    root = Path(settings.projects_root) / f"{project_id}_{safe_filename(project_name)}"
    root.mkdir(parents=True, exist_ok=True)

    # 初始化子目录
    for sub in [
        DIR_PRODUCT_MATERIAL,
        DIR_REFERENCE,
        DIR_VISUAL_ANALYSIS,
        DIR_PLANNING,
        DIR_PROMPTS,
        DIR_IMAGES,
        DIR_COPYWRITING,
        DIR_DOCS,
        DIR_EXPORTS,
    ]:
        (root / sub).mkdir(exist_ok=True)

    # 模块子目录
    for k, dirname in MODULE_DIRS.items():
        (root / DIR_IMAGES / dirname).mkdir(exist_ok=True)

    return root


def module_dir(workdir: str | Path, module_key: str) -> Path:
    name = MODULE_DIRS.get(module_key, f"99_{module_key}")
    return Path(workdir) / DIR_IMAGES / name


def save_uploaded_file(src_path: str | Path, dest_path: str | Path) -> Path:
    dest = Path(dest_path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src_path, dest)
    return dest


def remove_file(path: str | Path) -> bool:
    p = Path(path)
    if p.exists() and p.is_file():
        p.unlink()
        return True
    return False


def relative_to_projects(path: str | Path) -> str:
    p = Path(path).resolve()
    try:
        return str(p.relative_to(Path(settings.projects_root).resolve()))
    except ValueError:
        return str(p)


def timestamp_str() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")
