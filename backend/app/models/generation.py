"""生图任务表：每个模块每次生成都是一个任务，方便状态追踪与失败重试。"""
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class GenerationTask(Base):
    __tablename__ = "generation_tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[str] = mapped_column(String(40), ForeignKey("projects.id", ondelete="CASCADE"))

    module_key: Mapped[str] = mapped_column(String(50), default="")
    language: Mapped[str] = mapped_column(String(20), default="")

    # pending | running | success | failed
    status: Mapped[str] = mapped_column(String(20), default="pending")
    progress: Mapped[int] = mapped_column(Integer, default=0)
    message: Mapped[Optional[str]] = mapped_column(Text, default="")
    asset_id: Mapped[Optional[int]] = mapped_column(Integer, default=None)

    prompt: Mapped[Optional[str]] = mapped_column(Text, default="")
    model: Mapped[str] = mapped_column(String(100), default="")
    resolution: Mapped[str] = mapped_column(String(10), default="")
    aspect_ratio: Mapped[str] = mapped_column(String(10), default="")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    project = relationship("Project", back_populates="tasks")
