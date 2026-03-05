"""
播放列表和设备模型扩展测试

测试新增的字段：
1. Playlist.is_system
2. Playlist.version
3. Device.mac_address
4. Device.ip_address
5. Device.registration_code
6. Device.playback_speed
7. CachedMedia 模型
"""
import pytest
import uuid
from datetime import datetime


class TestDeviceModelExtensions:
    """设备模型扩展测试"""

    def test_device_mac_address_field(self, test_db):
        """测试 MAC 地址字段"""
        from app.models.device import Device

        device = Device(
            device_id=str(uuid.uuid4()),
            device_name="MAC Test Device",
            mac_address="AA:BB:CC:DD:EE:FF"
        )
        test_db.add(device)
        test_db.commit()
        test_db.refresh(device)

        assert device.mac_address == "AA:BB:CC:DD:EE:FF"

    def test_device_ip_address_field(self, test_db):
        """测试 IP 地址字段"""
        from app.models.device import Device

        device = Device(
            device_id=str(uuid.uuid4()),
            device_name="IP Test Device",
            ip_address="192.168.1.100"
        )
        test_db.add(device)
        test_db.commit()
        test_db.refresh(device)

        assert device.ip_address == "192.168.1.100"

    def test_device_registration_code_field(self, test_db):
        """测试注册码字段"""
        from app.models.device import Device

        device = Device(
            device_id=str(uuid.uuid4()),
            device_name="Reg Code Test Device",
            registration_code="CP-A1B2-C3D4-E5F6"
        )
        test_db.add(device)
        test_db.commit()
        test_db.refresh(device)

        assert device.registration_code == "CP-A1B2-C3D4-E5F6"

    def test_device_playback_speed_default(self, test_db):
        """测试播放速度默认值"""
        from app.models.device import Device

        device = Device(
            device_id=str(uuid.uuid4()),
            device_name="Speed Test Device"
        )
        test_db.add(device)
        test_db.commit()
        test_db.refresh(device)

        assert device.playback_speed == 1  # 默认 1X

    def test_device_playback_speed_custom(self, test_db):
        """测试自定义播放速度"""
        from app.models.device import Device

        device = Device(
            device_id=str(uuid.uuid4()),
            device_name="Fast Device",
            playback_speed=4
        )
        test_db.add(device)
        test_db.commit()
        test_db.refresh(device)

        assert device.playback_speed == 4

    def test_device_mac_address_unique(self, test_db):
        """测试 MAC 地址唯一性"""
        from app.models.device import Device
        from sqlalchemy.exc import IntegrityError

        mac = "11:22:33:44:55:66"

        device1 = Device(
            device_id=str(uuid.uuid4()),
            device_name="Device 1",
            mac_address=mac
        )
        test_db.add(device1)
        test_db.commit()

        device2 = Device(
            device_id=str(uuid.uuid4()),
            device_name="Device 2",
            mac_address=mac  # 相同 MAC
        )
        test_db.add(device2)

        with pytest.raises(IntegrityError):
            test_db.commit()
            test_db.flush()

        # 回滚以清理状态
        test_db.rollback()

    def test_device_registration_code_unique(self, test_db):
        """测试注册码唯一性"""
        from app.models.device import Device
        from sqlalchemy.exc import IntegrityError

        code = "CP-1234-5678-9ABC"

        device1 = Device(
            device_id=str(uuid.uuid4()),
            device_name="Device 1",
            registration_code=code
        )
        test_db.add(device1)
        test_db.commit()

        device2 = Device(
            device_id=str(uuid.uuid4()),
            device_name="Device 2",
            registration_code=code  # 相同注册码
        )
        test_db.add(device2)

        with pytest.raises(IntegrityError):
            test_db.commit()
            test_db.flush()

        # 回滚以清理状态
        test_db.rollback()


class TestPlaylistModelExtensions:
    """播放列表模型扩展测试"""

    def test_playlist_is_system_default(self, test_db):
        """测试 is_system 默认值"""
        from app.models.playlist import Playlist

        playlist = Playlist(
            name="Test Playlist",
            description="Test"
        )
        test_db.add(playlist)
        test_db.commit()
        test_db.refresh(playlist)

        assert playlist.is_system is False

    def test_playlist_is_system_true(self, test_db):
        """测试 is_system 设为 True"""
        from app.models.playlist import Playlist

        playlist = Playlist(
            name="System Playlist",
            description="System default",
            is_system=True
        )
        test_db.add(playlist)
        test_db.commit()
        test_db.refresh(playlist)

        assert playlist.is_system is True

    def test_playlist_version_field(self, test_db):
        """测试版本字段"""
        from app.models.playlist import Playlist

        version = datetime.utcnow().isoformat()
        playlist = Playlist(
            name="Versioned Playlist",
            description="Test",
            version=version
        )
        test_db.add(playlist)
        test_db.commit()
        test_db.refresh(playlist)

        assert playlist.version == version

    def test_playlist_version_auto_updated(self, test_db):
        """测试版本自动更新"""
        from app.models.playlist import Playlist
        import time

        playlist = Playlist(
            name="Auto Version Playlist",
            description="Test"
        )
        test_db.add(playlist)
        test_db.commit()
        test_db.refresh(playlist)

        initial_updated = playlist.updated_at

        # 等待一小段时间
        time.sleep(0.1)

        # 修改播放列表
        playlist.name = "Updated Name"
        test_db.commit()
        test_db.refresh(playlist)

        # updated_at 应该自动更新
        assert playlist.updated_at >= initial_updated


class TestCachedMediaModel:
    """缓存媒体模型测试"""

    def test_cached_media_creation(self, test_db, test_device, test_media):
        """测试创建缓存媒体记录"""
        from app.models.device import CachedMedia

        cached = CachedMedia(
            device_id=test_device.id,
            media_id=test_media.id,
            local_path="/data/cache/media_1.jpg",
            md5_hash="abc123def456",
            file_size=102400,
            download_status="completed"
        )
        test_db.add(cached)
        test_db.commit()
        test_db.refresh(cached)

        assert cached.id is not None
        assert cached.device_id == test_device.id
        assert cached.media_id == test_media.id
        assert cached.download_status == "completed"

    def test_cached_media_default_status(self, test_db, test_device, test_media):
        """测试缓存媒体默认状态"""
        from app.models.device import CachedMedia

        cached = CachedMedia(
            device_id=test_device.id,
            media_id=test_media.id
        )
        test_db.add(cached)
        test_db.commit()
        test_db.refresh(cached)

        assert cached.download_status == "pending"

    def test_cached_media_download_status_values(self, test_db, test_device, test_media):
        """测试下载状态值"""
        from app.models.device import CachedMedia

        statuses = ["pending", "downloading", "completed", "failed"]

        for status in statuses:
            cached = CachedMedia(
                device_id=test_device.id,
                media_id=test_media.id,
                download_status=status
            )
            test_db.add(cached)

        test_db.commit()

        # 验证所有状态都被正确保存
        cached_items = test_db.query(CachedMedia).filter(
            CachedMedia.device_id == test_device.id
        ).all()

        assert len(cached_items) == len(statuses)

    def test_cached_media_device_relationship(self, test_db, test_device, test_media):
        """测试缓存媒体与设备的关系"""
        from app.models.device import CachedMedia

        cached = CachedMedia(
            device_id=test_device.id,
            media_id=test_media.id,
            download_status="completed"
        )
        test_db.add(cached)
        test_db.commit()
        test_db.refresh(cached)

        # 通过关系访问设备
        assert cached.device.id == test_device.id
        assert cached.device.device_name == test_device.device_name

    def test_cached_media_cascade_delete_with_device(self, test_db, test_media):
        """测试删除设备时级联删除缓存媒体"""
        from app.models.device import Device, CachedMedia

        # 创建新设备
        device = Device(
            device_id=str(uuid.uuid4()),
            device_name="Cascade Test Device"
        )
        test_db.add(device)
        test_db.commit()
        test_db.refresh(device)

        # 创建缓存媒体
        cached = CachedMedia(
            device_id=device.id,
            media_id=test_media.id,
            download_status="completed"
        )
        test_db.add(cached)
        test_db.commit()
        cached_id = cached.id

        # 删除设备
        test_db.delete(device)
        test_db.commit()

        # 缓存媒体应该被删除
        deleted = test_db.query(CachedMedia).filter(
            CachedMedia.id == cached_id
        ).first()
        assert deleted is None


class TestDeviceRelationshipWithCachedMedia:
    """设备与缓存媒体关系测试"""

    def test_device_cached_media_relationship(self, test_db, test_device, test_media):
        """测试设备访问缓存媒体关系"""
        from app.models.device import CachedMedia

        cached = CachedMedia(
            device_id=test_device.id,
            media_id=test_media.id,
            local_path="/cache/media.jpg",
            download_status="completed"
        )
        test_db.add(cached)
        test_db.commit()
        test_db.refresh(test_device)

        # 通过关系访问
        assert len(test_device.cached_media) == 1
        assert test_device.cached_media[0].local_path == "/cache/media.jpg"

    def test_device_multiple_cached_media(self, test_db, test_device, multiple_test_media):
        """测试设备多个缓存媒体"""
        from app.models.device import CachedMedia

        for media in multiple_test_media:
            cached = CachedMedia(
                device_id=test_device.id,
                media_id=media.id,
                download_status="completed"
            )
            test_db.add(cached)

        test_db.commit()
        test_db.refresh(test_device)

        assert len(test_device.cached_media) == len(multiple_test_media)
