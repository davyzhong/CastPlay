"""
Media API Routes
"""
import logging
import os
import subprocess
from datetime import datetime
from typing import Optional, Set

from flask import Blueprint, request, jsonify, send_file, current_app
from werkzeug.utils import secure_filename

from app import db
from app.models import MediaFile, MediaFolder
from app.utils.path import resolve_file_path, PathSecurityError, get_relative_path
from config import DEFAULT_PAGE_SIZE, DEFAULT_IMAGE_DISPLAY_DURATION, BASE_DIR

logger = logging.getLogger(__name__)

bp = Blueprint('media', __name__)


def allowed_file(filename, file_type):
    """检查文件扩展名是否允许"""
    if '.' not in filename:
        return False

    ext = filename.rsplit('.', 1)[1].lower()
    allowed_extensions = current_app.config['ALLOWED_EXTENSIONS'].get(
        file_type, set())

    return ext in allowed_extensions


@bp.route('/upload', methods=['POST'])
def upload_media():
    """上传媒体文件"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    file_type = request.form.get('file_type')  # image/video/ppt

    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if not file_type or file_type not in ['image', 'video', 'ppt']:
        return jsonify({'error': 'Invalid file_type'}), 400

    if not allowed_file(file.filename, file_type):
        return jsonify({'error': f'File type not allowed for {file_type}'}), 400

    # 获取文件夹ID
    folder_id = request.form.get('folder_id', type=int)

    # 保存原始文件名用于显示
    original_filename = file.filename

    # 使用安全文件名保存文件（处理中文等特殊字符）
    safe_filename = secure_filename(file.filename)
    # 如果 secure_filename 返回空或只有扩展名，使用时间戳作为文件名
    if not safe_filename or safe_filename == original_filename.rsplit('.', 1)[-1]:
        ext = original_filename.rsplit(
            '.', 1)[-1] if '.' in original_filename else ''
        safe_filename = f"file_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.{ext}" if ext else f"file_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    unique_filename = f"{timestamp}_{safe_filename}"

    upload_folder = current_app.config['UPLOAD_FOLDER']
    file_path = os.path.join(upload_folder, unique_filename)
    file.save(file_path)

    file_size = os.path.getsize(file_path)

    # 创建数据库记录（使用原始文件名用于显示）
    media_file = MediaFile(
        file_name=original_filename,
        file_type=file_type,
        file_path=file_path,
        file_size=file_size,
        folder_id=folder_id,
        status='ready' if file_type != 'ppt' else 'processing'
    )

    db.session.add(media_file)
    db.session.commit()

    # 如果是PPT，尝试触发转换任务
    if file_type == 'ppt':
        try:
            from app.tasks.convert import convert_ppt_to_video
            convert_ppt_to_video.delay(media_file.id)
        except Exception as e:
            # Celery 未运行时忽略错误，文件已保存，状态保持 processing
            logger.warning(
                f"Celery task failed (worker may not be running): {e}")

    return jsonify({
        'message': 'File uploaded successfully',
        'media': media_file.to_dict()
    }), 201


@bp.route('', methods=['GET'])
def list_media():
    """媒体文件列表"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', DEFAULT_PAGE_SIZE, type=int)
    file_type = request.args.get('file_type')
    status = request.args.get('status')
    folder_id = request.args.get('folder_id')  # 'null' 表示根目录，数字表示文件夹ID

    query = MediaFile.query

    if file_type:
        query = query.filter_by(file_type=file_type)
    if status:
        query = query.filter_by(status=status)

    # 文件夹过滤
    if folder_id is not None:
        if folder_id == 'null' or folder_id == '':
            # 根目录，显示未分类文件
            query = query.filter(MediaFile.folder_id.is_(None))
        else:
            try:
                query = query.filter_by(folder_id=int(folder_id))
            except ValueError:
                pass

    pagination = query.order_by(MediaFile.upload_time.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return jsonify({
        'media': [media.to_dict() for media in pagination.items],
        'total': pagination.total,
        'page': page,
        'per_page': per_page,
        'pages': pagination.pages
    }), 200


@bp.route('/<int:media_id>', methods=['GET'])
def get_media(media_id):
    """获取媒体文件详情"""
    media = MediaFile.query.get_or_404(media_id)
    return jsonify(media.to_dict()), 200


@bp.route('/<int:media_id>', methods=['PUT'])
def update_media(media_id):
    """更新媒体文件信息"""
    media = MediaFile.query.get_or_404(media_id)
    data = request.get_json()

    if 'file_name' in data:
        media.file_name = data['file_name']

    if 'folder_id' in data:
        media.folder_id = data['folder_id']

    db.session.commit()

    return jsonify({
        'message': 'Media updated successfully',
        'media': media.to_dict()
    }), 200


@bp.route('/<int:media_id>', methods=['DELETE'])
def delete_media(media_id):
    """删除媒体文件"""
    media = MediaFile.query.get_or_404(media_id)

    # 删除物理文件（使用安全路径解析）
    try:
        file_path = resolve_file_path(media.file_path)
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"Deleted file: {file_path}")
    except PathSecurityError as e:
        logger.warning(f"Cannot delete file due to security check: {e}")
    except Exception as e:
        logger.error(f"Error deleting file: {e}")

    # 删除转换后的文件
    if media.converted_path:
        try:
            converted_path = resolve_file_path(media.converted_path)
            if os.path.exists(converted_path):
                os.remove(converted_path)
                logger.info(f"Deleted converted file: {converted_path}")
        except (PathSecurityError, Exception) as e:
            logger.warning(f"Cannot delete converted file: {e}")

    # 删除缩略图
    if media.thumbnail_path:
        try:
            thumbnail_path = resolve_file_path(media.thumbnail_path)
            if os.path.exists(thumbnail_path):
                os.remove(thumbnail_path)
                logger.info(f"Deleted thumbnail: {thumbnail_path}")
        except (PathSecurityError, Exception) as e:
            logger.warning(f"Cannot delete thumbnail: {e}")

    db.session.delete(media)
    db.session.commit()

    return jsonify({'message': 'Media deleted successfully'}), 200


@bp.route('/<int:media_id>/download', methods=['GET'])
def download_media(media_id):
    """下载媒体文件"""
    media = MediaFile.query.get_or_404(media_id)

    # 如果是PPT且已转换，返回转换后的视频
    if media.file_type == 'ppt' and media.converted_path:
        file_path = resolve_file_path(media.converted_path)
    else:
        file_path = resolve_file_path(media.file_path)

    if not os.path.exists(file_path):
        return jsonify({'error': 'File not found'}), 404

    return send_file(
        file_path,
        as_attachment=True,
        download_name=os.path.basename(file_path)
    )


@bp.route('/<int:media_id>/thumbnail', methods=['GET'])
def get_thumbnail(media_id):
    """获取缩略图 - 支持自动 fallback"""
    media = MediaFile.query.get_or_404(media_id)

    # 1. 优先使用已生成的缩略图
    if media.thumbnail_path:
        thumbnail_path = resolve_file_path(media.thumbnail_path)
        if os.path.exists(thumbnail_path):
            return send_file(thumbnail_path, mimetype='image/jpeg')

    # 2. 图片类型：直接返回原图
    if media.file_type == 'image':
        file_path = resolve_file_path(media.file_path)
        if os.path.exists(file_path):
            ext = os.path.splitext(media.file_name)[1].lower()
            mime_map = {
                '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
                '.png': 'image/png', '.gif': 'image/gif',
                '.bmp': 'image/bmp', '.webp': 'image/webp'
            }
            mime = mime_map.get(ext, 'image/jpeg')
            return send_file(file_path, mimetype=mime)

    # 3. PPT/视频类型：从视频实时截图
    if media.file_type in ('ppt', 'video'):
        if media.file_type == 'ppt' and media.converted_path:
            source_path = resolve_file_path(media.converted_path)
        elif media.file_type == 'video':
            source_path = resolve_file_path(media.file_path)
        else:
            return jsonify({'error': 'No source for thumbnail'}), 404

        if not os.path.exists(source_path):
            return jsonify({'error': 'Source file not found'}), 404

        try:
            from config import BASE_DIR
            import subprocess
            thumbnail_dir = os.path.join(BASE_DIR, 'storage/thumbnails')
            os.makedirs(thumbnail_dir, exist_ok=True)
            thumb_path = os.path.join(thumbnail_dir, f'thumb_{media_id}.jpg')
            ffmpeg_path = current_app.config.get(
                'FFMPEG_PATH', '/usr/bin/ffmpeg')
            cmd = [ffmpeg_path, '-y', '-i', source_path,
                   '-ss', '00:00:01', '-vframes', '1',
                   '-vf', 'scale=1280:-1', thumb_path]
            result = subprocess.run(cmd, capture_output=True, timeout=30)
            if result.returncode == 0 and os.path.exists(thumb_path):
                rel_path = os.path.relpath(thumb_path, BASE_DIR)
                media.thumbnail_path = rel_path
                db.session.commit()
                return send_file(thumb_path, mimetype='image/jpeg')
        except Exception as e:
            current_app.logger.error(
                f'Failed to generate thumbnail for media {media_id}: {e}')

    return jsonify({'error': 'Thumbnail not available'}), 404
