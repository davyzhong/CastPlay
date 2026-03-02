"""
Playlist API Routes
"""
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

from flask import Blueprint, request, jsonify
from sqlalchemy.orm import joinedload

from app import db
from app.models import Playlist, PlaylistItem, DevicePlaylist, MediaFile
from app.api.validators import (
    validate_json_data, max_length, is_list_of, positive_number, non_negative
)
from config import DEFAULT_PAGE_SIZE, DEFAULT_IMAGE_DISPLAY_DURATION

logger = logging.getLogger(__name__)

bp = Blueprint('playlist', __name__)


@bp.route('', methods=['POST'])
@validate_json_data(
    required_fields=['name'],
    field_types={'name': str, 'description': str},
    field_validators={'name': max_length(128)}
)
def create_playlist():
    """创建播放列表"""
    data = request.get_json()

    name = data.get('name')
    if not name:
        return jsonify({'error': 'name is required'}), 400

    playlist = Playlist(
        name=name,
        description=data.get('description', '')
    )

    db.session.add(playlist)
    db.session.commit()

    return jsonify({
        'message': 'Playlist created successfully',
        'playlist': playlist.to_dict()
    }), 201


@bp.route('', methods=['GET'])
def list_playlists():
    """播放列表列表"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', DEFAULT_PAGE_SIZE, type=int)

    pagination = Playlist.query.order_by(Playlist.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return jsonify({
        'playlists': [playlist.to_dict() for playlist in pagination.items],
        'total': pagination.total,
        'page': page,
        'per_page': per_page,
        'pages': pagination.pages
    }), 200


@bp.route('/<int:playlist_id>', methods=['GET'])
def get_playlist(playlist_id: int):
    """获取播放列表详情

    使用 joinedload 预加载关联数据，避免 N+1 查询问题
    """
    # 使用 joinedload 预加载 items -> media_file 和 devices -> device
    playlist = Playlist.query.options(
        joinedload(Playlist.items).joinedload(PlaylistItem.media_file),
        joinedload(Playlist.devices).joinedload(DevicePlaylist.device)
    ).get_or_404(playlist_id)

    result = playlist.to_dict()

    # 包含播放列表项（数据已预加载，不会产生额外查询）
    result['items'] = []
    for item in playlist.items:
        media_file = item.media_file
        if media_file:
            # 根据媒体类型和状态确定播放URL
            if media_file.file_type == 'ppt' and media_file.converted_path and media_file.status == 'ready':
                file_url = f'/api/player/media/{media_file.id}/converted'
            else:
                file_url = f'/api/media/{media_file.id}/download'

            result['items'].append({
                'id': item.id,
                'media_id': item.media_id,
                'media_name': media_file.file_name,
                'media_type': media_file.file_type,
                'display_order': item.display_order,
                'display_duration': item.display_duration,
                'status': media_file.status,
                'file_url': file_url,
                'media': {
                    'id': media_file.id,
                    'file_name': media_file.file_name,
                    'file_type': media_file.file_type,
                    'file_size': media_file.file_size,
                    'status': media_file.status,
                    'thumbnail_path': f'/api/media/{media_file.id}/thumbnail' if media_file.thumbnail_path else None,
                }
            })
        else:
            # 媒体文件已被删除，仍然返回项目信息
            result['items'].append({
                'id': item.id,
                'media_id': item.media_id,
                'media_name': f'[已删除] ID:{item.media_id}',
                'media_type': 'unknown',
                'display_order': item.display_order,
                'display_duration': item.display_duration,
                'media': None
            })

    # 包含关联的设备（数据已预加载，不会产生额外查询）
    result['devices'] = [
        {
            'device_id': dp.device_id,
            'device_name': dp.device.device_name,
            'is_active': dp.is_active
        }
        for dp in playlist.devices
    ]

    return jsonify(result), 200


@bp.route('/<int:playlist_id>', methods=['PUT'])
@validate_json_data(
    field_types={'name': str, 'description': str},
    field_validators={'name': max_length(128)}
)
def update_playlist(playlist_id: int):
    """更新播放列表"""
    playlist = Playlist.query.get_or_404(playlist_id)
    data = request.get_json()

    if 'name' in data:
        playlist.name = data['name']
    if 'description' in data:
        playlist.description = data['description']

    playlist.updated_at = datetime.utcnow()
    db.session.commit()

    return jsonify({
        'message': 'Playlist updated successfully',
        'playlist': playlist.to_dict()
    }), 200


@bp.route('/<int:playlist_id>', methods=['DELETE'])
def delete_playlist(playlist_id):
    """删除播放列表"""
    playlist = Playlist.query.get_or_404(playlist_id)

    db.session.delete(playlist)
    db.session.commit()

    return jsonify({'message': 'Playlist deleted successfully'}), 200


@bp.route('/<int:playlist_id>/items', methods=['POST'])
@validate_json_data(
    required_fields=['media_id'],
    field_types={'media_id': int, 'display_duration': int},
    field_validators={'display_duration': positive_number}
)
def add_media_to_playlist(playlist_id: int):
    """添加媒体到播放列表"""
    playlist = Playlist.query.get_or_404(playlist_id)
    data = request.get_json()

    media_id = data.get('media_id')
    if not media_id:
        return jsonify({'error': 'media_id is required'}), 400

    # 检查媒体是否存在
    media = MediaFile.query.get_or_404(media_id)

    # 获取当前最大顺序号
    max_order = db.session.query(db.func.max(PlaylistItem.display_order))\
        .filter_by(playlist_id=playlist_id).scalar() or 0

    playlist_item = PlaylistItem(
        playlist_id=playlist_id,
        media_id=media_id,
        display_order=max_order + 1,
        display_duration=data.get(
            'display_duration', DEFAULT_IMAGE_DISPLAY_DURATION)
    )

    db.session.add(playlist_item)
    db.session.commit()

    return jsonify({
        'message': 'Media added to playlist successfully',
        'item': playlist_item.to_dict()
    }), 201


@bp.route('/<int:playlist_id>/items/<int:item_id>', methods=['DELETE'])
def remove_media_from_playlist(playlist_id, item_id):
    """从播放列表移除媒体"""
    item = PlaylistItem.query.filter_by(
        id=item_id,
        playlist_id=playlist_id
    ).first_or_404()

    db.session.delete(item)
    db.session.commit()

    return jsonify({'message': 'Media removed from playlist successfully'}), 200


@bp.route('/<int:playlist_id>/items/reorder', methods=['PUT'])
@validate_json_data(
    required_fields=['items'],
    field_types={'items': list}
)
def reorder_playlist_items(playlist_id: int):
    """重新排序播放列表项"""
    playlist = Playlist.query.get_or_404(playlist_id)
    data = request.get_json()

    item_orders = data.get('items', [])  # [{'id': 1, 'order': 0}, ...]

    for item_data in item_orders:
        item = PlaylistItem.query.get(item_data['id'])
        if item and item.playlist_id == playlist_id:
            item.display_order = item_data['order']

    db.session.commit()

    return jsonify({'message': 'Playlist items reordered successfully'}), 200


@bp.route('/<int:playlist_id>/devices/<int:device_id>', methods=['POST'])
def assign_playlist_to_device(playlist_id, device_id):
    """分配播放列表到设备"""
    from app.models import Device

    playlist = Playlist.query.get_or_404(playlist_id)
    device = Device.query.get_or_404(device_id)

    # 检查是否已分配
    device_playlist = DevicePlaylist.query.filter_by(
        device_id=device_id,
        playlist_id=playlist_id
    ).first()

    if device_playlist:
        return jsonify({'message': 'Playlist already assigned to device'}), 200

    device_playlist = DevicePlaylist(
        device_id=device_id,
        playlist_id=playlist_id,
        is_active=True
    )

    db.session.add(device_playlist)
    db.session.commit()

    # 触发 WebSocket 推送
    from app.websocket.handler import notify_playlist_update
    notify_playlist_update(device_id, playlist_id)

    return jsonify({
        'message': 'Playlist assigned to device successfully',
        'assignment': device_playlist.to_dict()
    }), 201


@bp.route('/<int:playlist_id>/devices/<int:device_id>', methods=['DELETE'])
def unassign_playlist_from_device(playlist_id, device_id):
    """取消分配播放列表"""
    device_playlist = DevicePlaylist.query.filter_by(
        device_id=device_id,
        playlist_id=playlist_id
    ).first_or_404()

    db.session.delete(device_playlist)
    db.session.commit()

    return jsonify({'message': 'Playlist unassigned from device successfully'}), 200


@bp.route('/<int:playlist_id>/devices/<int:device_id>/activate', methods=['PUT'])
@validate_json_data(
    field_types={'is_active': bool}
)
def activate_playlist(playlist_id: int, device_id: int):
    """激活/停用播放列表"""
    device_playlist = DevicePlaylist.query.filter_by(
        device_id=device_id,
        playlist_id=playlist_id
    ).first_or_404()

    data = request.get_json()
    is_active = data.get('is_active', True)

    device_playlist.is_active = is_active
    db.session.commit()

    return jsonify({
        'message': f'Playlist {"activated" if is_active else "deactivated"} successfully'
    }), 200
