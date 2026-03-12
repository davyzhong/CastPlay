"""
日志工具模块
使用 loguru 作为日志库
"""
import sys
from pathlib import Path
from loguru import logger

from app.config import settings


def setup_logger():
    """配置日志系统"""

    # 移除默认的 logger
    logger.remove()

    # 控制台输出
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="INFO" if not settings.DEBUG else "DEBUG",
        colorize=True
    )

    # 文件输出（所有日志）
    logger.add(
        Path("logs") / "castplay.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="DEBUG",
        rotation="10 MB",
        retention="30 days",
        compression="zip"
    )

    # 文件输出（错误日志）
    logger.add(
        Path("logs") / "error.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="ERROR",
        rotation="10 MB",
        retention="90 days",
        compression="zip"
    )

    # 确保 logs 目录存在
    Path("logs").mkdir(exist_ok=True)


# 初始化日志
setup_logger()
