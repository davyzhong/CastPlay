"""
WebSocket 连接管理器
管理设备连接和实时消息推送
"""
from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, List
from loguru import logger


class ConnectionManager:
    """
    WebSocket 连接管理器

    管理：
    - 设备连接
    - 消息广播
    - 设备房间
    """

    def __init__(self):
        """初始化连接管理器"""
        # 设备 ID -> WebSocket 连接
        self.active_connections: Dict[str, WebSocket] = {}
        # 房间管理（按 device_id 分组）
        self.rooms: Dict[str, List[str]] = {}

    async def connect(self, device_id: str, websocket: WebSocket):
        """
        设备连接

        Args:
            device_id: 设备 ID
            websocket: WebSocket 连接对象
        """
        await websocket.accept()
        self.active_connections[device_id] = websocket

        # 添加设备到自己的房间
        self.rooms[device_id] = [device_id]

        logger.info(f"Device {device_id} connected via WebSocket")

    def disconnect(self, device_id: str):
        """
        设备断开连接

        Args:
            device_id: 设备 ID
        """
        if device_id in self.active_connections:
            del self.active_connections[device_id]

        if device_id in self.rooms:
            del self.rooms[device_id]

        logger.info(f"Device {device_id} disconnected")

    async def send_to_device(self, device_id: str, message: dict):
        """
        发送消息到指定设备

        Args:
            device_id: 设备 ID
            message: 消息内容（字典）
        """
        if device_id in self.active_connections:
            try:
                await self.active_connections[device_id].send_json(message)
                logger.debug(f"Message sent to device {device_id}: {message}")
            except Exception as e:
                logger.error(f"Failed to send message to {device_id}: {e}")
                # 连接可能已断开，清理
                self.disconnect(device_id)

    async def broadcast(self, message: dict, room: str = None):
        """
        广播消息

        Args:
            message: 消息内容
            room: 房间 ID（可选），None 表示广播给所有设备
        """
        if room:
            # 发送到指定房间
            devices = self.rooms.get(room, [])
            for device_id in devices:
                await self.send_to_device(device_id, message)
        else:
            # 广播给所有设备
            for device_id, websocket in self.active_connections.items():
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    logger.error(f"Failed to broadcast to {device_id}: {e}")

        logger.debug(f"Broadcast sent: {message}")

    async def notify_playlist_update(self, device_id: int):
        """
        通知设备播放列表更新

        Args:
            device_id: 设备数据库 ID
        """
        message = {
            "event": "playlist_update",
            "device_id": device_id,
            "action": "update",
            "timestamp": self._now()
        }
        # 需要将数据库 ID 转换为 device_id（UUID）
        # 这里暂时使用数据库 ID
        await self.send_to_device(str(device_id), message)

    async def notify_schedule_update(self, device_id: int):
        """
        通知设备定时配置更新

        Args:
            device_id: 设备数据库 ID
        """
        message = {
            "event": "schedule_update",
            "device_id": device_id,
            "action": "update",
            "timestamp": self._now()
        }
        await self.send_to_device(str(device_id), message)

    async def notify_force_sync(self, device_id: int):
        """
        通知设备强制同步

        Args:
            device_id: 设备数据库 ID
        """
        message = {
            "event": "force_sync",
            "device_id": device_id,
            "action": "sync",
            "timestamp": self._now()
        }
        await self.send_to_device(str(device_id), message)

    async def notify_reboot(self, device_id: int):
        """
        通知设备重启

        Args:
            device_id: 设备数据库 ID
        """
        message = {
            "event": "reboot",
            "device_id": device_id,
            "action": "reboot",
            "timestamp": self._now()
        }
        await self.send_to_device(str(device_id), message)

    def get_connected_devices(self) -> List[str]:
        """
        获取已连接的设备 ID 列表

        Returns:
            设备 ID 列表
        """
        return list(self.active_connections.keys())

    def is_connected(self, device_id: str) -> bool:
        """
        检查设备是否已连接

        Args:
            device_id: 设备 ID

        Returns:
            是否已连接
        """
        return device_id in self.active_connections

    def _now(self) -> str:
        """
        获取当前时间字符串

        Returns:
            ISO 格式的时间字符串
        """
        from datetime import datetime
        return datetime.utcnow().isoformat()


# 全局连接管理器实例
manager = ConnectionManager()
