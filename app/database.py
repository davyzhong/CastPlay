"""
数据库连接和会话管理
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from typing import Generator
import sqlite3
from pathlib import Path

from app.config import settings

# 数据库文件路径
DB_PATH = Path(settings.DATABASE_PATH)
DB_PATH.parent.mkdir(exist_ok=True)

# SQLite 连接字符串
# 使用 check_same_thread=False 允许多线程访问
# 使用 QueuePool 连接池支持高并发
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH.absolute()}"

# 创建数据库引擎
# 使用 QueuePool 提供连接池管理，支持高并发场景
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={
        "check_same_thread": False,  # SQLite 多线程需要
    },
    poolclass=QueuePool,  # 使用队列连接池
    pool_size=20,  # 连接池大小
    max_overflow=40,  # 最大溢出连接数
    pool_pre_ping=True,  # 使用前检查连接是否有效
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

        # 数据库迁移：添加缺失的列
        cursor = conn.cursor()
        try:
            # 获取当前列
            cursor.execute("SELECT * FROM pragma_table_info WHERE name='devices'")
            columns = cursor.fetchall()
            column_names = [col[1] for col in columns]

            migrations = [
                ("is_disabled", "BOOLEAN DEFAULT 0"),
                ("device_type", "VARCHAR(50) DEFAULT 'web_browser'"),
                ("current_playlist_id", "INTEGER REFERENCES playlists(id)"),
                ("last_media_id", "INTEGER REFERENCES media_files(id)"),
                ("device_metadata", "TEXT"),
            ]

            # 检查 media_files 表是否需要添加 slide_duration 列
            cursor.execute("SELECT * FROM pragma_table_info WHERE name='media_files'")
            media_columns = cursor.fetchall()
            media_column_names = [col[1] for col in media_columns]

            media_migrations = [
                ("slide_duration", "INTEGER DEFAULT 5"),
            ]

            for col_name, col_def in media_migrations:
                if col_name not in media_column_names:
                    print(f"Adding {col_name} column to media_files table...")
                    cursor.execute(f"ALTER TABLE media_files ADD COLUMN {col_name} {col_def}")
                    conn.commit()
                    print(f"{col_name} column added successfully")

            for col_name, col_def in migrations:
                if col_name not in column_names:
                    print(f"Adding {col_name} column to devices table...")
                    cursor.execute(f"ALTER TABLE devices ADD COLUMN {col_name} {col_def}")
                    conn.commit()
                    print(f"{col_name} column added successfully")

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
