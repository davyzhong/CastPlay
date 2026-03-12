"""
文件工具模块
包含文件上传、MD5 计算、缩略图生成等文件相关功能
"""
import os
import hashlib
import struct
from pathlib import Path
from typing import Tuple, Optional, Dict, Set
from PIL import Image
import mimetypes

from app.config import settings
from app.utils.logger import logger


# ============================================================================
# 文件 Magic Number (文件签名) 定义
# 用于验证文件实际类型，防止恶意文件伪装
# ============================================================================
FILE_SIGNATURES: Dict[str, Set[bytes]] = {
    # 图片格式
    'jpg': {b'\xff\xd8\xff'},
    'jpeg': {b'\xff\xd8\xff'},
    'png': {b'\x89PNG\r\n\x1a\n'},
    'gif': {b'GIF87a', b'GIF89a'},
    'bmp': {b'BM'},

    # 视频格式 - MP4/MOV 使用 ftyp box 检测（在 validate_file_content 中特殊处理）
    # 这些签名仅作为备用检测
    'mp4': set(),  # 通过 ftyp box 检测
    'avi': {b'RIFF'},
    'mov': set(),  # 通过 ftyp box 检测（与 MP4 相同结构）
    'mkv': {b'\x1a\x45\xdf\xa3'},
    'flv': {b'FLV'},

    # PPT 格式 (Office 文件)
    'ppt': {b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1'},  # OLE 复合文档
    'pptx': {b'PK\x03\x04', b'PK\x05\x06', b'PK\x07\x08'},  # ZIP 格式
}

# MIME 类型映射
MIME_TYPE_MAP: Dict[str, str] = {
    'jpg': 'image/jpeg',
    'jpeg': 'image/jpeg',
    'png': 'image/png',
    'gif': 'image/gif',
    'bmp': 'image/bmp',
    'mp4': 'video/mp4',
    'avi': 'video/x-msvideo',
    'mov': 'video/quicktime',
    'mkv': 'video/x-matroska',
    'flv': 'video/x-flv',
    'ppt': 'application/vnd.ms-powerpoint',
    'pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
}


def validate_file_content(contents: bytes, claimed_type: str) -> Tuple[bool, str]:
    """
    验证文件实际内容类型（通过 Magic Number）

    Args:
        contents: 文件二进制内容
        claimed_type: 声称的文件类型 (image/video/ppt)

    Returns:
        (是否验证通过, 错误消息)
    """
    if len(contents) < 8:
        return False, "File too small to validate"

    # 获取该类型允许的扩展名
    type_to_ext = {
        'image': settings.ALLOWED_IMAGE_TYPES,
        'video': settings.ALLOWED_VIDEO_TYPES,
        'ppt': settings.ALLOWED_PPT_TYPES
    }
    allowed_extensions = type_to_ext.get(claimed_type, [])

    # 检查文件签名
    for ext in allowed_extensions:
        signatures = FILE_SIGNATURES.get(ext, set())
        for sig in signatures:
            if contents[:len(sig)] == sig:
                return True, ""

    # MP4/MOV 文件：检测 ftyp box（ISO Base Media File Format）
    # MP4 文件结构：[4字节大小][ftyp][brand][...]
    # 常见 brand: mp41, mp42, isom, M4V, MSNV, qt, etc.
    if claimed_type == 'video' and ('mp4' in allowed_extensions or 'mov' in allowed_extensions):
        # 检查是否有 ftyp box
        if len(contents) >= 12:
            # 尝试解析 box 大小（大端序）
            try:
                box_size = struct.unpack('>I', contents[:4])[0]
                box_type = contents[4:8]

                # ftyp box 存在说明是 ISO Base Media File Format
                if box_type == b'ftyp' and box_size >= 8:
                    # 读取 brand（ftyp 后 4 字节）
                    brand = contents[8:12]
                    # 常见的视频 brand
                    video_brands = [
                        b'mp41', b'mp42', b'isom', b'iso2', b'iso3', b'iso4', b'iso5', b'iso6',
                        b'M4V ', b'M4A ', b'MSNV', b'qt  ', b'avc1', b'f4v ', b'M4VH',
                        b' dash', b'heic', b'heix', b'mif1'
                    ]
                    # 也检查 brand 的前几个字节（某些品牌可能较短）
                    brand_lower = brand.lower() if brand else b''
                    if brand in video_brands or any(brand.startswith(b'MP4') for b in [brand]):
                        return True, ""
                    # 更宽松的检查：只要存在 ftyp box 就认为是有效的 MP4/MOV
                    if box_size >= 8 and box_size < 100000:  # 合理的 box 大小
                        logger.debug(f"MP4/MOV detected with ftyp box, brand: {brand}")
                        return True, ""
            except (struct.error, IndexError) as e:
                logger.debug(f"MP4 box parsing failed: {e}")

    # PPTX 是 ZIP 格式，需要额外检查
    if claimed_type == 'ppt' and contents[:4] == b'PK\x03\x04':
        # 可能是 PPTX，进一步检查内容
        # 简化处理：检查是否包含 [Content_Types].xml
        if b'[Content_Types]' in contents[:8192]:
            return True, ""

    # AVI 文件是 RIFF 格式，需要进一步验证
    if claimed_type == 'video' and contents[:4] == b'RIFF':
        if len(contents) >= 12 and contents[8:12] == b'AVI ':
            return True, ""

    allowed_ext_str = ', '.join(allowed_extensions)
    return False, f"File content does not match claimed type '{claimed_type}'. Allowed: {allowed_ext_str}"


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


def generate_thumbnail(file_path: str, output_path: str, size: Tuple[int, int] = (640, 480)) -> bool:
    """
    生成图片缩略图

    Args:
        file_path: 原始文件路径
        output_path: 缩略图输出路径
        size: 缩略图尺寸 (宽度, 高度)，默认 640x480

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
