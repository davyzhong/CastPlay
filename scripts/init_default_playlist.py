"""
默认播放列表初始化脚本

系统启动时自动创建默认播放列表,包含 3 张图片：
1. 设备信息和服务端说明
2. 系统产品介绍
3. 公司宣传内容
"""
import os
import sys
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.playlist import Playlist, PlaylistItem
from app.models.media import MediaFile
from app.models.device import Device, DevicePlaylist


def create_default_media_files(db: Session, data_dir: str) -> list:
    """创建默认媒体文件记录"""
    media_dir = os.path.join(data_dir, "media")
    os.makedirs(media_dir, exist_ok=True)

    default_files = [
        {
            "file_name": "device_info.png",
            "file_type": "image",
            "description": "设备信息和服务端说明"
        },
        {
            "file_name": "system_intro.png",
            "file_type": "image",
            "description": "系统产品介绍"
        },
        {
            "file_name": "company_promo.png",
            "file_type": "image",
            "description": "公司宣传内容"
        }
    ]

    created_media = []

    for file_info in default_files:
        file_path = os.path.join(media_dir, file_info["file_name"])

        # 如果文件不存在，创建占位符文件
        if not os.path.exists(file_path):
            # 创建一个 1x1 像素的占位符图片（实际项目中应该替换为真实图片）
            with open(file_path, 'wb') as f:
                # 简单的 PNG 文件头 + 最小图片数据
                # PNG 签名
                f.write(b'\x89PNG\r\n\x1a\n')
                # IHDR chunk
                f.write(b'\x00\x00\x00\x01')  # 宽度
                f.write(b'\x00\x00\x00\x01')  # 高度
                f.write(b'\x08\x02\x00\x00\x00')  # 位深度、颜色类型等
                # CRC
                f.write(b'\x90wS\xde')
                # IDAT chunk
                f.write(b'\x00\x00\x00\x0c')  # 长度
                f.write(b'IDAT\x08\xd3\x68\x00')  # 数据
                f.write(b'\x00\x00\x00\x01\x00\x00\x00\x00')  # 最小像素数据
                f.write(b'IEND\xaeB`\x82')  # CRC
                # IEND chunk
                f.write(b'\x00\x00\x00\x00IEND\xaeB`\x82')

        # 检查是否已存在
        existing = db.query(MediaFile).filter(
            MediaFile.file_name == file_info["file_name"]
        ).first()

        if existing:
            created_media.append(existing)
            continue

        # 获取文件大小
        file_size = os.path.getsize(file_path) if os.path.exists(file_path) else None

        media = MediaFile(
            file_name=file_info["file_name"],
            file_type=file_info["file_type"],
            file_path=file_path,
            file_size=file_size,
            status="ready"
        )
        db.add(media)
        db.flush()
        created_media.append(media)

    return created_media


def create_default_playlist(db: Session, data_dir: str) -> Playlist:
    """创建默认播放列表"""
    # 检查是否已存在默认播放列表
    existing = db.query(Playlist).filter(Playlist.is_system == True).first()

    if existing:
        print(f"Default playlist already exists: {existing.name}")
        return existing

    # 创建默认媒体文件
    media_files = create_default_media_files(db, data_dir)

    # 创建默认播放列表
    version = datetime.utcnow().isoformat()
    default_playlist = Playlist(
        name="系统默认播放列表",
        description="CastPlay 系统默认播放列表，包含设备信息、系统介绍和公司宣传",
        is_system=True,
        version=version
    )
    db.add(default_playlist)
    db.flush()

    # 添加播放列表项
    for index, media in enumerate(media_files):
        item = PlaylistItem(
            playlist_id=default_playlist.id,
            media_id=media.id,
            display_order=index + 1,
            display_duration=10  # 默认显示 10 秒
        )
        db.add(item)

    db.commit()
    db.refresh(default_playlist)

    print(f"Created default playlist with {len(media_files)} items")
    return default_playlist


def assign_to_new_devices(db: Session, playlist_id: int):
    """将默认播放列表分配给新设备"""
    devices = db.query(Device).all()

    for device in devices:
        # 检查是否已有激活的播放列表
        existing_assignment = db.query(DevicePlaylist).filter(
            DevicePlaylist.device_id == device.id,
            DevicePlaylist.is_active == True
        ).first()

        if existing_assignment:
            continue

        # 分配默认播放列表
        assignment = DevicePlaylist(
            device_id=device.id,
            playlist_id=playlist_id,
            is_active=True
        )
        db.add(assignment)

    db.commit()
    print(f"Default playlist assigned to {len(devices)} devices")


def init_default_playlist():
    """主函数：初始化默认播放列表"""
    db = SessionLocal()

    try:
        # 获取数据目录
        data_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "data"
        )

        # 创建默认播放列表
        default_playlist = create_default_playlist(db, data_dir)

        # 分配给新设备
        assign_to_new_devices(db, default_playlist.id)

        print("Default playlist initialization completed successfully")

    except Exception as e:
        print(f"Error initializing default playlist: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    init_default_playlist()
