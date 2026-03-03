"""
Socket.IO Server Instance (FastAPI 版本)

异步 Socket.IO 服务器实例，用于设备与服务器之间的实时通信
"""
import socketio

# 创建异步 Socket.IO 服务器
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins='*',  # 在生产环境中应该限制
    logger=True,
    engineio_logger=True
)


def get_sio():
    """获取 Socket.IO 实例"""
    return sio
