"""
CastPlay All-in-One - FastAPI 主应用
一体化数字标牌管理系统

简化版：使用 bootstrap 模块负责所有初始化，避免 main.py 膨胀
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from pathlib import Path
import uvicorn

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


# WebSocket 路由（保留在主文件中，因为需要直接处理连接）
@app.websocket("/ws/{device_id}")
async def websocket_endpoint(websocket: WebSocket, device_id: str):
    """
    WebSocket 端点

    设备连接后：
    1. 接受连接
    2. 处理心跳
    3. 接收服务器推送的更新通知
    """
    from app.websocket.handler import manager as connection_manager

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
