"""
Unit Tests for Models
"""
import pytest
from datetime import datetime, time
from app import db
from app.models import Device, DeviceSchedule, MediaFile, Playlist, PlaylistItem, DevicePlaylist


class TestDeviceModel:
    """测试 Device 模型"""

    def test_create_device(self, app):
        """测试创建设备"""
        with app.app_context():
            device = Device(
                device_id='test-001',
                device_name='Test Device',
                timezone='Asia/Shanghai'
            )
            db.session.add(device)
            db.session.commit()

            assert device.id is not None
            assert device.device_id == 'test-001'
            assert device.device_name == 'Test Device'
            assert device.timezone == 'Asia/Shanghai'
            assert device.status == 'offline'  # 默认值

    def test_device_to_dict(self, app, sample_device):
        """测试设备序列化"""
        with app.app_context():
            device = Device.query.get(sample_device.id)
            data = device.to_dict()

            assert 'id' in data
            assert 'device_id' in data
            assert 'device_name' in data
            assert 'timezone' in data
            assert 'status' in data
            assert data['device_id'] == 'test-device-001'

    def test_device_unique_constraint(self, app):
        """测试设备 ID 唯一性约束"""
        with app.app_context():
            device1 = Device(device_id='same-id', device_name='Device 1')
            db.session.add(device1)
            db.session.commit()

            device2 = Device(device_id='same-id', device_name='Device 2')
            db.session.add(device2)

            with pytest.raises(Exception):  # IntegrityError
                db.session.commit()


class TestDeviceScheduleModel:
    """测试 DeviceSchedule 模型"""

    def test_create_schedule(self, app, sample_device):
        """测试创建定时配置"""
        with app.app_context():
            schedule = DeviceSchedule(
                device_id=sample_device.id,
                power_on_time=time(8, 0),
                power_off_time=time(18, 0),
                is_enabled=True,
                weekdays='1,2,3,4,5'
            )
            db.session.add(schedule)
            db.session.commit()

            assert schedule.id is not None
            assert schedule.device_id == sample_device.id
            assert schedule.power_on_time == time(8, 0)
            assert schedule.is_enabled is True

    def test_schedule_to_dict(self, app, sample_device):
        """测试定时配置序列化"""
        with app.app_context():
            schedule = DeviceSchedule(
                device_id=sample_device.id,
                power_on_time=time(9, 30),
                power_off_time=time(17, 0),
                weekdays='1,2,3,4,5,6,7'
            )
            db.session.add(schedule)
            db.session.commit()

            data = schedule.to_dict()

            assert data['power_on_time'] == '09:30'
            assert data['power_off_time'] == '17:00'
            assert data['weekdays'] == ['1', '2', '3', '4', '5', '6', '7']


class TestMediaFileModel:
    """测试 MediaFile 模型"""

    def test_create_media_file(self, app):
        """测试创建媒体文件"""
        with app.app_context():
            media = MediaFile(
                file_name='video.mp4',
                file_type='video',
                file_path='/storage/uploads/video.mp4',
                file_size=5242880,
                status='ready'
            )
            db.session.add(media)
            db.session.commit()

            assert media.id is not None
            assert media.file_name == 'video.mp4'
            assert media.file_type == 'video'
            assert media.status == 'ready'

    def test_media_to_dict(self, app, sample_media):
        """测试媒体文件序列化"""
        with app.app_context():
            media = MediaFile.query.get(sample_media.id)
            data = media.to_dict()

            assert 'id' in data
            assert 'file_name' in data
            assert 'file_type' in data
            assert 'file_size' in data
            assert 'status' in data
            assert data['file_name'] == 'test_image.jpg'

    def test_media_default_status(self, app):
        """测试媒体文件默认状态"""
        with app.app_context():
            media = MediaFile(
                file_name='ppt.pptx',
                file_type='ppt',
                file_path='/storage/uploads/ppt.pptx'
            )
            db.session.add(media)
            db.session.commit()

            assert media.status == 'processing'  # PPT 默认 processing


class TestPlaylistModel:
    """测试 Playlist 模型"""

    def test_create_playlist(self, app):
        """测试创建播放列表"""
        with app.app_context():
            playlist = Playlist(
                name='My Playlist',
                description='Test description'
            )
            db.session.add(playlist)
            db.session.commit()

            assert playlist.id is not None
            assert playlist.name == 'My Playlist'
            assert playlist.description == 'Test description'

    def test_playlist_to_dict(self, app, sample_playlist):
        """测试播放列表序列化"""
        with app.app_context():
            playlist = Playlist.query.get(sample_playlist.id)
            data = playlist.to_dict()

            assert 'id' in data
            assert 'name' in data
            assert 'item_count' in data
            assert data['name'] == 'Test Playlist'
            assert data['item_count'] == 1

    def test_playlist_to_dict_with_items(self, app, sample_playlist):
        """测试播放列表序列化（包含项目）"""
        with app.app_context():
            playlist = Playlist.query.get(sample_playlist.id)
            data = playlist.to_dict(include_items=True)

            assert 'items' in data
            assert len(data['items']) == 1
            assert data['items'][0]['display_order'] == 1


class TestPlaylistItemModel:
    """测试 PlaylistItem 模型"""

    def test_create_playlist_item(self, app, sample_playlist, sample_media):
        """测试创建播放列表项"""
        with app.app_context():
            item = PlaylistItem(
                playlist_id=sample_playlist.id,
                media_id=sample_media.id,
                display_order=2,
                display_duration=10
            )
            db.session.add(item)
            db.session.commit()

            assert item.id is not None
            assert item.playlist_id == sample_playlist.id
            assert item.media_id == sample_media.id
            assert item.display_order == 2
            assert item.display_duration == 10

    def test_playlist_item_to_dict(self, app, sample_playlist):
        """测试播放列表项序列化"""
        with app.app_context():
            playlist = Playlist.query.get(sample_playlist.id)
            item = playlist.items[0]
            data = item.to_dict()

            assert 'id' in data
            assert 'playlist_id' in data
            assert 'media_id' in data
            assert 'media' in data
            assert data['display_order'] == 1


class TestDevicePlaylistModel:
    """测试 DevicePlaylist 模型"""

    def test_create_device_playlist(self, app, sample_device, sample_playlist):
        """测试创建设备播放列表关联"""
        with app.app_context():
            dp = DevicePlaylist(
                device_id=sample_device.id,
                playlist_id=sample_playlist.id,
                is_active=True
            )
            db.session.add(dp)
            db.session.commit()

            assert dp.id is not None
            assert dp.device_id == sample_device.id
            assert dp.playlist_id == sample_playlist.id
            assert dp.is_active is True

    def test_device_playlist_unique_constraint(self, app, sample_device, sample_playlist):
        """测试设备播放列表唯一性约束"""
        with app.app_context():
            dp1 = DevicePlaylist(
                device_id=sample_device.id,
                playlist_id=sample_playlist.id
            )
            db.session.add(dp1)
            db.session.commit()

            dp2 = DevicePlaylist(
                device_id=sample_device.id,
                playlist_id=sample_playlist.id
            )
            db.session.add(dp2)

            with pytest.raises(Exception):  # IntegrityError
                db.session.commit()

    def test_device_playlist_to_dict(self, app, sample_device, sample_playlist):
        """测试设备播放列表序列化"""
        with app.app_context():
            dp = DevicePlaylist(
                device_id=sample_device.id,
                playlist_id=sample_playlist.id,
                is_active=False
            )
            db.session.add(dp)
            db.session.commit()

            data = dp.to_dict()

            assert 'id' in data
            assert 'device_id' in data
            assert 'playlist_id' in data
            assert 'is_active' in data
            assert data['is_active'] is False
