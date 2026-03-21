"""
CastPlay All-in-One - FastAPI 主应用
一体化数字标牌管理系统

简化版：使用 bootstrap 模块负责所有初始化，避免 main.py 膨胀
"""
from contextlib import asynccontextmanager
from typing import Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pathlib import Path
import uvicorn
from pydantic import ValidationError

from app.bootstrap.application import bootstrap
from app.utils.logger import logger
from app.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理

    启动时：
    1. 初始化数据库
    2. 创建必要目录
    3. 配置中间件
    4. 注册路由
    5. 启动后台任务调度器

    关闭时：
    1. 停止后台任务调度器
    """
    await bootstrap.startup()
    yield
    await bootstrap.shutdown()


# 创建 FastAPI 应用实例
app = bootstrap.get_app()
app.router.lifespan_context = lifespan


# ========== 异常处理器 ==========

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """
    HTTP 异常处理器
    处理所有 HTTPException 及其子类（404, 403, 400 等）
    """
    logger.warning(f"HTTP Exception: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    请求验证异常处理器
    处理 Pydantic 验证错误
    """
    logger.warning(f"Validation error: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors()}
    )


@app.exception_handler(ValidationError)
async def pydantic_validation_exception_handler(request: Request, exc: ValidationError):
    """
    Pydantic 验证异常处理器
    """
    logger.error(f"Pydantic validation error: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": str(exc)}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """
    全局异常处理器
    捕获所有未处理的异常，避免泄露敏感信息
    """
    logger.error(f"Unhandled exception: {type(exc).__name__} - {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"}
    )


# WebSocket 路由（保留在主文件中，因为需要直接处理连接）
@app.websocket("/ws/{device_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    device_id: str,
    token: Optional[str] = None
):
    """
    WebSocket 端点

    设备连接后：
    1. 验证设备是否已注册
    2. 验证 Token（生产环境必须，使用 registration_code 作为 Token）
    3. 接受连接
    4. 处理心跳
    5. 接收服务器推送的更新通知

    Args:
        device_id: 设备唯一标识
        token: 认证令牌（可选，生产环境必须，使用设备的 registration_code）
    """
    from app.websocket.handler import manager as connection_manager
    from app.database import SessionLocal
    from app.models.device import Device

    db = SessionLocal()
    try:
        device = db.query(Device).filter(Device.device_id == device_id).first()

        # 验证设备是否已注册
        if not device:
            logger.warning(f"WebSocket rejected: unregistered device {device_id}")
            await websocket.close(code=4004, reason="Device not registered")
            return

        # 检查设备是否被禁用
        if device.is_disabled:
            logger.warning(f"WebSocket rejected: disabled device {device_id}")
            await websocket.close(code=4003, reason="Device is disabled")
            return

        # 生产环境必须验证 Token
        if settings.ENVIRONMENT == "production":
            if not token:
                logger.warning(f"WebSocket rejected: missing token for {device_id}")
                await websocket.close(code=4001, reason="Authentication token required")
                return

            # 使用 registration_code 作为 Token
            if token != device.registration_code:
                logger.warning(f"WebSocket rejected: invalid token for {device_id}")
                await websocket.close(code=4001, reason="Invalid authentication token")
                return
    finally:
        db.close()

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
                logger.debug(
                    f"Device {device_id} status: {data.get('status')}")

    except WebSocketDisconnect:
        connection_manager.disconnect(device_id)
        logger.info(f"Device {device_id} WebSocket disconnected")
    except Exception as e:
        logger.error(f"WebSocket error for {device_id}: {e}")
        connection_manager.disconnect(device_id)


if __name__ == "__main__":
    logger.info("Starting CastPlay All-in-One...")
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
