"""
数据库迁移脚本：添加播放端状态采集字段

执行方式：
python scripts/migrate_player_status.py
"""
from app.database import engine
from app.config import settings
from sqlalchemy import create_engine, text, inspect
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))


def check_column_exists(table_name: str, column_name: str) -> bool:
    """检查列是否已存在"""
    inspector = inspect(engine)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns


def migrate():
    """执行数据库迁移"""
    print("Starting database migration...")

    with engine.connect() as conn:
        # 1. 添加 device_type 字段
        if not check_column_exists('devices', 'device_type'):
            print("Adding device_type column...")
            conn.execute(text(
                "ALTER TABLE devices ADD COLUMN device_type VARCHAR(50) DEFAULT 'web_browser'"
            ))
            print("✓ device_type column added")
        else:
            print("✓ device_type column already exists")

        # 2. 添加 current_playlist_id 字段
        if not check_column_exists('devices', 'current_playlist_id'):
            print("Adding current_playlist_id column...")
            conn.execute(text(
                "ALTER TABLE devices ADD COLUMN current_playlist_id INTEGER"
            ))
            print("✓ current_playlist_id column added")
        else:
            print("✓ current_playlist_id column already exists")

        # 3. 添加 last_media_id 字段
        if not check_column_exists('devices', 'last_media_id'):
            print("Adding last_media_id column...")
            conn.execute(text(
                "ALTER TABLE devices ADD COLUMN last_media_id INTEGER"
            ))
            print("✓ last_media_id column added")
        else:
            print("✓ last_media_id column already exists")

        # 4. 添加 device_metadata 字段（原 metadata，因与 SQLAlchemy 保留字冲突改名）
        if not check_column_exists('devices', 'device_metadata'):
            print("Adding device_metadata column...")
            conn.execute(text(
                "ALTER TABLE devices ADD COLUMN device_metadata TEXT"
            ))
            print("✓ device_metadata column added")
        else:
            print("✓ device_metadata column already exists")

        # 5. 创建索引（如果不存在）
        print("Creating indexes...")

        try:
            conn.execute(text(
                "CREATE INDEX IF NOT EXISTS idx_devices_device_type ON devices(device_type)"
            ))
            conn.execute(text(
                "CREATE INDEX IF NOT EXISTS idx_devices_current_playlist ON devices(current_playlist_id)"
            ))
            conn.execute(text(
                "CREATE INDEX IF NOT EXISTS idx_devices_last_media ON devices(last_media_id)"
            ))
            print("✓ Indexes created")
        except Exception as e:
            print(f"⚠ Error creating indexes: {e}")

        conn.commit()

    print("\n✅ Migration completed successfully!")


if __name__ == "__main__":
    try:
        migrate()
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
