"""
播放列表调度 - 数据库迁移脚本
新增：playlist_schedules 表
"""
from app.config import settings
from app.database import engine
from sqlalchemy import text
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
    print("🚀 Starting playlist_schedules migration...")

    with engine.connect() as conn:
        # 创建播放列表调度表
        if not check_table_exists('playlist_schedules'):
            print("Creating table: playlist_schedules...")
            conn.execute(text("""
                CREATE TABLE playlist_schedules (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    device_id INTEGER NOT NULL,
                    playlist_id INTEGER NOT NULL,
                    start_time TIME NOT NULL,
                    end_time TIME NOT NULL,
                    days_of_week INTEGER NOT NULL DEFAULT 127,
                    enabled BOOLEAN NOT NULL DEFAULT 1,
                    priority INTEGER NOT NULL DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (device_id) REFERENCES devices(id) ON DELETE CASCADE,
                    FOREIGN KEY (playlist_id) REFERENCES playlists(id) ON DELETE CASCADE
                )
            """))
            print("✓ playlist_schedules table created")

            # 创建索引
            conn.execute(text("""
                CREATE INDEX idx_schedule_device
                ON playlist_schedules(device_id)
            """))
            conn.execute(text("""
                CREATE INDEX idx_schedule_enabled
                ON playlist_schedules(enabled)
            """))
            conn.execute(text("""
                CREATE INDEX idx_schedule_time
                ON playlist_schedules(start_time, end_time)
            """))
            print("✓ Indexes created for playlist_schedules")
        else:
            print("✓ playlist_schedules table already exists")

        # 提交事务
        conn.commit()

    print("\n✅ Migration completed successfully!")


if __name__ == "__main__":
    migrate()
