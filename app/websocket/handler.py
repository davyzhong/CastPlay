"""
WebSocket 连接管理器
管理设备连接和实时消息推送

注意：使用全局单例 manager，其他模块应通过导入此实例使用：
    from app.websocket.handler import manager
"""
from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, List, Optional, Any
from loguru import logger
from datetime import datetime
from enum import Enum
from pydantic import BaseModel
from typing import Optional as Opt


# ============================================================================
# 消息类型定义
# ============================================================================

class MessageType(str, Enum):
    """WebSocket 消息类型"""
    # 服务端 -> 播放端
    PLAYLIST_ASSIGNED = "playlist_assigned"      # 播放列表已分配
    PLAYLIST_UPDATED = "playlist_updated"        # 播放列表内容更新
    PLAYLIST_REMOVED = "playlist_removed"        # 播放列表已移除
    DEVICE_CONFIG_UPDATED = "device_config_updated" # 设备配置更新
    DEVICE_DISABLED = "device_disabled"          # 设备已禁用
    SCHEDULE_UPDATED = "schedule_updated"        # 定时配置更新
    SCHEDULE_UPDATE = "schedule_update"          # 调度触发播放列表切换
    FORCE_SYNC = "force_sync"                    # 强制同步
    CONTROL = "control"                          # 播放控制指令

    # 播放端 -> 服务端
    DOWNLOAD_PROGRESS = "download_progress"      # 下载进度上报
    DOWNLOAD_COMPLETE = "download_complete"      # 下载完成
    DOWNLOAD_FAILED = "download_failed"          # 下载失败
    PLAYLIST_SWITCHED = "playlist_switched"      # 播放列表已切换
    PLAYER_STATUS = "player_status"              # 播放状态上报
    HEARTBEAT = "heartbeat"                      # 心跳


class PlaylistNotificationData(BaseModel):
    """播放列表通知数据"""
    playlist_id: int
    playlist_name: str
    version: str              # 播放列表版本号
    action: str               # "assign", "update", "remove"
    item_count: int = 0        # 媒体项数量
    total_size: int = 0        # 总文件大小（字节）
    priority: str = "normal"   # "high", "normal", "low"
    changes: Opt[Dict[str, Any]] = None  # 增量更新时的变更内容


class DownloadProgressData(BaseModel):
    """下载进度数据"""
    playlist_id: int
    media_id: int
    media_name: str
    progress: float          # 0.0 - 100.0
    status: str              # "pending", "downloading", "completed", "failed"
    downloaded_bytes: int = 0
    total_bytes: int = 0
    error: Opt[str] = None


# ============================================================================
# 连接管理器
# ============================================================================

class ConnectionManager:
    """
    WebSocket 连接管理器

    管理：
    - 设备连接
    - 消息广播
    - 设备房间
    - 数据库 ID 到 WebSocket ID 的映射
    """

    def __init__(self):
        """初始化连接管理器"""
        # device_id (UUID) -> WebSocket 连接
        self.active_connections: Dict[str, WebSocket] = {}
        # 房间管理（按 device_id 分组）
        self.rooms: Dict[str, List[str]] = {}
        # 数据库 ID -> device_id (UUID) 映射
        self.db_id_to_device_id: Dict[int, str] = {}

    def register_device_mapping(self, db_id: int, device_id: str):
        """
        注册数据库 ID 到 device_id 的映射

        Args:
            db_id: 设备数据库 ID
            device_id: 设备 UUID
        """
        self.db_id_to_device_id[db_id] = device_id
        logger.debug(f"Registered device mapping: db_id={db_id} -> device_id={device_id}")

    def unregister_device_mapping(self, db_id: int):
        """
        注销数据库 ID 映射

        Args:
            db_id: 设备数据库 ID
        """
        if db_id in self.db_id_to_device_id:
            del self.db_id_to_device_id[db_id]

    def get_device_id_by_db_id(self, db_id: int) -> Optional[str]:
        """
        根据数据库 ID 获取设备的 WebSocket 连接 ID

        Args:
            db_id: 设备数据库 ID

        Returns:
            设备 UUID，如果未找到则返回 None
        """
        return self.db_id_to_device_id.get(db_id)

    async def connect(self, device_id: str, websocket: WebSocket, db_id: int = None):
        """
        设备连接

        Args:
            device_id: 设备 ID (UUID)
            websocket: WebSocket 连接对象
            db_id: 设备数据库 ID（可选）
        """
        await websocket.accept()
        self.active_connections[device_id] = websocket

        # 添加设备到自己的房间
        self.rooms[device_id] = [device_id]

        # 注册映射
        if db_id is not None:
            self.register_device_mapping(db_id, device_id)

        logger.info(f"Device {device_id} connected via WebSocket (db_id={db_id})")

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

        # 清理映射
        for db_id, d_id in list(self.db_id_to_device_id.items()):
            if d_id == device_id:
                del self.db_id_to_device_id[db_id]

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
                logger.debug(f"Message sent to device {device_id}: {message.get('event', message.get('type', 'unknown'))}")
            except Exception as e:
                logger.error(f"Failed to send message to {device_id}: {e}")
                # 连接可能已断开，清理
                self.disconnect(device_id)

    async def send_to_device_by_db_id(self, db_id: int, message: dict):
        """
        通过数据库 ID 发送消息到设备

        Args:
            db_id: 设备数据库 ID
            message: 消息内容
        """
        device_id = self.get_device_id_by_db_id(db_id)
        if device_id:
            await self.send_to_device(device_id, message)
        else:
            logger.warning(f"Device with db_id={db_id} not connected")

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

        logger.debug(f"Broadcast sent: {message.get('event', message.get('type', 'unknown'))}")

    # ==================== 播放列表通知（新版） ====================

    async def notify_playlist_assigned(self, device_id: str, data: PlaylistNotificationData):
        """
        通知设备：播放列表已分配

        Args:
            device_id: 设备 ID (UUID)
            data: 播放列表通知数据
        """
        message = {
            "type": MessageType.PLAYLIST_ASSIGNED,
            "device_id": device_id,
            "timestamp": self._now(),
            "data": data.model_dump()
        }
        await self.send_to_device(device_id, message)
        logger.info(f"Playlist assigned notification sent to {device_id}: playlist {data.playlist_id}")

    async def notify_playlist_updated(self, device_id: str, data: PlaylistNotificationData):
        """
        通知设备：播放列表内容已更新

        Args:
            device_id: 设备 ID (UUID)
            data: 播放列表通知数据
        """
        message = {
            "type": MessageType.PLAYLIST_UPDATED,
            "device_id": device_id,
            "timestamp": self._now(),
            "data": data.model_dump()
        }
        await self.send_to_device(device_id, message)
        logger.info(f"Playlist updated notification sent to {device_id}: playlist {data.playlist_id} v{data.version}")

    async def notify_playlist_removed(self, device_id: str, playlist_id: int):
        """
        通知设备：播放列表已移除

        Args:
            device_id: 设备 ID (UUID)
            playlist_id: 播放列表 ID
        """
        message = {
            "type": MessageType.PLAYLIST_REMOVED,
            "device_id": device_id,
            "timestamp": self._now(),
            "data": {
                "playlist_id": playlist_id,
                "action": "remove"
            }
        }
        await self.send_to_device(device_id, message)
        logger.info(f"Playlist removed notification sent to {device_id}: playlist {playlist_id}")

    # ==================== 设备配置通知 ====================

    async def notify_device_config_updated(self, device_id: str, config: dict):
        """
        通知设备：设备配置更新（如播放速度）

        Args:
            device_id: 设备 ID (UUID)
            config: 配置内容
        """
        message = {
            "type": MessageType.DEVICE_CONFIG_UPDATED,
            "device_id": device_id,
            "timestamp": self._now(),
            "data": config
        }
        await self.send_to_device(device_id, message)
        logger.info(f"Device config updated notification sent to {device_id}")

    async def notify_device_disabled(self, device_id: str, is_disabled: bool):
        """
        通知设备：设备已禁用/启用

        Args:
            device_id: 设备 ID (UUID)
            is_disabled: 是否禁用
        """
        message = {
            "type": MessageType.DEVICE_DISABLED if is_disabled else MessageType.DEVICE_CONFIG_UPDATED,
            "device_id": device_id,
            "timestamp": self._now(),
            "data": {
                "is_disabled": is_disabled,
                "message": "设备已被禁用，只能播放默认内容" if is_disabled else "设备已启用"
            }
        }
        await self.send_to_device(device_id, message)
        logger.info(f"Device {'disabled' if is_disabled else 'enabled'} notification sent to {device_id}")

    async def notify_schedule_updated(self, device_id: str, schedule: dict):
        """
        通知设备：定时配置更新

        Args:
            device_id: 设备 ID (UUID)
            schedule: 定时配置
        """
        message = {
            "type": MessageType.SCHEDULE_UPDATED,
            "device_id": device_id,
            "timestamp": self._now(),
            "data": schedule
        }
        await self.send_to_device(device_id, message)
        logger.info(f"Schedule updated notification sent to {device_id}")

    async def notify_schedule_trigger(
        self,
        device_id: str,
        playlist_id: int,
        schedule_id: int | None = None,
        schedule_name: str | None = None
    ):
        """
        通知设备：调度触发，需要切换播放列表

        Args:
            device_id: 设备 ID (UUID)
            playlist_id: 目标播放列表 ID
            schedule_id: 触发的调度 ID（可选）
            schedule_name: 调度名称（可选）
        """
        message = {
            "type": MessageType.SCHEDULE_UPDATE,
            "device_id": device_id,
            "timestamp": self._now(),
            "data": {
                "playlist_id": playlist_id,
                "schedule_id": schedule_id,
                "schedule_name": schedule_name,
                "action": "switch"
            }
        }
        await self.send_to_device(device_id, message)
        logger.info(
            f"Schedule trigger notification sent to {device_id}: "
            f"switch to playlist {playlist_id} (schedule {schedule_id})"
        )

    async def notify_force_sync(self, device_id: str):
        """
        通知设备：强制同步

        Args:
            device_id: 设备 ID (UUID)
        """
        message = {
            "type": MessageType.FORCE_SYNC,
            "device_id": device_id,
            "timestamp": self._now(),
            "data": {
                "action": "sync"
            }
        }
        await self.send_to_device(device_id, message)
        logger.info(f"Force sync notification sent to {device_id}")

    async def notify_reboot(self, device_id: str):
        """
        通知设备：重启

        Args:
            device_id: 设备 ID (UUID)
        """
        message = {
            "type": MessageType.CONTROL,
            "device_id": device_id,
            "timestamp": self._now(),
            "data": {
                "action": "reboot"
            }
        }
        await self.send_to_device(device_id, message)
        logger.info(f"Reboot notification sent to {device_id}")

    # ==================== 播放控制指令 ====================

    async def send_pause_command(self, device_id: str):
        """发送暂停播放指令"""
        message = {
            "type": MessageType.CONTROL,
            "device_id": device_id,
            "timestamp": self._now(),
            "data": {"action": "pause"}
        }
        await self.send_to_device(device_id, message)
        logger.info(f"Pause command sent to device {device_id}")

    async def send_resume_command(self, device_id: str):
        """发送恢复播放指令"""
        message = {
            "type": MessageType.CONTROL,
            "device_id": device_id,
            "timestamp": self._now(),
            "data": {"action": "resume"}
        }
        await self.send_to_device(device_id, message)
        logger.info(f"Resume command sent to device {device_id}")

    async def send_volume_command(self, device_id: str, volume: int):
        """发送音量调节指令"""
        if not 0 <= volume <= 100:
            raise ValueError("Volume must be between 0 and 100")
        message = {
            "type": MessageType.CONTROL,
            "device_id": device_id,
            "timestamp": self._now(),
            "data": {"action": "volume", "volume": volume}
        }
        await self.send_to_device(device_id, message)
        logger.info(f"Volume command sent to device {device_id}: {volume}")

    async def send_reload_command(self, device_id: str):
        """发送重新加载指令"""
        message = {
            "type": MessageType.CONTROL,
            "device_id": device_id,
            "timestamp": self._now(),
            "data": {"action": "reload"}
        }
        await self.send_to_device(device_id, message)
        logger.info(f"Reload command sent to device {device_id}")

    async def send_seek_command(self, device_id: str, position: int):
        """发送跳转指令"""
        message = {
            "type": MessageType.CONTROL,
            "device_id": device_id,
            "timestamp": self._now(),
            "data": {"action": "seek", "position": position}
        }
        await self.send_to_device(device_id, message)
        logger.info(f"Seek command sent to device {device_id}: {position}s")

    async def send_next_command(self, device_id: str):
        """发送下一个指令"""
        message = {
            "type": MessageType.CONTROL,
            "device_id": device_id,
            "timestamp": self._now(),
            "data": {"action": "next"}
        }
        await self.send_to_device(device_id, message)
        logger.info(f"Next command sent to device {device_id}")

    async def send_prev_command(self, device_id: str):
        """发送上一个指令"""
        message = {
            "type": MessageType.CONTROL,
            "device_id": device_id,
            "timestamp": self._now(),
            "data": {"action": "prev"}
        }
        await self.send_to_device(device_id, message)
        logger.info(f"Prev command sent to device {device_id}")

    async def send_switch_playlist_command(self, device_id: str, playlist_id: int):
        """发送切换播放列表指令"""
        message = {
            "type": MessageType.CONTROL,
            "device_id": device_id,
            "timestamp": self._now(),
            "data": {"action": "switch_playlist", "playlist_id": playlist_id}
        }
        await self.send_to_device(device_id, message)
        logger.info(f"Switch playlist command sent to device {device_id}: playlist {playlist_id}")

    # ==================== 辅助方法 ====================

    def get_connected_devices(self) -> List[str]:
        """获取已连接的设备 ID 列表"""
        return list(self.active_connections.keys())

    def is_connected(self, device_id: str) -> bool:
        """检查设备是否已连接"""
        return device_id in self.active_connections

    def _now(self) -> str:
        """获取当前时间字符串（ISO 格式）"""
        return datetime.utcnow().isoformat()


# ============================================================================
# 全局连接管理器单例
# 重要：其他模块必须通过此导入使用，不要创建新实例
# ============================================================================
manager = ConnectionManager()
