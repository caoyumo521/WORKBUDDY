"""资产表：产品原图、参考图、竞品图、生成图全部落入此表。"""
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Asset(Base):
    __tablename__ = "assets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[str] = mapped_column(String(40), ForeignKey("projects.id", ondelete="CASCADE"))

    # 类型: product_image | reference | competitor | generated | composed
    asset_type: Mapped[str] = mapped_column(String(30), default="product_image")
    # 模块名（仅对 generated 资产有意义，如 hero / pain_point / feature）
    module_key: Mapped[str] = mapped_column(String(50), default="")
    # 第几张（同一模块可生成多张）
    seq: Mapped[int] = mapped_column(Integer, default=0)
    # 语言（多语言版本时区分）
    language: Mapped[str] = mapped_column(String(20), default="")

    file_path: Mapped[str] = mapped_column(String(500), default="")
    url: Mapped[str] = mapped_column(String(500), default="")
    thumbnail_url: Mapped[str] = mapped_column(String(500), default="")
    width: Mapped[int] = mapped_column(Integer, default=0)
    height: Mapped[int] = mapped_column(Integer, default=0)
    file_size: Mapped[int] = mapped_column(Integer, default=0)

    prompt: Mapped[Optional[str]] = mapped_column(Text, default="")
    negative_prompt: Mapped[Optional[str]] = mapped_column(Text, default="")
    model: Mapped[str] = mapped_column(String(100), default="")
    resolution: Mapped[str] = mapped_column(String(10), default="")

    # 生成任务状态
    status: Mapped[str] = mapped_column(String(20), default="pending")
    error_message: Mapped[Optional[str]] = mapped_column(Text, default="")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="assets")
