"""SQLAlchemy 数据库连接。"""
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if settings.database_url.startswith("sqlite") else {},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _ensure_column(table: str, column: str, ddl: str) -> None:
    """简易字段补齐：SQLite 无该字段时执行 ALTER TABLE ADD COLUMN。"""
    if not settings.database_url.startswith("sqlite"):
        return
    try:
        with engine.connect() as conn:
            cols = {c["name"] for c in inspect(conn).get_columns(table)}
            if column not in cols:
                conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {ddl}"))
                conn.commit()
    except Exception as e:
        # 启动期字段补齐失败不应阻断服务；打印日志继续
        print(f"[db] ensure column {table}.{column} failed: {e}")


def init_db() -> None:
    # 导入所有模型，确保 create_all 能识别
    from app.models import project, asset, generation  # noqa: F401

    Base.metadata.create_all(bind=engine)

    # 补齐模型新增字段（create_all 不会修改已有表）
    _ensure_column("projects", "module_copy", "JSON")
