"""
Player API Routes - Android 播放端专用接口
"""
from flask import Blueprint, request, jsonify, send_file, current_app
from datetime import datetime
import os
from app import db
from app.models import Device, Playlist, MediaFile

bp = Blueprint('player', __name__)


def resolve_file_path(relative_path: str) -> str:
    """
    解析文件路径，将相对路径转换为绝对路径

    Args:
        relative_path: 数据库中存储的路径（可能是相对路径）

    Returns:
        绝对路径
    """
    if os.path.isabs(relative_path):
        return relative_path

    # 使用 castplay-server 目录作为基准
    from config import BASE_DIR
    full_path = os.path.join(BASE_DIR, relative_path)
    return os.path.normpath(full_path)


@bp.route('/init', methods=['POST'])
def player_init():
    """播放端初始化"""
    data = request.get_json()
    device_id = data.get('device_id')

    if not device_id:
        return jsonify({'error': 'device_id is required'}), 400

    device = Device.query.filter_by(device_id=device_id).first()

    if not device:
        return jsonify({'error': 'Device not registered'}), 404

    # 更新设备状态
    device.last_online = datetime.utcnow()
    device.status = 'online'
    db.session.commit()

    # 获取设备的播放列表
    active_playlists = []
    for dp in device.playlists:
        if dp.is_active:
            playlist_data = {
                'id': dp.playlist_id,
                'name': dp.playlist.name,
                'version': dp.playlist.updated_at.isoformat() if dp.playlist.updated_at else dp.playlist.created_at.isoformat(),
                'items': []
            }

            for item in dp.playlist.items:
                media = item.media_file
                if not media:
                    # 跳过已删除的媒体文件
                    continue

                # 确定文件URL
                if media.file_type == 'ppt' and media.converted_path:
                    file_url = f"/api/player/media/{media.id}/converted"
                else:
                    file_url = f"/api/player/media/{media.id}/download"

                playlist_data['items'].append({
                    'id': item.id,
                    'media_id': media.id,
                    'file_name': media.file_name,
                    'file_type': media.file_type,
                    'file_url': file_url,
                    'display_order': item.display_order,
                    'display_duration': item.display_duration,
                    'file_size': media.file_size,
                    'md5_hash': media.md5_hash
                })

            active_playlists.append(playlist_data)

    # 获取定时配置
    schedule = None
    if device.schedule and device.schedule.is_enabled:
        schedule = {
            'power_on_time': device.schedule.power_on_time.isoformat() if device.schedule.power_on_time else None,
            'power_off_time': device.schedule.power_off_time.isoformat() if device.schedule.power_off_time else None,
            'weekdays': [int(d) for d in device.schedule.weekdays.split(',')],
            'timezone': device.timezone
        }

    return jsonify({
        'device': {
            'id': device.id,
            'device_id': device.device_id,
            'device_name': device.device_name,
            'timezone': device.timezone
        },
        'playlists': active_playlists,
        'schedule': schedule,
        'websocket_url': current_app.config.get('WEBSOCKET_URL', 'ws://localhost:5001')
    }), 200


@bp.route('/playlist/<int:playlist_id>/check', methods=['POST'])
def check_playlist_version(playlist_id):
    """检查播放列表版本"""
    data = request.get_json()
    local_version = data.get('version')

    playlist = Playlist.query.get_or_404(playlist_id)

    server_version = playlist.updated_at.isoformat(
    ) if playlist.updated_at else playlist.created_at.isoformat()

    needs_update = local_version != server_version

    return jsonify({
        'needs_update': needs_update,
        'server_version': server_version,
        'local_version': local_version
    }), 200


@bp.route('/media/<int:media_id>/download', methods=['GET'])
def download_media_for_player(media_id):
    """获取媒体文件（原始文件）- 支持流式播放"""
    media = MediaFile.query.get_or_404(media_id)

    # 解析文件路径
    file_path = resolve_file_path(media.file_path)

    if not os.path.exists(file_path):
        current_app.logger.error(f'File not found: {file_path}')
        return jsonify({'error': 'File not found', 'path': file_path}), 404

    # 根据文件类型设置正确的MIME类型
    mime_types = {
        'image': 'image/jpeg',
        'video': 'video/mp4',
        'ppt': 'application/vnd.ms-powerpoint'
    }

    return send_file(
        file_path,
        mimetype=mime_types.get(media.file_type, 'application/octet-stream')
    )


@bp.route('/media/<int:media_id>/converted', methods=['GET'])
def download_converted_media(media_id):
    """获取转换后的媒体文件（PPT转视频）- 支持流式播放"""
    try:
        media = MediaFile.query.get_or_404(media_id)

        if not media.converted_path:
            return jsonify({'error': 'Converted file not found', 'reason': 'no converted_path'}), 404

        # 解析文件路径
        converted_path = resolve_file_path(media.converted_path)
        current_app.logger.info(f'Resolved path: {converted_path}')

        if not os.path.exists(converted_path):
            current_app.logger.error(
                f'Converted file not found: {converted_path}')
            return jsonify({
                'error': 'Converted file not found',
                'original_path': media.converted_path,
                'resolved_path': converted_path
            }), 404

        return send_file(
            converted_path,
            mimetype='video/mp4'
        )
    except Exception as e:
        current_app.logger.exception(f'Error serving converted media: {e}')
        return jsonify({'error': str(e), 'type': type(e).__name__}), 500


@bp.route('/status', methods=['POST'])
def report_player_status():
    """播放端上报状态"""
    data = request.get_json()
    device_id = data.get('device_id')

    if not device_id:
        return jsonify({'error': 'device_id is required'}), 400

    device = Device.query.filter_by(device_id=device_id).first()

    if not device:
        return jsonify({'error': 'Device not found'}), 404

    # 更新设备状态
    device.last_online = datetime.utcnow()
    device.status = data.get('status', 'online')

    # 可以记录播放状态等信息
    # 这里可以扩展存储更详细的播放统计信息

    db.session.commit()

    return jsonify({'message': 'Status reported successfully'}), 200


@bp.route('/debug/media/<int:media_id>', methods=['GET'])
def debug_media_path(media_id):
    """调试：检查媒体文件路径"""
    media = MediaFile.query.get_or_404(media_id)

    result = {
        'id': media.id,
        'file_name': media.file_name,
        'file_type': media.file_type,
        'status': media.status,
        'file_path': media.file_path,
        'resolved_file_path': resolve_file_path(media.file_path),
        'file_exists': os.path.exists(resolve_file_path(media.file_path)),
    }

    if media.converted_path:
        result['converted_path'] = media.converted_path
        result['resolved_converted_path'] = resolve_file_path(
            media.converted_path)
        result['converted_exists'] = os.path.exists(
            resolve_file_path(media.converted_path))

    return jsonify(result), 200
