"""
Device API Routes
"""
import logging
import uuid
from datetime import datetime, time
from typing import Dict, List, Any, Optional

from flask import Blueprint, request, jsonify
from sqlalchemy.orm import joinedload

from app import db
from app.models import Device, DeviceSchedule
from app.models.playlist import DevicePlaylist
from config import DEFAULT_PAGE_SIZE

logger = logging.getLogger(__name__)

bp = Blueprint('device', __name__)


@bp.route('', methods=['POST'])
def create_device():
    """创建新设备"""
    data = request.get_json() or {}

    # 生成唯一设备ID
    device_id = data.get('device_id') or str(uuid.uuid4())[
        :12].upper().replace('-', '')
    device_name = data.get('device_name') or f'Device-{device_id[:8]}'
    timezone = data.get('timezone', 'Asia/Shanghai')

    # 检查设备ID是否已存在
    existing = Device.query.filter_by(device_id=device_id).first()
    if existing:
        return jsonify({'error': '设备ID已存在'}), 400

    device = Device(
        device_id=device_id,
        device_name=device_name,
        timezone=timezone,
        status='offline'
    )
    db.session.add(device)
    db.session.commit()

    return jsonify({
        'message': 'Device created successfully',
        'device': device.to_dict()
    }), 201


@bp.route('/register', methods=['POST'])
def register_device():
    """设备注册"""
    data = request.get_json()

    device_id = data.get('device_id')

    if not device_id:
        return jsonify({'error': 'device_id is required'}), 400

    device_name = data.get('device_name', f'Device-{device_id[:8]}')
    timezone = data.get('timezone', 'Asia/Shanghai')

    # 检查设备是否已存在
    device = Device.query.filter_by(device_id=device_id).first()

    if device:
        # 更新设备信息
        device.device_name = device_name
        device.timezone = timezone
        device.last_online = datetime.utcnow()
        device.status = 'online'
    else:
        # 创建新设备
        device = Device(
            device_id=device_id,
            device_name=device_name,
            timezone=timezone,
            last_online=datetime.utcnow(),
            status='online'
        )
        db.session.add(device)

    db.session.commit()

    return jsonify({
        'message': 'Device registered successfully',
        'device': device.to_dict()
    }), 200


@bp.route('/<int:device_id>/heartbeat', methods=['PUT'])
def heartbeat(device_id):
    """心跳上报"""
    device = Device.query.get_or_404(device_id)

    device.last_online = datetime.utcnow()
    device.status = 'online'
    db.session.commit()

    return jsonify({
        'message': 'Heartbeat received',
        'device': device.to_dict()
    }), 200


@bp.route('', methods=['GET'])
def list_devices():
    """设备列表"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', DEFAULT_PAGE_SIZE, type=int)
    status = request.args.get('status')

    query = Device.query

    if status:
        query = query.filter_by(status=status)

    pagination = query.order_by(Device.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return jsonify({
        'devices': [device.to_dict() for device in pagination.items],
        'total': pagination.total,
        'page': page,
        'per_page': per_page,
        'pages': pagination.pages
    }), 200


@bp.route('/<int:device_id>', methods=['GET'])
def get_device(device_id: int):
    """获取设备详情

    使用 joinedload 预加载关联数据，避免 N+1 查询问题
    """
    # 预加载 schedule 和 playlists -> playlist
    device = Device.query.options(
        joinedload(Device.schedule),
        joinedload(Device.playlists).joinedload(DevicePlaylist.playlist)
    ).get_or_404(device_id)

    result = device.to_dict()

    # 包含定时配置（已预加载）
    if device.schedule:
        result['schedule'] = device.schedule.to_dict()

    # 包含播放列表（已预加载）
    result['playlists'] = [
        {
            'id': dp.playlist_id,
            'name': dp.playlist.name,
            'is_active': dp.is_active
        }
        for dp in device.playlists
    ]

    return jsonify(result), 200


@bp.route('/<int:device_id>', methods=['PUT'])
def update_device(device_id):
    """更新设备信息"""
    device = Device.query.get_or_404(device_id)
    data = request.get_json()

    if 'device_name' in data:
        device.device_name = data['device_name']
    if 'timezone' in data:
        device.timezone = data['timezone']
    if 'status' in data:
        device.status = data['status']

    device.updated_at = datetime.utcnow()
    db.session.commit()

    return jsonify({
        'message': 'Device updated successfully',
        'device': device.to_dict()
    }), 200


@bp.route('/<int:device_id>', methods=['DELETE'])
def delete_device(device_id):
    """删除设备"""
    device = Device.query.get_or_404(device_id)

    db.session.delete(device)
    db.session.commit()

    return jsonify({'message': 'Device deleted successfully'}), 200


@bp.route('/<int:device_id>/schedule', methods=['POST', 'PUT'])
def set_schedule(device_id):
    """设置定时配置"""
    device = Device.query.get_or_404(device_id)
    data = request.get_json()

    power_on_time = None
    power_off_time = None

    if data.get('power_on_time'):
        h, m = map(int, data['power_on_time'].split(':'))
        power_on_time = time(h, m)

    if data.get('power_off_time'):
        h, m = map(int, data['power_off_time'].split(':'))
        power_off_time = time(h, m)

    if device.schedule:
        # 更新现有配置
        schedule = device.schedule
        schedule.power_on_time = power_on_time
        schedule.power_off_time = power_off_time
        schedule.is_enabled = data.get('is_enabled', True)
        schedule.weekdays = ','.join(
            map(str, data.get('weekdays', [1, 2, 3, 4, 5, 6, 7])))
    else:
        # 创建新配置
        schedule = DeviceSchedule(
            device_id=device.id,
            power_on_time=power_on_time,
            power_off_time=power_off_time,
            is_enabled=data.get('is_enabled', True),
            weekdays=','.join(
                map(str, data.get('weekdays', [1, 2, 3, 4, 5, 6, 7])))
        )
        db.session.add(schedule)

    db.session.commit()

    # 触发定时配置更新通知
    from app.websocket.handler import notify_schedule_update
    notify_schedule_update(device.id, schedule.to_dict())

    return jsonify({
        'message': 'Schedule set successfully',
        'schedule': schedule.to_dict()
    }), 200


@bp.route('/<int:device_id>/schedule', methods=['GET'])
def get_schedule(device_id):
    """查询定时配置"""
    device = Device.query.get_or_404(device_id)

    if not device.schedule:
        return jsonify({'message': 'No schedule configured'}), 404

    return jsonify(device.schedule.to_dict()), 200
