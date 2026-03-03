"""CastPlay Server - FastAPI Application Entry Point"""
import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
import socketio

from app.core.config import settings
from app.database import engine, Base
from app.api.v1 import api_router
from app.websocket.sio import sio

# 配置日志
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # Startup
    logger.info("Starting CastPlay Server...")

    # 创建存储目录
    for folder_path in [
        settings.UPLOAD_FOLDER,
        settings.CONVERTED_FOLDER,
        settings.THUMBNAIL_FOLDER
    ]:
        os.makedirs(folder_path, exist_ok=True)

    # 创建数据库表（开发环境）
    if settings.DEBUG:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    logger.info(f"CastPlay Server started (debug={settings.DEBUG})")

    yield

    # Shutdown
    logger.info("Shutting down CastPlay Server...")
    await engine.dispose()


def create_app() -> FastAPI:
    """创建 FastAPI 应用"""
    app = FastAPI(
        title="CastPlay Server",
        description="数字标牌后台管理系统 API",
        version="2.0.0",
        lifespan=lifespan,
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
    )

    # CORS 配置
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 注册 API 路由
    app.include_router(api_router, prefix="/api/v1")

    # 兼容旧版 API（无版本前缀）
    app.include_router(api_router, prefix="/api", include_in_schema=False)

    # 健康检查
    @app.get("/health")
    async def health_check():
        return {"status": "ok", "service": "castplay-server"}

    # 网页播放器
    @app.get("/player")
    async def web_player():
        static_dir = os.path.join(os.path.dirname(__file__), "..", "static")
        return FileResponse(os.path.join(static_dir, "player.html"))

    # 全局异常处理
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled Exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal Server Error",
                "message": str(exc) if settings.DEBUG else "服务器内部错误"
            }
        )

    # 挂载 Socket.IO
    sio_app = socketio.ASGIApp(sio, other_asgi_app=app)

    return sio_app


# 创建应用实例
app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=settings.DEBUG
    )
