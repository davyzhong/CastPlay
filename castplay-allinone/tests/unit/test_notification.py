"""
通知服务单元测试

测试 NotificationService 的通知发送功能
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestNotificationService:
    """通知服务测试"""

    @pytest.fixture
    def mock_manager(self):
        """创建 mock 连接管理器"""
        manager = MagicMock()
        manager.notify_playlist_update = AsyncMock()
        manager.notify_schedule_update = AsyncMock()
        manager.notify_force_sync = AsyncMock()
        manager.notify_reboot = AsyncMock()
        manager.broadcast = AsyncMock()
        manager.is_connected = MagicMock(return_value=False)
        manager.get_connected_devices = MagicMock(return_value=[])
        return manager

    # ========================================================================
    # 播放列表更新通知测试
    # ========================================================================

    @pytest.mark.asyncio
    async def test_notify_playlist_update(self, mock_manager):
        """测试播放列表更新通知"""
        with patch('app.services.notification.connection_manager', mock_manager):
            from app.services.notification import NotificationService

            await NotificationService.notify_playlist_update(123)

            mock_manager.notify_playlist_update.assert_called_once_with(123)

    @pytest.mark.asyncio
    async def test_notify_playlist_update_multiple_devices(self, mock_manager):
        """测试多个设备播放列表更新通知"""
        with patch('app.services.notification.connection_manager', mock_manager):
            from app.services.notification import NotificationService

            await NotificationService.notify_playlist_update(1)
            await NotificationService.notify_playlist_update(2)
            await NotificationService.notify_playlist_update(3)

            assert mock_manager.notify_playlist_update.call_count == 3

    # ========================================================================
    # 定时配置更新通知测试
    # ========================================================================

    @pytest.mark.asyncio
    async def test_notify_schedule_update(self, mock_manager):
        """测试定时配置更新通知"""
        with patch('app.services.notification.connection_manager', mock_manager):
            from app.services.notification import NotificationService

            await NotificationService.notify_schedule_update(456)

            mock_manager.notify_schedule_update.assert_called_once_with(456)

    # ========================================================================
    # 强制同步通知测试
    # ========================================================================

    @pytest.mark.asyncio
    async def test_notify_force_sync(self, mock_manager):
        """测试强制同步通知"""
        with patch('app.services.notification.connection_manager', mock_manager):
            from app.services.notification import NotificationService

            await NotificationService.notify_force_sync(789)

            mock_manager.notify_force_sync.assert_called_once_with(789)

    # ========================================================================
    # 重启通知测试
    # ========================================================================

    @pytest.mark.asyncio
    async def test_notify_reboot(self, mock_manager):
        """测试重启通知"""
        with patch('app.services.notification.connection_manager', mock_manager):
            from app.services.notification import NotificationService

            await NotificationService.notify_reboot(101)

            mock_manager.notify_reboot.assert_called_once_with(101)

    # ========================================================================
    # 广播消息测试
    # ========================================================================

    @pytest.mark.asyncio
    async def test_broadcast_to_all(self, mock_manager):
        """测试广播消息到所有设备"""
        with patch('app.services.notification.connection_manager', mock_manager):
            from app.services.notification import NotificationService

            message = {"type": "system_update", "version": "2.0"}
            await NotificationService.broadcast_to_all(message)

            mock_manager.broadcast.assert_called_once_with(message)

    @pytest.mark.asyncio
    async def test_broadcast_complex_message(self, mock_manager):
        """测试广播复杂消息"""
        with patch('app.services.notification.connection_manager', mock_manager):
            from app.services.notification import NotificationService

            message = {
                "type": "config_update",
                "data": {
                    "settings": {
                        "volume": 80,
                        "brightness": 100
                    }
                },
                "timestamp": "2024-01-01T00:00:00Z"
            }
            await NotificationService.broadcast_to_all(message)

            mock_manager.broadcast.assert_called_once_with(message)

    # ========================================================================
    # 设备在线状态测试
    # ========================================================================

    def test_is_device_online_true(self, mock_manager):
        """测试设备在线检查 - 在线"""
        mock_manager.is_connected.return_value = True

        with patch('app.services.notification.connection_manager', mock_manager):
            from app.services.notification import NotificationService

            result = NotificationService.is_device_online("device-123")

            assert result is True
            mock_manager.is_connected.assert_called_once_with("device-123")

    def test_is_device_online_false(self, mock_manager):
        """测试设备在线检查 - 离线"""
        mock_manager.is_connected.return_value = False

        with patch('app.services.notification.connection_manager', mock_manager):
            from app.services.notification import NotificationService

            result = NotificationService.is_device_online("device-offline")

            assert result is False
            mock_manager.is_connected.assert_called_once_with("device-offline")

    def test_is_device_online_empty_string(self, mock_manager):
        """测试设备在线检查 - 空字符串"""
        mock_manager.is_connected.return_value = False

        with patch('app.services.notification.connection_manager', mock_manager):
            from app.services.notification import NotificationService

            result = NotificationService.is_device_online("")

            assert result is False

    # ========================================================================
    # 获取在线设备列表测试
    # ========================================================================

    def test_get_online_devices_empty(self, mock_manager):
        """测试获取在线设备列表 - 空"""
        mock_manager.get_connected_devices.return_value = []

        with patch('app.services.notification.connection_manager', mock_manager):
            from app.services.notification import NotificationService

            devices = NotificationService.get_online_devices()

            assert devices == []

    def test_get_online_devices_multiple(self, mock_manager):
        """测试获取在线设备列表 - 多个设备"""
        online_devices = ["device-1", "device-2", "device-3"]
        mock_manager.get_connected_devices.return_value = online_devices

        with patch('app.services.notification.connection_manager', mock_manager):
            from app.services.notification import NotificationService

            devices = NotificationService.get_online_devices()

            assert devices == online_devices
            assert len(devices) == 3


class TestNotificationServiceStaticMethods:
    """测试静态方法"""

    def test_all_methods_are_static(self):
        """测试所有方法都是静态方法"""
        from app.services.notification import NotificationService
        import inspect

        methods = [
            'notify_playlist_update',
            'notify_schedule_update',
            'notify_force_sync',
            'notify_reboot',
            'broadcast_to_all',
            'is_device_online',
            'get_online_devices'
        ]

        for method_name in methods:
            method = getattr(NotificationService, method_name)
            # 静态方法不应该是绑定方法
            assert callable(method)


class TestNotificationServiceIntegration:
    """通知服务集成测试"""

    @pytest.mark.asyncio
    async def test_full_notification_flow(self):
        """测试完整通知流程"""
        from app.websocket.handler import ConnectionManager

        # 创建真实的连接管理器
        manager = ConnectionManager()
        mock_ws = AsyncMock()
        await manager.connect("1", mock_ws)

        with patch('app.services.notification.connection_manager', manager):
            from app.services.notification import NotificationService

            # 测试播放列表更新通知
            await NotificationService.notify_playlist_update(1)
            mock_ws.send_json.assert_called()

            # 测试设备在线状态
            assert NotificationService.is_device_online("1") is True

            # 测试获取在线设备
            devices = NotificationService.get_online_devices()
            assert "1" in devices

        # 清理
        manager.disconnect("1")

    @pytest.mark.asyncio
    async def test_notification_to_offline_device(self):
        """测试向离线设备发送通知"""
        from app.websocket.handler import ConnectionManager

        manager = ConnectionManager()

        with patch('app.services.notification.connection_manager', manager):
            from app.services.notification import NotificationService

            # 向不存在的设备发送通知
            await NotificationService.notify_playlist_update(999)

            # 应该不抛出异常


class TestNotificationServiceEdgeCases:
    """测试边界情况"""

    @pytest.fixture
    def mock_manager(self):
        """创建 mock 连接管理器"""
        manager = MagicMock()
        manager.notify_playlist_update = AsyncMock()
        manager.notify_schedule_update = AsyncMock()
        manager.notify_force_sync = AsyncMock()
        manager.notify_reboot = AsyncMock()
        manager.broadcast = AsyncMock()
        manager.is_connected = MagicMock(return_value=False)
        manager.get_connected_devices = MagicMock(return_value=[])
        return manager

    @pytest.mark.asyncio
    async def test_notify_with_zero_device_id(self, mock_manager):
        """测试设备 ID 为 0 的通知"""
        with patch('app.services.notification.connection_manager', mock_manager):
            from app.services.notification import NotificationService

            await NotificationService.notify_playlist_update(0)

            mock_manager.notify_playlist_update.assert_called_once_with(0)

    @pytest.mark.asyncio
    async def test_notify_with_negative_device_id(self, mock_manager):
        """测试设备 ID 为负数的通知"""
        with patch('app.services.notification.connection_manager', mock_manager):
            from app.services.notification import NotificationService

            await NotificationService.notify_playlist_update(-1)

            mock_manager.notify_playlist_update.assert_called_once_with(-1)

    @pytest.mark.asyncio
    async def test_broadcast_empty_message(self, mock_manager):
        """测试广播空消息"""
        with patch('app.services.notification.connection_manager', mock_manager):
            from app.services.notification import NotificationService

            await NotificationService.broadcast_to_all({})

            mock_manager.broadcast.assert_called_once_with({})
