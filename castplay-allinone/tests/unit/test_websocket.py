"""
WebSocket 连接管理器单元测试

测试 WebSocket 连接管理、消息发送和广播功能
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime


class TestConnectionManager:
    """WebSocket 连接管理器测试"""

    @pytest.fixture
    def manager(self):
        """创建管理器实例"""
        from app.websocket.handler import ConnectionManager
        return ConnectionManager()

    @pytest.fixture
    def mock_websocket(self):
        """创建 mock WebSocket"""
        ws = AsyncMock()
        ws.accept = AsyncMock()
        ws.send_json = AsyncMock()
        return ws

    # ========================================================================
    # 连接管理测试
    # ========================================================================

    @pytest.mark.asyncio
    async def test_connect(self, manager, mock_websocket):
        """测试设备连接"""
        await manager.connect("device-123", mock_websocket)

        assert "device-123" in manager.active_connections
        assert manager.active_connections["device-123"] == mock_websocket
        assert "device-123" in manager.rooms
        mock_websocket.accept.assert_called_once()

    @pytest.mark.asyncio
    async def test_connect_multiple_devices(self, manager):
        """测试多个设备连接"""
        ws1 = AsyncMock()
        ws2 = AsyncMock()
        ws3 = AsyncMock()

        await manager.connect("device-1", ws1)
        await manager.connect("device-2", ws2)
        await manager.connect("device-3", ws3)

        assert len(manager.active_connections) == 3
        assert len(manager.rooms) == 3

    def test_disconnect(self, manager, mock_websocket):
        """测试设备断开连接"""
        manager.active_connections["device-123"] = mock_websocket
        manager.rooms["device-123"] = ["device-123"]

        manager.disconnect("device-123")

        assert "device-123" not in manager.active_connections
        assert "device-123" not in manager.rooms

    def test_disconnect_nonexistent_device(self, manager):
        """测试断开不存在的设备"""
        # 应该不会抛出异常
        manager.disconnect("nonexistent-device")
        assert len(manager.active_connections) == 0

    def test_disconnect_partial_state(self, manager, mock_websocket):
        """测试设备在部分状态下断开（只有连接没有房间）"""
        manager.active_connections["device-123"] = mock_websocket
        # 没有房间

        manager.disconnect("device-123")

        assert "device-123" not in manager.active_connections

    # ========================================================================
    # 消息发送测试
    # ========================================================================

    @pytest.mark.asyncio
    async def test_send_to_device(self, manager, mock_websocket):
        """测试发送消息到指定设备"""
        manager.active_connections["device-123"] = mock_websocket

        message = {"type": "update", "data": "test"}
        await manager.send_to_device("device-123", message)

        mock_websocket.send_json.assert_called_once_with(message)

    @pytest.mark.asyncio
    async def test_send_to_disconnected_device(self, manager):
        """测试发送消息到已断开的设备"""
        # 设备不在连接列表中
        await manager.send_to_device("nonexistent-device", {"type": "test"})
        # 应该不抛出异常

    @pytest.mark.asyncio
    async def test_send_to_device_with_failure(self, manager, mock_websocket):
        """测试发送消息失败时的处理"""
        mock_websocket.send_json.side_effect = Exception("Connection closed")
        manager.active_connections["device-123"] = mock_websocket

        await manager.send_to_device("device-123", {"type": "test"})

        # 设备应该被清理
        assert "device-123" not in manager.active_connections
        assert "device-123" not in manager.rooms

    @pytest.mark.asyncio
    async def test_send_to_multiple_devices(self, manager):
        """测试发送消息到多个设备"""
        ws1 = AsyncMock()
        ws2 = AsyncMock()
        manager.active_connections = {
            "device-1": ws1,
            "device-2": ws2
        }

        message = {"type": "broadcast", "data": "test"}
        await manager.send_to_device("device-1", message)
        await manager.send_to_device("device-2", message)

        ws1.send_json.assert_called_once_with(message)
        ws2.send_json.assert_called_once_with(message)

    # ========================================================================
    # 广播测试
    # ========================================================================

    @pytest.mark.asyncio
    async def test_broadcast_to_all(self, manager):
        """测试广播到所有设备"""
        ws1 = AsyncMock()
        ws2 = AsyncMock()
        ws3 = AsyncMock()
        manager.active_connections = {
            "device-1": ws1,
            "device-2": ws2,
            "device-3": ws3
        }

        message = {"type": "broadcast", "data": "all"}
        await manager.broadcast(message)

        ws1.send_json.assert_called_once_with(message)
        ws2.send_json.assert_called_once_with(message)
        ws3.send_json.assert_called_once_with(message)

    @pytest.mark.asyncio
    async def test_broadcast_to_room(self, manager):
        """测试广播到指定房间"""
        ws1 = AsyncMock()
        ws2 = AsyncMock()
        ws3 = AsyncMock()
        manager.active_connections = {
            "device-1": ws1,
            "device-2": ws2,
            "device-3": ws3
        }
        manager.rooms = {
            "room-a": ["device-1", "device-2"],
            "room-b": ["device-3"]
        }

        message = {"type": "room-message"}
        await manager.broadcast(message, room="room-a")

        ws1.send_json.assert_called_once_with(message)
        ws2.send_json.assert_called_once_with(message)
        ws3.send_json.assert_not_called()

    @pytest.mark.asyncio
    async def test_broadcast_to_empty_room(self, manager):
        """测试广播到空房间"""
        manager.rooms = {}

        await manager.broadcast({"type": "test"}, room="empty-room")
        # 应该不抛出异常

    @pytest.mark.asyncio
    async def test_broadcast_with_failure(self, manager):
        """测试广播时部分设备失败"""
        ws1 = AsyncMock()
        ws2 = AsyncMock()
        ws2.send_json.side_effect = Exception("Send failed")
        ws3 = AsyncMock()

        manager.active_connections = {
            "device-1": ws1,
            "device-2": ws2,
            "device-3": ws3
        }

        await manager.broadcast({"type": "test"})

        # 所有设备的 send_json 都应该被调用
        ws1.send_json.assert_called_once()
        ws2.send_json.assert_called_once()
        ws3.send_json.assert_called_once()

    @pytest.mark.asyncio
    async def test_broadcast_no_connections(self, manager):
        """测试没有连接时广播"""
        manager.active_connections = {}

        await manager.broadcast({"type": "test"})
        # 应该不抛出异常

    # ========================================================================
    # 通知功能测试
    # ========================================================================

    @pytest.mark.asyncio
    async def test_notify_playlist_update(self, manager, mock_websocket):
        """测试播放列表更新通知"""
        manager.active_connections["1"] = mock_websocket

        await manager.notify_playlist_update(1)

        mock_websocket.send_json.assert_called_once()
        call_args = mock_websocket.send_json.call_args[0][0]
        assert call_args["event"] == "playlist_update"
        assert call_args["action"] == "update"
        assert "timestamp" in call_args

    @pytest.mark.asyncio
    async def test_notify_schedule_update(self, manager, mock_websocket):
        """测试定时配置更新通知"""
        manager.active_connections["1"] = mock_websocket

        await manager.notify_schedule_update(1)

        mock_websocket.send_json.assert_called_once()
        call_args = mock_websocket.send_json.call_args[0][0]
        assert call_args["event"] == "schedule_update"
        assert call_args["action"] == "update"

    @pytest.mark.asyncio
    async def test_notify_force_sync(self, manager, mock_websocket):
        """测试强制同步通知"""
        manager.active_connections["1"] = mock_websocket

        await manager.notify_force_sync(1)

        mock_websocket.send_json.assert_called_once()
        call_args = mock_websocket.send_json.call_args[0][0]
        assert call_args["event"] == "force_sync"
        assert call_args["action"] == "sync"

    @pytest.mark.asyncio
    async def test_notify_reboot(self, manager, mock_websocket):
        """测试重启通知"""
        manager.active_connections["1"] = mock_websocket

        await manager.notify_reboot(1)

        mock_websocket.send_json.assert_called_once()
        call_args = mock_websocket.send_json.call_args[0][0]
        assert call_args["event"] == "reboot"
        assert call_args["action"] == "reboot"

    # ========================================================================
    # 工具方法测试
    # ========================================================================

    def test_get_connected_devices(self, manager):
        """测试获取已连接设备列表"""
        manager.active_connections = {
            "device-1": MagicMock(),
            "device-2": MagicMock(),
            "device-3": MagicMock()
        }

        devices = manager.get_connected_devices()

        assert len(devices) == 3
        assert "device-1" in devices
        assert "device-2" in devices
        assert "device-3" in devices

    def test_get_connected_devices_empty(self, manager):
        """测试获取空连接列表"""
        devices = manager.get_connected_devices()
        assert devices == []

    def test_is_connected_true(self, manager, mock_websocket):
        """测试检查已连接设备"""
        manager.active_connections["device-123"] = mock_websocket

        assert manager.is_connected("device-123") is True

    def test_is_connected_false(self, manager):
        """测试检查未连接设备"""
        assert manager.is_connected("nonexistent-device") is False

    def test_now_returns_iso_format(self, manager):
        """测试时间戳返回 ISO 格式"""
        timestamp = manager._now()

        # 检查是否是有效的 ISO 格式字符串
        assert isinstance(timestamp, str)
        # 尝试解析时间戳
        parsed = datetime.fromisoformat(timestamp)
        assert isinstance(parsed, datetime)


class TestConnectionManagerIntegration:
    """连接管理器集成测试"""

    @pytest.fixture
    def manager(self):
        """创建管理器实例"""
        from app.websocket.handler import ConnectionManager
        return ConnectionManager()

    @pytest.mark.asyncio
    async def test_full_connection_lifecycle(self, manager):
        """测试完整的连接生命周期"""
        ws = AsyncMock()

        # 连接
        await manager.connect("device-123", ws)
        assert manager.is_connected("device-123")

        # 发送消息
        await manager.send_to_device("device-123", {"type": "test"})
        ws.send_json.assert_called_once()

        # 断开
        manager.disconnect("device-123")
        assert not manager.is_connected("device-123")

    @pytest.mark.asyncio
    async def test_reconnect_updates_connection(self, manager):
        """测试重连更新连接"""
        ws1 = AsyncMock()
        ws2 = AsyncMock()

        # 第一次连接
        await manager.connect("device-123", ws1)
        assert manager.active_connections["device-123"] == ws1

        # 重连（应该替换旧连接）
        await manager.connect("device-123", ws2)
        assert manager.active_connections["device-123"] == ws2
        assert len(manager.active_connections) == 1

    @pytest.mark.asyncio
    async def test_concurrent_operations(self, manager):
        """测试并发操作"""
        import asyncio

        websockets = [AsyncMock() for _ in range(5)]

        # 并发连接
        await asyncio.gather(*[
            manager.connect(f"device-{i}", ws)
            for i, ws in enumerate(websockets)
        ])

        assert len(manager.active_connections) == 5

        # 并发发送消息
        await asyncio.gather(*[
            manager.send_to_device(f"device-{i}", {"type": "test"})
            for i in range(5)
        ])

        # 所有 WebSocket 应该收到消息
        for ws in websockets:
            ws.send_json.assert_called_once()


class TestGlobalManager:
    """全局管理器实例测试"""

    def test_global_manager_exists(self):
        """测试全局管理器实例存在"""
        from app.websocket.handler import manager

        assert manager is not None
        assert hasattr(manager, 'active_connections')
        assert hasattr(manager, 'rooms')
        assert hasattr(manager, 'connect')
        assert hasattr(manager, 'disconnect')
        assert hasattr(manager, 'broadcast')
