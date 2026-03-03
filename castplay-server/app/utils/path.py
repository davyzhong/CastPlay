"""
路径安全工具模块

提供安全的文件路径解析功能，防止路径遍历攻击
"""
import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# 延迟导入避免循环依赖
_BASE_DIR: Optional[str] = None
_ALLOWED_DIRS: Optional[list] = None


def _init_dirs():
    """延迟初始化目录配置"""
    global _BASE_DIR, _ALLOWED_DIRS
    if _BASE_DIR is None:
        from config import BASE_DIR
        _BASE_DIR = BASE_DIR
        _ALLOWED_DIRS = [
            os.path.join(_BASE_DIR, 'storage'),
            os.path.join(_BASE_DIR, 'storage/uploads'),
            os.path.join(_BASE_DIR, 'storage/converted'),
            os.path.join(_BASE_DIR, 'storage/thumbnails'),
        ]


class PathSecurityError(Exception):
    """路径安全检查失败异常"""
    pass


def resolve_file_path(relative_path: str, check_exists: bool = False) -> str:
    """
    安全地解析文件路径，防止路径遍历攻击

    Args:
        relative_path: 数据库中存储的路径（可能是相对路径或绝对路径）
        check_exists: 是否检查文件存在

    Returns:
        规范化的绝对路径

    Raises:
        PathSecurityError: 路径不在允许的目录范围内
        FileNotFoundError: check_exists=True 时文件不存在
    """
    _init_dirs()

    if not relative_path:
        raise PathSecurityError("Empty path provided")

    # 如果是绝对路径，直接使用；否则拼接基准目录
    if os.path.isabs(relative_path):
        full_path = relative_path
    else:
        full_path = os.path.join(_BASE_DIR, relative_path)

    # 规范化路径，消除 ../ ./ 等
    full_path = os.path.normpath(os.path.abspath(full_path))

    # 安全检查：确保路径在允许的目录内
    is_allowed = any(
        full_path.startswith(os.path.abspath(allowed_dir))
        for allowed_dir in _ALLOWED_DIRS
    )

    if not is_allowed:
        logger.warning(
            f"Path security violation attempt: {relative_path} -> {full_path}")
        raise PathSecurityError(f"Access to path not allowed: {relative_path}")

    # 可选：检查文件是否存在
    if check_exists and not os.path.exists(full_path):
        raise FileNotFoundError(f"File not found: {full_path}")

    return full_path


def is_path_safe(relative_path: str) -> bool:
    """
    检查路径是否安全（不抛异常版本）

    Args:
        relative_path: 要检查的路径

    Returns:
        True 如果路径安全，否则 False
    """
    try:
        resolve_file_path(relative_path)
        return True
    except (PathSecurityError, Exception):
        return False


def get_relative_path(absolute_path: str) -> str:
    """
    将绝对路径转换为相对于 BASE_DIR 的相对路径

    Args:
        absolute_path: 绝对路径

    Returns:
        相对路径
    """
    _init_dirs()
    abs_path = os.path.abspath(absolute_path)
    if abs_path.startswith(_BASE_DIR):
        return os.path.relpath(abs_path, _BASE_DIR)
    return absolute_path


def ensure_dir_exists(dir_path: str) -> str:
    """
    确保目录存在，不存在则创建

    Args:
        dir_path: 目录路径

    Returns:
        目录的绝对路径
    """
    _init_dirs()

    # 解析并验证路径
    full_path = resolve_file_path(dir_path)

    if not os.path.exists(full_path):
        os.makedirs(full_path, exist_ok=True)
        logger.info(f"Created directory: {full_path}")

    return full_path
