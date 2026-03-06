"""
Tests for WebSocket Event Emitter

测试 WebSocket 事件发送功能
"""
import pytest
from unittest.mock import Mock, patch, call
from app.websocket.emitter import (
    emit_playlist_update,
    emit_device_status,
    emit_media_ready,
    emit_schedule_update
)


class TestWebSocketEmitter:
    """WebSocket 事件发射器测试类"""

    @patch('app.websocket.emitter.socketio')
    def test_emit_playlist_update_with_device_id(self, mock_socketio):
        """测试发送播放列表更新事件（指定设备）"""
        # 执行
        emit_playlist_update(playlist_id=123, device_id=456)

        # 验证调用
        mock_socketio.emit.assert_called_once()
        call_args = mock_socketio.emit.call_args

        # 验证事件名
        assert call_args[0][0] == 'playlist_update'

        # 验证数据内容
        data = call_args[0][1]
        assert data['type'] == 'playlist_update'
        assert data['playlist_id'] == 123
        assert data['action'] == 'refresh'

        # 验证房间（指定设备）
        assert call_args[1]['room'] == 'device_456'

    @patch('app.websocket.emitter.socketio')
    def test_emit_playlist_update_broadcast(self, mock_socketio):
        """测试发送播放列表更新事件（广播）"""
        # 执行
        emit_playlist_update(playlist_id=789)

        # 验证房间（广播给所有设备）
        call_args = mock_socketio.emit.call_args
        assert call_args[1]['room'] == 'all_devices'

    @patch('app.websocket.emitter.socketio')
    def test_emit_device_status(self, mock_socketio):
        """测试发送设备状态更新"""
        # 执行
        emit_device_status(device_id=100, status='online')

        # 验证调用
        mock_socketio.emit.assert_called_once()
        call_args = mock_socketio.emit.call_args

        # 验证事件名
        assert call_args[0][0] == 'device_status'

        # 验证数据内容
        data = call_args[0][1]
        assert data['type'] == 'device_status'
        assert data['device_id'] == 100
        assert data['status'] == 'online'

        # 验证房间
        assert call_args[1]['room'] == 'device_100'

    @patch('app.websocket.emitter.socketio')
    def test_emit_device_status_offline(self, mock_socketio):
        """测试发送设备离线状态"""
        emit_device_status(device_id=200, status='offline')

        call_args = mock_socketio.emit.call_args
        data = call_args[0][1]
        assert data['status'] == 'offline'

    @patch('app.websocket.emitter.socketio')
    def test_emit_media_ready_image(self, mock_socketio):
        """测试发送媒体就绪事件（图片）"""
        # 执行
        emit_media_ready(media_id=500, media_type='image')

        # 验证调用
        mock_socketio.emit.assert_called_once()
        call_args = mock_socketio.emit.call_args

        # 验证事件名
        assert call_args[0][0] == 'media_ready'

        # 验证数据内容
        data = call_args[0][1]
        assert data['type'] == 'media_ready'
        assert data['media_id'] == 500
        assert data['media_type'] == 'image'

        # 验证房间（广播）
        assert call_args[1]['room'] == 'all_clients'

    @patch('app.websocket.emitter.socketio')
    def test_emit_media_ready_video(self, mock_socketio):
        """测试发送媒体就绪事件（视频）"""
        emit_media_ready(media_id=600, media_type='video')

        call_args = mock_socketio.emit.call_args
        data = call_args[0][1]
        assert data['media_type'] == 'video'

    @patch('app.websocket.emitter.socketio')
    def test_emit_media_ready_ppt(self, mock_socketio):
        """测试发送媒体就绪事件（PPT）"""
        emit_media_ready(media_id=700, media_type='ppt')

        call_args = mock_socketio.emit.call_args
        data = call_args[0][1]
        assert data['media_type'] == 'ppt'

    @patch('app.websocket.emitter.socketio')
    def test_emit_schedule_update(self, mock_socketio):
        """测试发送节目单更新事件"""
        # 执行
        emit_schedule_update(device_id=999)

        # 验证调用
        mock_socketio.emit.assert_called_once()
        call_args = mock_socketio.emit.call_args

        # 验证事件名
        assert call_args[0][0] == 'schedule_update'

        # 验证数据内容
        data = call_args[0][1]
        assert data['type'] == 'schedule_update'
        assert data['device_id'] == 999
        assert data['action'] == 'reload'

        # 验证房间
        assert call_args[1]['room'] == 'device_999'

    @patch('app.websocket.emitter.socketio')
    def test_emit_playlist_update_exception_handling(self, mock_socketio):
        """测试发送播放列表更新异常处理"""
        # Mock socketio 抛出异常
        mock_socketio.emit.side_effect = Exception("Connection error")

        # 不应抛出异常，只记录日志
        try:
            emit_playlist_update(playlist_id=111)
        except Exception:
            pytest.fail("Exception should be caught and logged")

    @patch('app.websocket.emitter.socketio')
    def test_emit_device_status_exception_handling(self, mock_socketio):
        """测试发送设备状态异常处理"""
        mock_socketio.emit.side_effect = Exception("Socket error")

        try:
            emit_device_status(device_id=222, status='error')
        except Exception:
            pytest.fail("Exception should be caught and logged")

    @patch('app.websocket.emitter.logger')
    @patch('app.websocket.emitter.socketio')
    def test_error_logging(self, mock_socketio, mock_logger, caplog):
        """测试错误日志记录"""
        # Mock 抛出异常
        mock_socketio.emit.side_effect = Exception("Test error")

        # 执行
        emit_playlist_update(playlist_id=333)

        # 验证记录了错误日志
        mock_logger.error.assert_called_once()
        call_args = mock_logger.error.call_args
        assert "Failed to emit playlist update" in call_args[0][0]


class TestWebSocketEmitterIntegration:
    """WebSocket 事件发射器集成测试"""

    @patch('app.websocket.emitter.socketio')
    def test_multiple_emits(self, mock_socketio):
        """测试连续发送多个事件"""
        # 执行多次发送
        emit_playlist_update(playlist_id=1)
        emit_device_status(device_id=2, status='online')
        emit_media_ready(media_id=3, media_type='video')
        emit_schedule_update(device_id=4)

        # 验证调用了 4 次
        assert mock_socketio.emit.call_count == 4

        # 验证每次调用的事件类型
        calls = mock_socketio.emit.call_args_list
        assert calls[0][0][0] == 'playlist_update'
        assert calls[1][0][0] == 'device_status'
        assert calls[2][0][0] == 'media_ready'
        assert calls[3][0][0] == 'schedule_update'

    @patch('app.websocket.emitter.socketio')
    def test_event_data_structure(self, mock_socketio):
        """测试事件数据结构一致性"""
        # 测试所有事件都有 type 字段
        emit_playlist_update(playlist_id=1)
        emit_device_status(device_id=2, status='online')
        emit_media_ready(media_id=3, media_type='image')
        emit_schedule_update(device_id=4)

        calls = mock_socketio.emit.call_args_list
        for call_args in calls:
            data = call_args[0][1]
            assert 'type' in data
            assert isinstance(data['type'], str)
            assert len(data['type']) > 0
