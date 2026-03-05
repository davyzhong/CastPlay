"""
CastPlay All-in-One - FastAPI 主应用
一体化数字标牌管理系统
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from pathlib import Path
import uvicorn

from app.config import settings
from app.database import init_database, get_db
from app.middleware.cors import setup_cors
from app.workers import task_manager
from app.utils.logger import logger
from app.websocket import ConnectionManager


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理

    启动时：
    1. 初始化数据库
    2. 启动后台任务队列

    关闭时：
    1. 停止后台任务队列
    """
    # 启动时执行
    logger.info("=" * 50)
    logger.info(f"{settings.APP_NAME} v{settings.APP_VERSION} starting...")
    logger.info("=" * 50)

    # 初始化数据库（测试模式下跳过）
    import os
    if not os.environ.get("TESTING"):
        init_database()

    # 启动后台任务队列
    task_manager.start()

    # 注册 PPT 转换任务处理器
    def handle_ppt_conversion(task):
        from app.services.converter import PPTConverter
        from app.models.media import MediaFile
        from sqlalchemy.orm import Session

        media_id = task.get("media_id")
        file_path = task.get("file_path")

        # 获取数据库会话
        db = SessionLocal()

        try:
            # 更新状态为处理中
            media = db.query(MediaFile).filter(MediaFile.id == media_id).first()
            if media:
                media.status = "processing"
                db.commit()

            # 执行转换
            converter = PPTConverter()
            result = converter.convert(file_path, media_id)

            # 更新数据库
            if media:
                if result.get("success"):
                    media.status = "ready"
                    media.converted_path = result.get("converted_path")
                    if result.get("thumbnail_path"):
                        media.thumbnail_path = result.get("thumbnail_path")
                    if result.get("duration"):
                        media.duration = result.get("duration")
                else:
                    media.status = "failed"
                db.commit()

        except Exception as e:
            logger.error(f"PPT conversion task failed: {e}")
            if media:
                media.status = "failed"
                db.commit()
        finally:
            db.close()

    task_manager.register_handler("convert_ppt", handle_ppt_conversion)

    yield

    # 关闭时执行
    logger.info("Shutting down...")
    task_manager.stop()
    logger.info("Shutdown complete")


# 创建 FastAPI 应用
app = FastAPI(
    title=settings.APP_NAME,
    description="一体化数字标牌管理系统",
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# 配置 CORS
setup_cors(app)

# 挂载静态文件（如果存在）
static_dir = Path("frontend/dist")
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
    logger.info(f"Static files mounted from {static_dir}")

# 挂载媒体文件目录
media_dir = Path("data")
if media_dir.exists():
    app.mount("/media", StaticFiles(directory=str(media_dir)), name="media")
    logger.info(f"Media files mounted from {media_dir}")


# 全局异常处理
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """处理请求验证错误"""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation error",
            "details": exc.errors()
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """处理通用异常"""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "detail": str(exc) if settings.DEBUG else "An unexpected error occurred"
        }
    )


# 健康检查端点
@app.get("/health", tags=["系统"])
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION
    }


# 注册 API 路由
from app.api import auth, devices, media, playlists, player

app.include_router(auth.router, prefix="/api/auth", tags=["认证"])
app.include_router(devices.router, prefix="/api/devices", tags=["设备"])
app.include_router(media.router, prefix="/api/media", tags=["媒体"])
app.include_router(playlists.router, prefix="/api/playlists", tags=["播放列表"])
app.include_router(player.router, prefix="/api/player", tags=["播放端"])


# WebSocket 路由
@app.websocket("/ws/{device_id}")
async def websocket_endpoint(websocket: WebSocket, device_id: str):
    """
    WebSocket 端点

    设备连接后：
    1. 接受连接
    2. 处理心跳
    3. 接收服务器推送的更新通知
    """
    connection_manager = ConnectionManager()

    try:
        # 连接设备
        await connection_manager.connect(device_id, websocket)

        # 处理设备消息
        while True:
            data = await websocket.receive_json()

            # 处理心跳
            if data.get("type") == "heartbeat":
                await websocket.send_json({
                    "type": "heartbeat_ack",
                    "timestamp": connection_manager._now()
                })

            # 处理设备状态上报
            elif data.get("type") == "status":
                # 记录设备状态
                logger.debug(f"Device {device_id} status: {data.get('status')}")

    except WebSocketDisconnect:
        connection_manager.disconnect(device_id)
        logger.info(f"Device {device_id} WebSocket disconnected")
    except Exception as e:
        logger.error(f"WebSocket error for {device_id}: {e}")
        connection_manager.disconnect(device_id)


# 根路径重定向到文档（如果没有前端）
@app.get("/", tags=["系统"])
async def root():
    """根路径"""
    if static_dir.exists():
        # 如果有前端构建文件，返回 index.html
        index_file = static_dir / "index.html"
        if index_file.exists():
            from fastapi.responses import FileResponse
            return FileResponse(index_file)

    # 否则返回欢迎信息
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
