"""应用入口 - 启动 FastAPI 服务"""
import uvicorn
from app.config import settings

if __name__ == "__main__":
    # 关闭 reload，避免 watch 干扰手动重启
    uvicorn.run(
        "app.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=False,
    )
