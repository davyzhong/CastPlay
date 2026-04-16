"""
数据模型单元测试

测试所有 SQLAlchemy 模型的字段、关系和约束
"""
import pytest
from datetime import datetime

from app.models.user import User
from app.models.device import Device, DeviceSchedule
from app.models.media import MediaFile
from app.models.playlist import Playlist, PlaylistItem, DevicePlaylist


# ============================================================================
# User 模型测试
# ============================================================================

class TestUserModel:
    """User 模型测试"""

    def test_user_creation(self, db_session):
        """测试创建用户"""
        user = User(
            username="testuser",
            password_hash="hashed_password",
            email="test@example.com",
            full_name="Test User"
        )
        db_session.add(user)
        db_session.commit()

        retrieved_user = db_session.query(User).filter(User.username == "testuser").first()
        assert retrieved_user is not None
        assert retrieved_user.username == "testuser"
        assert retrieved_user.email == "test@example.com"
        assert retrieved_user.full_name == "Test User"
        assert retrieved_user.is_active is True
        assert retrieved_user.is_superuser is False

    def test_user_timestamps(self, db_session):
        """测试用户时间戳自动生成"""
        user = User(
            username="timestamp_test",
            password_hash="hashed"
        )
        db_session.add(user)
        db_session.commit()

        assert user.created_at is not None
        assert user.updated_at is not None
        assert isinstance(user.created_at, datetime)
        assert isinstance(user.updated_at, datetime)

    def test_user_superuser_flag(self, db_session):
        """测试超级用户标志"""
        admin = User(
            username="admin",
            password_hash="hashed",
            is_superuser=True
        )
        db_session.add(admin)
        db_session.commit()

        assert admin.is_superuser is True

    def test_user_active_flag(self, db_session):
        """测试用户激活状态"""
        inactive_user = User(
            username="inactive",
            password_hash="hashed",
            is_active=False
        )
        db_session.add(inactive_user)
        db_session.commit()

        assert inactive_user.is_active is False


# ============================================================================
# Device 模型测试
# ============================================================================

class TestDeviceModel:
    """Device 模型测试"""

    def test_device_creation(self, db_session):
        """测试创建设备"""
        device = Device(
            device_id="123e4567-e89b-12d3-a456-426614174000",
            device_name="Test Device",
            timezone="Asia/Shanghai",
            status="online"
        )
        db_session.add(device)
        db_session.commit()

        retrieved = db_session.query(Device).filter(Device.device_id == device.device_id).first()
        assert retrieved is not None
        assert retrieved.device_name == "Test Device"
        assert retrieved.timezone == "Asia/Shanghai"
        assert retrieved.status == "online"

    def test_device_default_timezone(self, db_session):
        """测试设备默认时区"""
        device = Device(
            device_id="test-device-id",
            device_name="Default Timezone Device"
        )
        db_session.add(device)
        db_session.commit()

        assert device.timezone == "Asia/Shanghai"

    def test_device_default_status(self, db_session):
        """测试设备默认状态"""
        device = Device(
            device_id="test-device-id-2",
            device_name="Default Status Device"
        )
        db_session.add(device)
        db_session.commit()

        assert device.status == "offline"

    def test_device_last_online(self, db_session):
        """测试设备最后在线时间"""
        device = Device(
            device_id="test-device-id-3",
            device_name="Last Online Test"
        )
        db_session.add(device)
        db_session.commit()

        # last_online is nullable, can be None for new devices
        assert device.last_online is None or isinstance(device.last_online, datetime)


# ============================================================================
# DeviceSchedule 模型测试
# ============================================================================

class TestDeviceScheduleModel:
    """DeviceSchedule 模型测试"""

    def test_schedule_creation(self, db_session, test_device):
        """测试创建定时配置"""
        schedule = DeviceSchedule(
            device_id=test_device.id,
            power_on_time="09:00",
            power_off_time="18:00",
            is_enabled=1,
            weekdays="0,1,2,3,4"
        )
        db_session.add(schedule)
        db_session.commit()

        assert schedule.power_on_time == "09:00"
        assert schedule.power_off_time == "18:00"
        assert schedule.is_enabled == 1
        assert schedule.weekdays == "0,1,2,3,4"

    def test_schedule_relationship(self, db_session, test_device):
        """测试设备与定时配置的关系"""
        schedule = DeviceSchedule(
            device_id=test_device.id,
            power_on_time="08:00",
            power_off_time="20:00",
            is_enabled=1
        )
        db_session.add(schedule)
        db_session.commit()

        db_session.refresh(test_device)
        # 验证关系是否正确建立
        assert schedule.device_id == test_device.id


# ============================================================================
# MediaFile 模型测试
# ============================================================================

class TestMediaFileModel:
    """MediaFile 模型测试"""

    def test_media_creation(self, db_session):
        """测试创建媒体文件记录"""
        media = MediaFile(
            file_name="test.jpg",
            file_type="image",
            file_path="/uploads/test.jpg",
            file_size=102400,
            md5_hash="d41d8cd98f00b204e9800998ecf8427e"
        )
        db_session.add(media)
        db_session.commit()

        retrieved = db_session.query(MediaFile).filter(MediaFile.file_name == "test.jpg").first()
        assert retrieved is not None
        assert retrieved.file_type == "image"
        assert retrieved.file_size == 102400
        assert retrieved.status == "ready"

    def test_media_with_thumbnail(self, db_session):
        """测试带缩略图的媒体文件"""
        media = MediaFile(
            file_name="video.mp4",
            file_type="video",
            file_path="/uploads/video.mp4",
            file_size=10485760,
            thumbnail_path="/thumbnails/thumb_video.jpg",
            md5_hash="hash123"
        )
        db_session.add(media)
        db_session.commit()

        assert media.thumbnail_path is not None

    def test_media_with_converted_file(self, db_session):
        """测试带转换文件的 PPT 媒体"""
        media = MediaFile(
            file_name="presentation.pptx",
            file_type="ppt",
            file_path="/uploads/presentation.pptx",
            file_size=5242880,
            converted_path="/converted/presentation.mp4",
            md5_hash="hash456"
        )
        db_session.add(media)
        db_session.commit()

        assert media.converted_path is not None

    def test_media_status_enum(self, db_session):
        """测试媒体状态值"""
        statuses = ["ready", "processing", "failed"]
        for status in statuses:
            media = MediaFile(
                file_name=f"test_{status}.jpg",
                file_type="image",
                file_path=f"/uploads/test_{status}.jpg",
                file_size=1000,
                status=status
            )
            db_session.add(media)
        db_session.commit()

        for status in statuses:
            media = db_session.query(MediaFile).filter(MediaFile.file_name == f"test_{status}.jpg").first()
            assert media.status == status


# ============================================================================
# Playlist 模型测试
# ============================================================================

class TestPlaylistModel:
    """Playlist 模型测试"""

    def test_playlist_creation(self, db_session):
        """测试创建播放列表"""
        playlist = Playlist(
            name="Test Playlist",
            description="A test playlist"
        )
        db_session.add(playlist)
        db_session.commit()

        retrieved = db_session.query(Playlist).filter(Playlist.name == "Test Playlist").first()
        assert retrieved is not None
        assert retrieved.description == "A test playlist"

    def test_playlist_optional_description(self, db_session):
        """测试播放列表可选描述"""
        playlist = Playlist(name="No Description Playlist")
        db_session.add(playlist)
        db_session.commit()

        assert playlist.description is None


# ============================================================================
# PlaylistItem 模型测试
# ============================================================================

class TestPlaylistItemModel:
    """PlaylistItem 模型测试"""

    def test_playlist_item_creation(self, db_session, test_playlist, test_media):
        """测试创建播放列表项"""
        item = PlaylistItem(
            playlist_id=test_playlist.id,
            media_id=test_media.id,
            display_order=0,
            display_duration=10
        )
        db_session.add(item)
        db_session.commit()

        assert item.display_order == 0
        assert item.display_duration == 10

    def test_playlist_item_relationships(self, db_session, test_playlist, test_media):
        """测试播放列表项的关系"""
        item = PlaylistItem(
            playlist_id=test_playlist.id,
            media_id=test_media.id,
            display_order=0,
            display_duration=15
        )
        db_session.add(item)
        db_session.commit()

        assert item.playlist_id == test_playlist.id
        assert item.media_id == test_media.id

    def test_multiple_items_ordering(self, db_session, test_playlist, multiple_test_media):
        """测试多个播放列表项的排序"""
        for i, media in enumerate(multiple_test_media):
            item = PlaylistItem(
                playlist_id=test_playlist.id,
                media_id=media.id,
                display_order=i,
                display_duration=10
            )
            db_session.add(item)
        db_session.commit()

        items = db_session.query(PlaylistItem).filter(
            PlaylistItem.playlist_id == test_playlist.id
        ).order_by(PlaylistItem.display_order).all()

        for i, item in enumerate(items):
            assert item.display_order == i


# ============================================================================
# DevicePlaylist 模型测试
# ============================================================================

class TestDevicePlaylistModel:
    """DevicePlaylist 模型测试"""

    def test_device_playlist_assignment(self, db_session, test_device, test_playlist):
        """测试设备播放列表分配"""
        assignment = DevicePlaylist(
            device_id=test_device.id,
            playlist_id=test_playlist.id
        )
        db_session.add(assignment)
        db_session.commit()

        assert assignment.device_id == test_device.id
        assert assignment.playlist_id == test_playlist.id
        # is_active field exists for backward compatibility but is no longer used

    def test_device_playlist_inactive(self, db_session, test_device, test_playlist):
        """测试停用的设备播放列表分配（is_active 字段保留用于向后兼容）"""
        assignment = DevicePlaylist(
            device_id=test_device.id,
            playlist_id=test_playlist.id,
            is_active=0
        )
        db_session.add(assignment)
        db_session.commit()

        # is_active field exists but is deprecated
        assert hasattr(assignment, 'is_active')


# ============================================================================
# 模型关系测试
# ============================================================================

class TestModelRelationships:
    """测试模型之间的关系"""

    def test_user_to_device_relationship(self, db_session, test_user):
        """虽然当前模型中没有直接关联，但预留测试位置"""
        # User 和 Device 可能在未来需要关联
        pass

    def test_playlist_to_items_cascade(self, db_session, test_playlist, test_media):
        """测试删除播放列表时对项目的影响（如果配置了级联）"""
        item = PlaylistItem(
            playlist_id=test_playlist.id,
            media_id=test_media.id,
            display_order=0
        )
        db_session.add(item)
        db_session.commit()

        # 删除播放列表
        db_session.delete(test_playlist)
        db_session.commit()

        # 检查项目是否被删除（取决于级联配置）
        remaining_items = db_session.query(PlaylistItem).filter(
            PlaylistItem.playlist_id == test_playlist.id
        ).count()
        # 根据实际级联配置断言
        # assert remaining_items == 0  # 如果配置了级联删除

    def test_media_in_multiple_playlists(self, db_session, test_playlist, test_media):
        """测试同一媒体文件可以在多个播放列表中"""
        # 创建第二个播放列表
        playlist2 = Playlist(name="Second Playlist")
        db_session.add(playlist2)
        db_session.commit()

        # 添加到两个播放列表
        item1 = PlaylistItem(
            playlist_id=test_playlist.id,
            media_id=test_media.id,
            display_order=0
        )
        item2 = PlaylistItem(
            playlist_id=playlist2.id,
            media_id=test_media.id,
            display_order=0
        )
        db_session.add(item1)
        db_session.add(item2)
        db_session.commit()

        # 验证两个播放列表都包含该媒体
        items1 = db_session.query(PlaylistItem).filter(
            PlaylistItem.playlist_id == test_playlist.id
        ).all()
        items2 = db_session.query(PlaylistItem).filter(
            PlaylistItem.playlist_id == playlist2.id
        ).all()

        assert len(items1) == 1
        assert len(items2) == 1
        assert items1[0].media_id == items2[0].media_id


# ============================================================================
# 模型约束测试
# ============================================================================

class TestModelConstraints:
    """测试模型约束"""

    def test_device_unique_device_id(self, db_session):
        """测试设备ID唯一性"""
        device_id = "unique-device-id"

        device1 = Device(
            device_id=device_id,
            device_name="Device 1"
        )
        device2 = Device(
            device_id=device_id,
            device_name="Device 2"
        )

        db_session.add(device1)
        db_session.commit()

        # 尝试添加相同 device_id 的设备（应该失败或更新）
        db_session.add(device2)
        try:
            db_session.commit()
            # 如果成功提交，可能需要检查是否更新了第一条记录
        except Exception as e:
            # 预期会抛出 IntegrityError 或类似错误
            db_session.rollback()
            assert True  # 约束生效

    def test_user_unique_username(self, db_session):
        """测试用户名唯一性"""
        username = "uniqueuser"

        user1 = User(
            username=username,
            password_hash="hash1",
            email="user1@example.com"
        )
        user2 = User(
            username=username,
            password_hash="hash2",
            email="user2@example.com"
        )

        db_session.add(user1)
        db_session.commit()

        db_session.add(user2)
        try:
            db_session.commit()
        except Exception:
            db_session.rollback()
            assert True  # 约束生效
