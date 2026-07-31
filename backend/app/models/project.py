"""项目主表：存放每个详情页项目的配置。"""
from datetime import datetime
from typing import Optional

from sqlalchemy import JSON, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    industry: Mapped[str] = mapped_column(String(50), default="")
    target_market: Mapped[str] = mapped_column(String(50), default="")
    target_platform: Mapped[str] = mapped_column(String(50), default="")
    language: Mapped[str] = mapped_column(String(20), default="zh-CN")
    visual_style: Mapped[str] = mapped_column(String(50), default="")
    resolution: Mapped[str] = mapped_column(String(10), default="2K")
    aspect_ratio: Mapped[str] = mapped_column(String(10), default="3:4")

    # 产品信息
    product_name: Mapped[str] = mapped_column(String(200), default="")
    product_selling_points: Mapped[Optional[str]] = mapped_column(Text, default="")
    product_target_audience: Mapped[str] = mapped_column(String(200), default="")
    product_description: Mapped[Optional[str]] = mapped_column(Text, default="")
    extra_requirements: Mapped[Optional[str]] = mapped_column(Text, default="")

    # 详情页模块规划（按顺序）
    module_plan: Mapped[list] = mapped_column(JSON, default=list)

    # 工作目录
    workdir: Mapped[str] = mapped_column(String(300), default="")

    # 状态
    status: Mapped[str] = mapped_column(String(20), default="draft")  # draft | planning | generating | done

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    assets = relationship("Asset", back_populates="project", cascade="all, delete-orphan")
    tasks = relationship("GenerationTask", back_populates="project", cascade="all, delete-orphan")
