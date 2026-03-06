"""
播放端功能增强 - 数据库迁移脚本
新增：下载任务表、通知日志表、清理计划表
"""
from app.config import settings
from app.database import engine
from sqlalchemy import create_engine, text
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))


def check_table_exists(table_name: str) -> bool:
    """检查表是否存在"""
    with engine.connect() as conn:
        result = conn.execute(text(f"""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='{table_name}'
        """))
        return result.fetchone() is not None


def check_index_exists(index_name: str) -> bool:
    """检查索引是否存在"""
    with engine.connect() as conn:
        result = conn.execute(text(f"""
            SELECT name FROM sqlite_master
            WHERE type='index' AND name='{index_name}'
        """))
        return result.fetchone() is not None


def migrate():
    """执行数据库迁移"""
    print("🚀 Starting database migration...")

    with engine.connect() as conn:
        # 1. 创建播放列表下载任务表
        if not check_table_exists('playlist_download_tasks'):
            print("Creating table: playlist_download_tasks...")
            conn.execute(text("""
                CREATE TABLE playlist_download_tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    device_id VARCHAR(50) NOT NULL,
                    playlist_id INTEGER NOT NULL,
                    status VARCHAR(20) NOT NULL DEFAULT 'pending',
                    retry_count INTEGER DEFAULT 0,
                    error_message TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    completed_at DATETIME,
                    FOREIGN KEY (playlist_id) REFERENCES playlists(id)
                )
            """))
            print("✓ playlist_download_tasks table created")

            # 创建索引
            conn.execute(text("""
                CREATE INDEX idx_download_tasks_device
                ON playlist_download_tasks(device_id, status)
            """))
            print("✓ Indexes created for playlist_download_tasks")
        else:
            print("✓ playlist_download_tasks table already exists")

        # 2. 创建设备通知日志表
        if not check_table_exists('device_notification_logs'):
            print("Creating table: device_notification_logs...")
            conn.execute(text("""
                CREATE TABLE device_notification_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    device_id VARCHAR(50) NOT NULL,
                    notification_type VARCHAR(50) NOT NULL,
                    message TEXT,
                    playlist_id INTEGER,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """))
            print("✓ device_notification_logs table created")

            # 创建索引
            conn.execute(text("""
                CREATE INDEX idx_notification_device ON device_notification_logs(device_id)
            """))
            conn.execute(text("""
                CREATE INDEX idx_notification_type ON device_notification_logs(notification_type)
            """))
            print("✓ Indexes created for device_notification_logs")
        else:
            print("✓ device_notification_logs table already exists")

        # 3. 创建播放列表清理计划表
        if not check_table_exists('playlist_cleanup_schedule'):
            print("Creating table: playlist_cleanup_schedule...")
            conn.execute(text("""
                CREATE TABLE playlist_cleanup_schedule (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    playlist_id INTEGER NOT NULL,
                    scheduled_time DATETIME NOT NULL,
                    executed BOOLEAN DEFAULT FALSE,
                    executed_at DATETIME,
                    FOREIGN KEY (playlist_id) REFERENCES playlists(id)
                )
            """))
            print("✓ playlist_cleanup_schedule table created")
        else:
            print("✓ playlist_cleanup_schedule table already exists")

        # 提交事务
        conn.commit()

    print("\n✅ Migration completed successfully!")


if __name__ == "__main__":
    migrate()
