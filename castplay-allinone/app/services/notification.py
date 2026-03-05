"""
通知服务
封装 WebSocket 通知功能
"""
from app.websocket.handler import ConnectionManager

# 使用全局连接管理器
connection_manager = ConnectionManager()


class NotificationService:
    """
    通知服务

    封装设备通知相关功能
    """

    @staticmethod
    async def notify_playlist_update(device_id: int):
        """
        通知设备播放列表更新

        Args:
            device_id: 设备数据库 ID
        """
        await connection_manager.notify_playlist_update(device_id)

    @staticmethod
    async def notify_schedule_update(device_id: int):
        """
        通知设备定时配置更新

        Args:
            device_id: 设备数据库 ID
        """
        await connection_manager.notify_schedule_update(device_id)

    @staticmethod
    async def notify_force_sync(device_id: int):
        """
        通知设备强制同步

        Args:
            device_id: 设备数据库 ID
        """
        await connection_manager.notify_force_sync(device_id)

    @staticmethod
    async def notify_reboot(device_id: int):
        """
        通知设备重启

        Args:
            device_id: 设备数据库 ID
        """
        await connection_manager.notify_reboot(device_id)

    @staticmethod
    async def broadcast_to_all(message: dict):
        """
        广播消息到所有设备

        Args:
            message: 消息内容
        """
        await connection_manager.broadcast(message)

    @staticmethod
    def is_device_online(device_id: str) -> bool:
        """
        检查设备是否在线

        Args:
            device_id: 设备 ID

        Returns:
            是否在线
        """
        return connection_manager.is_connected(device_id)

    @staticmethod
    def get_online_devices():
        """
        获取所有在线设备

        Returns:
            在线设备 ID 列表
        """
        return connection_manager.get_connected_devices()
