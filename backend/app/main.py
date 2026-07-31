"""FastAPI 应用入口。"""
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings as app_settings
from app.database import init_db
from app.routers import ai, export, files, generation, meta, projects, settings as settings_router, upload

logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="AI 电商详情页工作台",
    description="本地运行的 AI 详情页生产工作台",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=app_settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/api/health")
def health():
    return {"status": "ok"}


app.include_router(projects.router)
app.include_router(upload.router)
app.include_router(generation.router)
app.include_router(files.router)
app.include_router(export.router)
app.include_router(meta.router)
app.include_router(ai.router)
app.include_router(settings_router.router)
