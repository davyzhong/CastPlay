"""
PPT Conversion Tasks
"""
import os
import subprocess
import logging
from typing import Dict, Any, Optional

from flask import current_app

from app import db
from app.models import MediaFile
from app.services.converter import PPTConverter
from app.tasks.celery_app import celery

logger = logging.getLogger(__name__)


@celery.task(bind=True)
def convert_ppt_to_video(self, media_id: int) -> Dict[str, Any]:
    """
    异步转换 PPT 为视频

    Args:
        media_id: MediaFile 的 ID
    """
    try:
        # 获取媒体文件记录
        media = MediaFile.query.get(media_id)
        if not media:
            raise Exception(f"Media file {media_id} not found")

        if media.file_type != 'ppt':
            raise Exception(f"Media file {media_id} is not a PPT file")

        # 更新状态为处理中
        media.status = 'processing'
        db.session.commit()

        # 初始化转换器
        converter = PPTConverter(
            libreoffice_path=current_app.config.get('LIBREOFFICE_PATH'),
            ffmpeg_path=current_app.config.get('FFMPEG_PATH')
        )

        # 获取输出目录
        converted_dir = current_app.config.get('CONVERTED_FOLDER',
                                               os.path.join(current_app.root_path, '../storage/converted'))
        os.makedirs(converted_dir, exist_ok=True)

        # 执行转换
        duration_per_slide = current_app.config.get('PPT_FRAME_DURATION', 5)
        video_path = converter.convert_to_video(
            media.file_path,
            converted_dir,
            duration_per_slide
        )

        # 生成缩略图
        thumbnail_dir = current_app.config.get('THUMBNAIL_FOLDER',
                                               os.path.join(current_app.root_path, '../storage/thumbnails'))
        os.makedirs(thumbnail_dir, exist_ok=True)

        thumbnail_path = os.path.join(
            thumbnail_dir,
            f"{os.path.splitext(os.path.basename(video_path))[0]}_thumb.jpg"
        )
        converter.generate_thumbnail(video_path, thumbnail_path)

        # 计算 MD5
        md5_hash = converter.calculate_md5(video_path)

        # 获取视频时长
        import subprocess
        try:
            result = subprocess.run(
                [converter.ffmpeg_path, '-i', video_path],
                capture_output=True,
                text=True
            )
            # 从 ffmpeg 输出中提取时长（简化实现）
            duration = None
            for line in result.stderr.split('\n'):
                if 'Duration:' in line:
                    duration_str = line.split('Duration:')[
                        1].split(',')[0].strip()
                    h, m, s = duration_str.split(':')
                    duration = int(h) * 3600 + int(m) * 60 + float(s)
                    break
        except Exception:
            duration = None

        # 更新数据库记录
        media.converted_path = video_path
        media.thumbnail_path = thumbnail_path
        media.md5_hash = md5_hash
        media.duration = int(duration) if duration else None
        media.status = 'ready'
        db.session.commit()

        return {
            'status': 'success',
            'media_id': media_id,
            'converted_path': video_path
        }

    except Exception as e:
        # 更新状态为失败
        media = MediaFile.query.get(media_id)
        if media:
            media.status = 'failed'
            db.session.commit()

        # 记录错误
        self.update_state(
            state='FAILURE',
            meta={'error': str(e)}
        )
        raise
