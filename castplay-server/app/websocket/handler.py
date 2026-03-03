"""
WebSocket Event Handler

处理设备与服务器之间的实时通信
"""
import logging
from datetime import datetime
from typing import Dict, Any, Optional

from flask import request
from flask_socketio import emit, join_room, leave_room

from app import socketio, db
from app.models import Device

logger = logging.getLogger(__name__)

# 存储设备连接信息 (device_id -> session_id)
# 注意: 多实例部署时应使用 Redis 存储
connected_devices: Dict[int, str] = {}


@socketio.on('connect')
def handle_connect() -> None:
    """客户端连接"""
    logger.info(f"Client connected: {request.sid}")


@socketio.on('disconnect')
def handle_disconnect() -> None:
    """客户端断开连接"""
    # 查找断开的设备
    device_id: Optional[int] = None
    for did, sid in connected_devices.items():
        if sid == request.sid:
            device_id = did
            break

    if device_id:
        del connected_devices[device_id]
        logger.info(f"Device {device_id} disconnected")
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

    # 记录连接
    connected_devices[device.id] = request.sid

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

    if device and device.id in connected_devices:
        device.last_online = datetime.utcnow()
        device.status = 'online'
        db.session.commit()

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
