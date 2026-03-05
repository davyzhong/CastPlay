"""
文件工具模块
包含文件上传、MD5 计算、缩略图生成等文件相关功能
"""
import os
import hashlib
from pathlib import Path
from typing import Tuple, Optional
from PIL import Image
import mimetypes

from app.config import settings
from app.utils.logger import logger


def get_file_extension(filename: str) -> str:
    """
    获取文件扩展名（小写）

    Args:
        filename: 文件名

    Returns:
        小写的文件扩展名（不含点）
    """
    return Path(filename).suffix.lower().lstrip('.')


def get_mime_type(filename: str) -> str:
    """
    获取文件的 MIME 类型

    Args:
        filename: 文件名

    Returns:
        MIME 类型字符串
    """
    mime_type, _ = mimetypes.guess_type(filename)
    return mime_type or 'application/octet-stream'


def calculate_md5(file_path: str) -> str:
    """
    计算文件的 MD5 哈希值

    Args:
        file_path: 文件路径

    Returns:
        MD5 哈希值（32位十六进制字符串）
    """
    md5_hash = hashlib.md5()
    with open(file_path, "rb") as f:
        # 分块读取文件，避免大文件内存问题
        for chunk in iter(lambda: f.read(8192), b""):
            md5_hash.update(chunk)
    return md5_hash.hexdigest()


def validate_file_type(filename: str, file_type: str) -> bool:
    """
    验证文件类型是否允许

    Args:
        filename: 文件名
        file_type: 期望的文件类型 (image/video/ppt)

    Returns:
        是否允许上传
    """
    ext = get_file_extension(filename)

    allowed_types = {
        'image': settings.ALLOWED_IMAGE_TYPES,
        'video': settings.ALLOWED_VIDEO_TYPES,
        'ppt': settings.ALLOWED_PPT_TYPES
    }

    return ext in allowed_types.get(file_type, [])


def generate_thumbnail(file_path: str, output_path: str, size: Tuple[int, int] = (320, 240)) -> bool:
    """
    生成图片缩略图

    Args:
        file_path: 原始文件路径
        output_path: 缩略图输出路径
        size: 缩略图尺寸 (宽度, 高度)

    Returns:
        是否成功
    """
    try:
        # 打开图片
        with Image.open(file_path) as img:
            # 转换为 RGB (处理 PNG 等格式）
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')

            # 生成缩略图（保持宽高比）
            img.thumbnail(size, Image.Resampling.LANCZOS)

            # 确保输出目录存在
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)

            # 保存缩略图
            img.save(output_path, 'JPEG', quality=85)

        logger.info(f"Thumbnail generated: {output_path}")
        return True

    except Exception as e:
        logger.error(f"Failed to generate thumbnail: {e}")
        return False


def get_unique_filename(upload_dir: str, filename: str) -> str:
    """
    获取唯一的文件名（避免文件名冲突）

    Args:
        upload_dir: 上传目录
        filename: 原始文件名

    Returns:
        唯一的文件名
    """
    path = Path(upload_dir) / filename

    if not path.exists():
        return filename

    # 文件已存在，添加数字后缀
    stem = path.stem
    suffix = path.suffix
    counter = 1

    while True:
        new_name = f"{stem}_{counter}{suffix}"
        new_path = Path(upload_dir) / new_name
        if not new_path.exists():
            return new_name
        counter += 1


def safe_delete_file(file_path: str) -> bool:
    """
    安全删除文件

    Args:
        file_path: 文件路径

    Returns:
        是否成功
    """
    try:
        path = Path(file_path)
        if path.exists():
            path.unlink()
            logger.info(f"File deleted: {file_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to delete file {file_path}: {e}")
        return False


def format_file_size(size_bytes: int) -> str:
    """
    格式化文件大小

    Args:
        size_bytes: 字节数

    Returns:
        格式化后的字符串（如 "10.5 MB"）
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"
