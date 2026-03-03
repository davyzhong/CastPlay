"""
WebSocket Handler Tests
"""
import pytest
from unittest.mock import Mock, patch, MagicMock


class TestWebSocketHandler:
    """WebSocket 事件处理测试"""

    def test_notify_playlist_update(self, app):
        """测试通知播放列表更新"""
        with app.app_context():
            with patch('app.websocket.handler.socketio') as mock_socketio:
                from app.websocket.handler import notify_playlist_update

                notify_playlist_update(device_id=1, playlist_id=10)

                mock_socketio.emit.assert_called_once()
                call_args = mock_socketio.emit.call_args
                assert call_args[0][0] == 'playlist_update'
                assert call_args[1]['room'] == 'device_1'
                assert call_args[0][1]['playlist_id'] == 10

    def test_notify_schedule_update(self, app):
        """测试通知定时配置更新"""
        with app.app_context():
            with patch('app.websocket.handler.socketio') as mock_socketio:
                from app.websocket.handler import notify_schedule_update

                schedule_data = {
                    'power_on_time': '08:00',
                    'power_off_time': '18:00'
                }
                notify_schedule_update(
                    device_id=1, schedule_data=schedule_data)

                mock_socketio.emit.assert_called_once()
                call_args = mock_socketio.emit.call_args
                assert call_args[0][0] == 'schedule_update'
                assert call_args[1]['room'] == 'device_1'
                assert call_args[0][1]['schedule'] == schedule_data

    def test_notify_force_sync(self, app):
        """测试强制同步通知"""
        with app.app_context():
            with patch('app.websocket.handler.socketio') as mock_socketio:
                from app.websocket.handler import notify_force_sync

                notify_force_sync(device_id=1)

                mock_socketio.emit.assert_called_once()
                call_args = mock_socketio.emit.call_args
                assert call_args[0][0] == 'force_sync'
                assert call_args[1]['room'] == 'device_1'
                assert call_args[0][1]['event'] == 'force_sync'

    def test_notify_reboot(self, app):
        """测试重启通知"""
        with app.app_context():
            with patch('app.websocket.handler.socketio') as mock_socketio:
                from app.websocket.handler import notify_reboot

                notify_reboot(device_id=1)

                mock_socketio.emit.assert_called_once()
                call_args = mock_socketio.emit.call_args
                assert call_args[0][0] == 'reboot'
                assert call_args[1]['room'] == 'device_1'
                assert call_args[0][1]['event'] == 'reboot'

    def test_broadcast_to_all(self, app):
        """测试广播消息"""
        with app.app_context():
            with patch('app.websocket.handler.socketio') as mock_socketio:
                from app.websocket.handler import broadcast_to_all

                broadcast_to_all('test_event', {'message': 'test'})

                mock_socketio.emit.assert_called_once_with(
                    'test_event',
                    {'message': 'test'},
                    broadcast=True
                )


class TestWebSocketEvents:
    """WebSocket 事件测试"""

    def test_connected_devices_storage(self, app):
        """测试连接设备存储（使用 device_store）"""
        with app.app_context():
            from app.services.redis_client import device_store

            # 清空连接设备（内存 fallback）
            device_store._local_cache.clear()

            # 添加设备
            device_store.set_connected(1, 'sid-1')
            device_store.set_connected(2, 'sid-2')

            assert device_store.is_connected(1)
            assert device_store.is_connected(2)
            assert device_store.get_session_id(1) == 'sid-1'

    def test_handle_device_register_missing_device_id(self, app):
        """测试设备注册缺少 device_id"""
        with app.app_context():
            with patch('app.websocket.handler.emit') as mock_emit:
                from app.websocket.handler import handle_device_register

                handle_device_register({})

                mock_emit.assert_called_once()
                call_args = mock_emit.call_args
                assert call_args[0][0] == 'error'
                assert 'device_id is required' in call_args[0][1]['message']

    def test_handle_device_register_device_not_found(self, app):
        """测试设备注册设备未找到"""
        with app.app_context():
            with patch('app.websocket.handler.emit') as mock_emit:
                from app.websocket.handler import handle_device_register

                handle_device_register({'device_id': 'NON-EXIST-WS'})

                mock_emit.assert_called_once()
                call_args = mock_emit.call_args
                assert call_args[0][0] == 'error'
                assert 'not registered' in call_args[0][1]['message']

    def test_handle_heartbeat_success(self, app):
        """测试心跳处理成功"""
        from app.models import Device
        from app import db

        with app.app_context():
            # 创建设备
            device = Device(
                device_id='WS-HB-001',
                device_name='Heartbeat Test Device',
                status='online'
            )
            db.session.add(device)
            db.session.commit()

            device_db_id = device.id

            with patch('app.websocket.handler.emit') as mock_emit:
                from app.services.redis_client import device_store
                from app.websocket import handler

                # 模拟设备已连接（使用 device_store）
                device_store.set_connected(device_db_id, 'hb-sid-001')

                handler.handle_heartbeat({'device_id': device_db_id})

                # 验证发送心跳确认
                mock_emit.assert_called_once()
                call_args = mock_emit.call_args
                assert call_args[0][0] == 'heartbeat_ack'

                # 清理
                device_store.remove_connected(device_db_id)

    def test_handle_heartbeat_device_not_connected(self, app):
        """测试心跳处理设备未连接"""
        with app.app_context():
            with patch('app.websocket.handler.emit') as mock_emit:
                from app.services.redis_client import device_store
                from app.websocket import handler

                # 清空连接设备
                device_store._local_cache.clear()

                handler.handle_heartbeat({'device_id': 999})

                # 不应发送心跳确认
                mock_emit.assert_not_called()

    def test_handle_heartbeat_no_device_id(self, app):
        """测试心跳处理没有 device_id"""
        with app.app_context():
            with patch('app.websocket.handler.emit') as mock_emit:
                from app.websocket.handler import handle_heartbeat

                handle_heartbeat({})

                # 不应发送心跳确认
                mock_emit.assert_not_called()
