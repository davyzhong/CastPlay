"""
CastPlay All-in-One - FastAPI 主应用
一体化数字标牌管理系统
"""
from app.api import auth, devices, media, playlists, player
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from pathlib import Path
import uvicorn

from app.config import settings
from app.database import init_database, get_db, SessionLocal
from app.middleware.cors import setup_cors
from app.scheduler import start as start_scheduler, stop as stop_scheduler
from app.utils.logger import logger
# 使用全局单例 manager，不要创建新实例
from app.websocket.handler import manager as connection_manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理

    启动时：
    1. 初始化数据库
    2. 启动后台任务调度器

    关闭时：
    1. 停止后台任务调度器
    """
    import os
    is_testing = os.environ.get("TESTING")

    # 启动时执行
    logger.info("=" * 50)
    logger.info(f"{settings.APP_NAME} v{settings.APP_VERSION} starting...")
    logger.info("=" * 50)

    # 初始化数据库（测试模式下跳过）
    if not is_testing:
        init_database()

    # 启动后台任务调度器（测试模式下跳过）
    if not is_testing:
        start_scheduler()

    yield

    # 关闭时执行（测试模式下跳过）
    if not is_testing:
        logger.info("Shutting down...")
        stop_scheduler()
        logger.info("Shutdown complete")


# 创建 FastAPI 应用
app = FastAPI(
    title=settings.APP_NAME,
    description="""
## CastPlay All-in-One 数字标牌管理系统

一体化数字标牌管理平台，支持设备管理、媒体文件管理、播放列表管理和实时推送。

### 主要功能

* **设备管理** - 设备注册、心跳监控、定时配置、状态管理
* **媒体管理** - 图片/视频/PPT 上传、自动转换、缩略图生成
* **播放列表** - 创建、编辑、排序、设备分配
* **实时推送** - WebSocket 实时通知播放列表更新

### 认证方式

使用 JWT Bearer Token 认证，通过 `/api/auth/login` 获取令牌。

### 技术栈

FastAPI + SQLAlchemy + SQLite + React + Ant Design
""",
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    contact={
        "name": "CastPlay Team",
    },
    license_info={
        "name": "MIT",
    },
    lifespan=lifespan
)

# 配置 CORS
setup_cors(app)

# 注意：已移除 SlowAPI 速率限制，改用简单限流器（见 app/utils/simple_rate_limiter.py）
# 小规模内网场景不需要复杂的速率限制

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
    try:
        # 使用全局 connection_manager 单例
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
                logger.debug(
                    f"Device {device_id} status: {data.get('status')}")

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
