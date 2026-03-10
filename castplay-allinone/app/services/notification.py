"""
通知服务
封装 WebSocket 通知功能，提供高层业务通知接口

重要：使用 websocket/handler.py 中的全局 manager 实例
"""
from datetime import datetime
from typing import Optional, Dict, Any, List
from loguru import logger
from app.websocket.handler import manager as connection_manager, PlaylistNotificationData


class NotificationService:
    """
    通知服务

    封装设备通知相关功能
    使用全局 ConnectionManager 单例
    """

    # ==================== 播放列表通知 ====================

    @staticmethod
    async def notify_playlist_assigned(
        device_id: str,
        playlist_id: int,
        playlist_name: str,
        version: str,
        item_count: int = 0,
        total_size: int = 0
    ):
        """
        通知设备：播放列表已分配

        触发时机：
        - 管理员分配播放列表到设备
        - 设备首次注册时分配默认播放列表

        Args:
            device_id: 设备 UUID
            playlist_id: 播放列表 ID
            playlist_name: 播放列表名称
            version: 播放列表版本号
            item_count: 媒体项数量
            total_size: 总文件大小（字节）
        """
        data = PlaylistNotificationData(
            playlist_id=playlist_id,
            playlist_name=playlist_name,
            version=version,
            action="assign",
            item_count=item_count,
            total_size=total_size,
            priority="normal"
        )
        await connection_manager.notify_playlist_assigned(device_id, data)

    @staticmethod
    async def notify_playlist_updated(
        device_id: str,
        playlist_id: int,
        playlist_name: str,
        version: str,
        changes: Optional[Dict[str, Any]] = None,
        item_count: int = 0,
        total_size: int = 0
    ):
        """
        通知设备：播放列表内容已更新

        触发时机：
        - 添加/删除/重排媒体项
        - 修改媒体显示时长

        Args:
            device_id: 设备 UUID
            playlist_id: 播放列表 ID
            playlist_name: 播放列表名称
            version: 新版本号
            changes: 变更内容 {"added": [...], "removed": [...], "reordered": bool}
            item_count: 媒体项数量
            total_size: 总文件大小（字节）
        """
        data = PlaylistNotificationData(
            playlist_id=playlist_id,
            playlist_name=playlist_name,
            version=version,
            action="update",
            item_count=item_count,
            total_size=total_size,
            priority="normal",
            changes=changes
        )
        await connection_manager.notify_playlist_updated(device_id, data)

    @staticmethod
    async def notify_playlist_removed(device_id: str, playlist_id: int):
        """
        通知设备：播放列表已移除

        触发时机：
        - 管理员取消播放列表分配

        Args:
            device_id: 设备 UUID
            playlist_id: 播放列表 ID
        """
        await connection_manager.notify_playlist_removed(device_id, playlist_id)

    @staticmethod
    async def notify_playlist_activated(device_id: str, playlist_id: int, is_active: bool):
        """
        通知设备：播放列表激活状态变更

        触发时机：
        - 管理员激活/停用播放列表

        Args:
            device_id: 设备 UUID
            playlist_id: 播放列表 ID
            is_active: 是否激活
        """
        await connection_manager.notify_playlist_activated(device_id, playlist_id, is_active)

    # ==================== 设备配置通知 ====================

    @staticmethod
    async def notify_config_update(device_id: str, config: dict):
        """
        通知设备配置更新（如播放速度、禁用状态等）

        Args:
            device_id: 设备 UUID
            config: 配置内容
        """
        if "is_disabled" in config:
            await connection_manager.notify_device_disabled(device_id, config["is_disabled"])
        else:
            await connection_manager.notify_device_config_updated(device_id, config)

    @staticmethod
    async def notify_schedule_update(device_id: str, schedule: dict = None):
        """
        通知设备定时配置更新

        Args:
            device_id: 设备 UUID
            schedule: 定时配置（可选，不提供则设备会主动拉取）
        """
        await connection_manager.notify_schedule_updated(device_id, schedule or {})

    @staticmethod
    async def notify_force_sync(device_id: str):
        """
        通知设备强制同步

        Args:
            device_id: 设备 UUID
        """
        await connection_manager.notify_force_sync(device_id)

    @staticmethod
    async def notify_reboot(device_id: str):
        """
        通知设备重启

        Args:
            device_id: 设备 UUID
        """
        await connection_manager.notify_reboot(device_id)

    # ==================== 播放控制 ====================

    @staticmethod
    async def send_pause(device_id: str):
        """发送暂停指令"""
        await connection_manager.send_pause_command(device_id)

    @staticmethod
    async def send_resume(device_id: str):
        """发送恢复播放指令"""
        await connection_manager.send_resume_command(device_id)

    @staticmethod
    async def send_volume(device_id: str, volume: int):
        """发送音量调节指令"""
        await connection_manager.send_volume_command(device_id, volume)

    @staticmethod
    async def send_reload(device_id: str):
        """发送重新加载指令"""
        await connection_manager.send_reload_command(device_id)

    @staticmethod
    async def send_next(device_id: str):
        """发送下一个指令"""
        await connection_manager.send_next_command(device_id)

    @staticmethod
    async def send_prev(device_id: str):
        """发送上一个指令"""
        await connection_manager.send_prev_command(device_id)

    @staticmethod
    async def send_switch_playlist(device_id: str, playlist_id: int):
        """发送切换播放列表指令"""
        await connection_manager.send_switch_playlist_command(device_id, playlist_id)

    # ==================== 广播 ====================

    @staticmethod
    async def broadcast_to_all(message: dict):
        """
        广播消息到所有设备

        Args:
            message: 消息内容
        """
        await connection_manager.broadcast(message)

    # ==================== 状态查询 ====================

    @staticmethod
    def is_device_online(device_id: str) -> bool:
        """
        检查设备是否在线

        Args:
            device_id: 设备 UUID

        Returns:
            是否在线
        """
        return connection_manager.is_connected(device_id)

    @staticmethod
    def get_online_devices() -> List[str]:
        """
        获取所有在线设备

        Returns:
            在线设备 ID 列表
        """
        return connection_manager.get_connected_devices()

    @staticmethod
    def register_device_mapping(db_id: int, device_id: str):
        """
        注册设备 ID 映射

        Args:
            db_id: 设备数据库 ID
            device_id: 设备 UUID
        """
        connection_manager.register_device_mapping(db_id, device_id)

    @staticmethod
    def get_device_id_by_db_id(db_id: int) -> Optional[str]:
        """
        根据数据库 ID 获取设备 UUID

        Args:
            db_id: 设备数据库 ID

        Returns:
            设备 UUID，如果未连接则返回 None
        """
        return connection_manager.get_device_id_by_db_id(db_id)

    # ==================== 兼容旧版 API（deprecated） ====================

    @staticmethod
    async def notify_playlist_update(device_id: int):
        """
        [已弃用] 通知设备播放列表更新

        请使用 notify_playlist_assigned 或 notify_playlist_updated
        """
        logger.warning(f"notify_playlist_update is deprecated, use notify_playlist_assigned instead")
        # 尝试通过映射发送
        uuid = connection_manager.get_device_id_by_db_id(device_id)
        if uuid:
            await connection_manager.notify_force_sync(uuid)
        else:
            # 兼容旧版：直接用字符串 ID
            await connection_manager.notify_force_sync(str(device_id))

    @staticmethod
    async def notify_schedule_update_legacy(device_id: int):
        """
        [已弃用] 通知设备定时配置更新

        请使用 notify_schedule_update
        """
        logger.warning(f"notify_schedule_update_legacy is deprecated")
        uuid = connection_manager.get_device_id_by_db_id(device_id)
        if uuid:
            await connection_manager.notify_schedule_updated(uuid, {})
        else:
            await connection_manager.notify_schedule_updated(str(device_id), {})
