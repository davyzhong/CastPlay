"""
数据库备份脚本
自动备份数据库文件到 backups 目录
"""
import shutil
from pathlib import Path
from datetime import datetime
import sys

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from app.config import settings
from app.utils.logger import logger, setup_logger


def backup_database():
    """
    备份数据库文件
    """
    db_path = Path(settings.DATABASE_PATH)
    backup_dir = settings.BACKUPS_DIR

    # 确保备份目录存在
    backup_dir.mkdir(exist_ok=True)

    # 检查数据库文件是否存在
    if not db_path.exists():
        logger.error(f"Database file not found: {db_path}")
        return False

    # 生成备份文件名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"castplay_{timestamp}.db"
    backup_path = backup_dir / backup_name

    try:
        # 复制数据库文件
        shutil.copy2(db_path, backup_path)

        # 获取文件大小
        file_size = backup_path.stat().st_size

        logger.info(f"Database backed up to: {backup_path}")
        logger.info(f"Backup size: {file_size:,} bytes")

        # 清理旧的备份（保留最近 7 天）
        cleanup_old_backups(backup_dir, days=7)

        return True

    except Exception as e:
        logger.error(f"Failed to backup database: {e}")
        return False


def cleanup_old_backups(backup_dir: Path, days: int = 7):
    """
    清理旧的备份文件

    Args:
        backup_dir: 备份目录
        days: 保留天数
    """
    cutoff_time = datetime.now().timestamp() - (days * 24 * 60 * 60)
    cleaned_count = 0

    for backup_file in backup_dir.glob("castplay_*.db"):
        file_mtime = backup_file.stat().st_mtime
        if file_mtime < cutoff_time:
            backup_file.unlink()
            cleaned_count += 1
            logger.info(f"Deleted old backup: {backup_file.name}")

    if cleaned_count > 0:
        logger.info(f"Cleaned up {cleaned_count} old backup(s)")


def main():
    """
    主函数
    """
    setup_logger()

    print("=" * 50)
    print("CastPlay Database Backup")
    print("=" * 50)

    if backup_database():
        print("\nBackup completed successfully!")
    else:
        print("\nBackup failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
