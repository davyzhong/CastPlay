"""
数据库连接和会话管理
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from typing import Generator
import sqlite3
from pathlib import Path

from app.config import settings

# 数据库文件路径
DB_PATH = Path(settings.DATABASE_PATH)
DB_PATH.parent.mkdir(exist_ok=True)

# SQLite 连接字符串
# 使用 check_same_thread=False 允许多线程访问
# 使用 StaticPool 连接池提高性能
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH.absolute()}"

# 创建数据库引擎
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={
        "check_same_thread": False,  # SQLite 多线程需要
    },
    poolclass=StaticPool,  # 使用静态连接池
    echo=settings.DEBUG,  # 开发模式下打印 SQL
)

# 创建 Session 工厂
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


def init_database():
    """初始化数据库，创建所有表"""
    from app.models import Base
    Base.metadata.create_all(bind=engine)

    # 启用 SQLite WAL 模式提高并发性能
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute('PRAGMA journal_mode=WAL')
        conn.execute('PRAGMA synchronous=NORMAL')
        conn.execute('PRAGMA cache_size=-64000')  # 64MB cache

        # 数据库迁移：添加 is_disabled 列（如果不存在）
        cursor = conn.cursor()
        try:
            # 检查 is_disabled 列是否存在
            cursor.execute("SELECT * FROM pragma_table_info WHERE name='devices'")
            columns = cursor.fetchall()
            column_names = [col[1] for col in columns]

            if 'is_disabled' not in column_names:
                print("Adding is_disabled column to devices table...")
                cursor.execute("ALTER TABLE devices ADD COLUMN is_disabled BOOLEAN DEFAULT 0")
                conn.commit()
                print("is_disabled column added successfully")

            # 移除 playback_speed 列（如果存在且不再需要）
            # 注意：SQLite 不支持 DROP COLUMN，保留该列但不使用

        except Exception as e:
            print(f"Migration check: {e}")

    print(f"Database initialized at {DB_PATH}")


def get_db() -> Generator[Session, None, None]:
    """
    获取数据库会话（依赖注入用）

    Yields:
        Session: 数据库会话
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def reset_database():
    """重置数据库（删除所有表）"""
    from app.models import Base
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("Database reset successfully")
