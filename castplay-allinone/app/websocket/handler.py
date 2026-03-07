"""
WebSocket 连接管理器
管理设备连接和实时消息推送

注意：使用全局单例 manager，其他模块应通过导入此实例使用：
    from app.websocket.handler import manager
"""
from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, List, Optional
from loguru import logger
from datetime import datetime


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

    # ==================== 新增远程控制指令 ====================

    async def send_pause_command(self, device_id: str):
        """
        发送暂停播放指令

        Args:
            device_id: 设备 ID (UUID)
        """
        message = {
            "event": "control",
            "action": "pause",
            "timestamp": self._now()
        }
        await self.send_to_device(device_id, message)
        logger.info(f"Pause command sent to device {device_id}")

    async def send_resume_command(self, device_id: str):
        """
        发送恢复播放指令

        Args:
            device_id: 设备 ID (UUID)
        """
        message = {
            "event": "control",
            "action": "resume",
            "timestamp": self._now()
        }
        await self.send_to_device(device_id, message)
        logger.info(f"Resume command sent to device {device_id}")

    async def send_volume_command(self, device_id: str, volume: int):
        """
        发送音量调节指令

        Args:
            device_id: 设备 ID (UUID)
            volume: 音量值 (0-100)
        """
        if not 0 <= volume <= 100:
            raise ValueError("Volume must be between 0 and 100")

        message = {
            "event": "control",
            "action": "volume",
            "volume": volume,
            "timestamp": self._now()
        }
        await self.send_to_device(device_id, message)
        logger.info(f"Volume command sent to device {device_id}: {volume}")

    async def send_reload_command(self, device_id: str):
        """
        发送重新加载指令

        Args:
            device_id: 设备 ID (UUID)
        """
        message = {
            "event": "control",
            "action": "reload",
            "timestamp": self._now()
        }
        await self.send_to_device(device_id, message)
        logger.info(f"Reload command sent to device {device_id}")

    async def send_seek_command(self, device_id: str, position: int):
        """
        发送跳转指令

        Args:
            device_id: 设备 ID (UUID)
            position: 跳转位置（秒）
        """
        message = {
            "event": "control",
            "action": "seek",
            "position": position,
            "timestamp": self._now()
        }
        await self.send_to_device(device_id, message)
        logger.info(f"Seek command sent to device {device_id}: {position}s")

    async def send_next_command(self, device_id: str):
        """
        发送下一个指令

        Args:
            device_id: 设备 ID (UUID)
        """
        message = {
            "event": "control",
            "action": "next",
            "timestamp": self._now()
        }
        await self.send_to_device(device_id, message)
        logger.info(f"Next command sent to device {device_id}")

    async def send_prev_command(self, device_id: str):
        """
        发送上一个指令

        Args:
            device_id: 设备 ID (UUID)
        """
        message = {
            "event": "control",
            "action": "prev",
            "timestamp": self._now()
        }
        await self.send_to_device(device_id, message)
        logger.info(f"Prev command sent to device {device_id}")

    async def send_switch_playlist_command(self, device_id: str, playlist_id: int):
        """
        发送切换播放列表指令

        Args:
            device_id: 设备 ID (UUID)
            playlist_id: 播放列表 ID
        """
        message = {
            "event": "control",
            "action": "switch_playlist",
            "playlist_id": playlist_id,
            "timestamp": self._now()
        }
        await self.send_to_device(device_id, message)
        logger.info(f"Switch playlist command sent to device {device_id}: playlist {playlist_id}")

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
        return datetime.utcnow().isoformat()

    def get_device_id_by_db_id(self, db_device_id: int) -> Optional[str]:
        """
        根据数据库 ID 获取设备的 WebSocket 连接 ID

        Args:
            db_device_id: 设备数据库 ID

        Returns:
            设备 UUID，如果未连接则返回 None
        """
        # 遍历查找（实际应用中可能需要建立映射表）
        for device_id in self.active_connections.keys():
            # 这里简化处理，实际应该维护 db_id -> device_id 的映射
            # 暂时返回字符串形式的 db_id
            pass
        return str(db_device_id)


# ============================================================================
# 全局连接管理器单例
# 重要：其他模块必须通过此导入使用，不要创建新实例
# ============================================================================
manager = ConnectionManager()
