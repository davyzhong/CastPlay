"""
数据库初始化脚本
创建数据库表并初始化默认管理员用户
"""
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.database import init_database, SessionLocal
from app.models import User
from app.utils.security import get_password_hash
from app.config import settings
from app.utils.logger import logger, setup_logger


def create_default_admin():
    """
    创建默认管理员用户
    """
    db = SessionLocal()

    try:
        # 检查是否已存在管理员
        existing = db.query(User).filter(User.username == settings.DEFAULT_ADMIN_USERNAME).first()

        if existing:
            logger.info(f"Default admin '{settings.DEFAULT_ADMIN_USERNAME}' already exists")
            return

        # 创建默认管理员
        admin = User(
            username=settings.DEFAULT_ADMIN_USERNAME,
            password_hash=get_password_hash(settings.DEFAULT_ADMIN_PASSWORD),
            email="admin@castplay.local",
            full_name="System Administrator",
            is_active=True,
            is_superuser=True
        )

        db.add(admin)
        db.commit()
        db.refresh(admin)

        logger.info(f"Default admin created successfully!")
        logger.info(f"Username: {settings.DEFAULT_ADMIN_USERNAME}")
        logger.info(f"Password: {settings.DEFAULT_ADMIN_PASSWORD}")
        logger.info("Please change the password after first login!")

    except Exception as e:
        logger.error(f"Failed to create default admin: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def main():
    """
    主函数
    """
    setup_logger()

    print("=" * 50)
    print("CastPlay Database Initialization")
    print("=" * 50)

    try:
        # 初始化数据库（创建表）
        init_database()

        # 创建默认管理员
        create_default_admin()

        print("\n" + "=" * 50)
        print("Database initialization completed successfully!")
        print("=" * 50)

    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
