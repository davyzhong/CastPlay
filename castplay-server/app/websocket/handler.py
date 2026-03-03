"""
WebSocket Event Handler

处理设备与服务器之间的实时通信

特性：
- 支持 Redis 存储设备连接状态（多实例部署）
- 无 Redis 时自动降级到内存存储
"""
import logging
from datetime import datetime
from typing import Dict, Any, Optional

from flask import request
from flask_socketio import emit, join_room, leave_room

from app import socketio, db
from app.models import Device
from app.services.redis_client import device_store

logger = logging.getLogger(__name__)


@socketio.on('connect')
def handle_connect() -> None:
    """客户端连接"""
    logger.info(f"Client connected: {request.sid}")


@socketio.on('disconnect')
def handle_disconnect() -> None:
    """客户端断开连接"""
    # 查找断开的设备
    device_id = device_store.find_device_by_session(request.sid)

    if device_id:
        device_store.remove_connected(device_id)
        logger.info(f"Device {device_id} disconnected")

        # 更新设备状态
        device = Device.query.get(device_id)
        if device:
            device.status = 'offline'
            db.session.commit()
    else:
        logger.debug(f"Client disconnected: {request.sid}")


@socketio.on('device_register')
def handle_device_register(data):
    """设备注册 WebSocket 连接"""
    device_id = data.get('device_id')

    if not device_id:
        emit('error', {'event': 'error', 'message': 'device_id is required'})
        return

    # 查询设备是否存在
    device = Device.query.filter_by(device_id=device_id).first()

    if not device:
        emit('error', {'event': 'error', 'message': 'Device not registered'})
        return

    # 加入设备房间
    join_room(f"device_{device.id}")

    # 记录连接（使用 Redis 或内存存储）
    device_store.set_connected(device.id, request.sid)

    # 更新设备在线状态
    device.last_online = datetime.utcnow()
    device.status = 'online'
    db.session.commit()

    emit('registered', {
        'event': 'registered',
        'message': 'Device registered successfully',
        'device_id': device.id
    })

    logger.info(f"Device {device_id} registered with sid {request.sid}")


@socketio.on('heartbeat')
def handle_heartbeat(data):
    """
    心跳

    注意: device_id 可能是字符串(device_id)或整数(数据库ID)
    """
    device_id_input = data.get('device_id')
    if not device_id_input:
        return

    # 处理两种情况：
    # 1. 如果是数字（数据库 ID），直接查询
    # 2. 如果是字符串（设备 device_id），按字段查询
    if isinstance(device_id_input, int):
        device = Device.query.get(device_id_input)
    else:
        device = Device.query.filter_by(device_id=str(device_id_input)).first()

    if device and device_store.is_connected(device.id):
        device.last_online = datetime.utcnow()
        device.status = 'online'
        db.session.commit()

        # 刷新心跳时间
        device_store.refresh_heartbeat(device.id)

        emit('heartbeat_ack', {
            'event': 'heartbeat_ack',
            'timestamp': datetime.utcnow().isoformat()
        })


def notify_playlist_update(device_id, playlist_id):
    """通知设备播放列表更新"""
    socketio.emit(
        'playlist_update',
        {
            'event': 'playlist_update',
            'playlist_id': playlist_id,
            'action': 'update',
            'timestamp': datetime.utcnow().isoformat()
        },
        room=f"device_{device_id}"
    )


def notify_schedule_update(device_id, schedule_data):
    """通知设备定时配置更新"""
    socketio.emit(
        'schedule_update',
        {
            'event': 'schedule_update',
            'schedule': schedule_data,
            'action': 'update',
            'timestamp': datetime.utcnow().isoformat()
        },
        room=f"device_{device_id}"
    )


def notify_force_sync(device_id):
    """强制设备同步"""
    socketio.emit(
        'force_sync',
        {
            'event': 'force_sync',
            'action': 'sync',
            'timestamp': datetime.utcnow().isoformat()
        },
        room=f"device_{device_id}"
    )


def notify_reboot(device_id):
    """通知设备重启"""
    socketio.emit(
        'reboot',
        {
            'event': 'reboot',
            'action': 'reboot',
            'timestamp': datetime.utcnow().isoformat()
        },
        room=f"device_{device_id}"
    )


def broadcast_to_all(event, data):
    """广播消息到所有设备"""
    socketio.emit(event, data, broadcast=True)
