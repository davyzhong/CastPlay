"""
Playlist API 单元测试补充
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from tests.conftest import _generate_unique_id


@pytest.fixture
def client():
    """创建测试客户端"""
    return TestClient(app)


@pytest.fixture
def test_playlist(db):
    """创建测试播放列表"""
    from app.models.playlist import Playlist

    unique_id = _generate_unique_id()
    playlist = Playlist(
        name=f'Test Playlist {unique_id}',
        description='Test description'
    )
    db.session.add(playlist)
    db.session.commit()
    db.session.refresh(playlist)
    return playlist


@pytest.fixture
def test_media(db):
    """创建测试媒体文件"""
    from app.models.media import MediaFile

    unique_id = _generate_unique_id()
    media = MediaFile(
        file_name=f'test_video_{unique_id}.mp4',
        file_type='video',
        file_path=f'/tmp/test_media_{unique_id}.mp4',
        file_size=1024,
        status='ready'
    )
    db.session.add(media)
    db.session.commit()
    db.session.refresh(media)
    return media


class TestPlaylistAPI:
    """Playlist API 测试类"""

    def test_list_playlists(self, client, db, test_playlist):
        """测试获取播放列表列表"""
        response = client.get('/api/v1/playlists')

        assert response.status_code == 200
        data = response.json()

        assert 'playlists' in data
        assert len(data['playlists']) > 0

        playlist_data = data['playlists'][0]
        assert playlist_data['id'] == test_playlist.id
        assert playlist_data['name'] == test_playlist.name

    def test_get_playlist_detail(self, client, db, test_playlist, test_media):
        """测试获取播放列表详情"""
        from app.models.playlist import PlaylistItem

        # 添加播放列表项
        item = PlaylistItem(
            playlist_id=test_playlist.id,
            media_id=test_media.id,
            display_order=1,
            display_duration=10
        )
        db.session.add(item)
        db.session.commit()

        response = client.get(f'/api/v1/playlists/{test_playlist.id}')

        assert response.status_code == 200
        data = response.json()

        assert data['id'] == test_playlist.id
        assert data['name'] == test_playlist.name
        assert 'items' in data
        assert len(data['items']) > 0

    def test_create_playlist(self, client, db):
        """测试创建播放列表"""
        unique_id = _generate_unique_id()
        payload = {
            'name': f'New Playlist {unique_id}',
            'description': 'Created by test'
        }

        response = client.post('/api/v1/playlists', json=payload)

        assert response.status_code == 200
        data = response.json()

        assert data['message'] == 'Playlist created successfully'
        assert 'playlist' in data
        assert data['playlist']['name'] == payload['name']

    def test_update_playlist(self, client, db, test_playlist):
        """测试更新播放列表"""
        payload = {
            'name': 'Updated Playlist Name',
            'description': 'Updated description'
        }

        response = client.put(
            f'/api/v1/playlists/{test_playlist.id}', json=payload)

        assert response.status_code == 200
        data = response.json()

        assert data['message'] == 'Playlist updated successfully'

        # 验证数据库中的更新
        from sqlalchemy import select
        from app.models.playlist import Playlist

        result = db.execute(select(Playlist).where(
            Playlist.id == test_playlist.id))
        updated_playlist = result.scalar_one()

        assert updated_playlist.name == 'Updated Playlist Name'
        assert updated_playlist.description == 'Updated description'

    def test_delete_playlist(self, client, db, test_playlist):
        """测试删除播放列表"""
        response = client.delete(f'/api/v1/playlists/{test_playlist.id}')

        assert response.status_code == 200
        data = response.json()

        assert data['message'] == 'Playlist deleted successfully'

        # 验证软删除
        from sqlalchemy import select
        from app.models.playlist import Playlist

        result = db.execute(select(Playlist).where(
            Playlist.id == test_playlist.id))
        deleted_playlist = result.scalar_one()

        assert deleted_playlist.is_deleted is True

    def test_add_media_to_playlist(self, client, db, test_playlist, test_media):
        """测试添加媒体到播放列表"""
        payload = {
            'media_id': test_media.id,
            'display_order': 1,
            'display_duration': 15
        }

        response = client.post(
            f'/api/v1/playlists/{test_playlist.id}/items',
            json=payload
        )

        assert response.status_code == 200
        data = response.json()

        assert data['message'] == 'Media added to playlist successfully'
        assert 'item' in data
        assert data['item']['media_id'] == test_media.id
        assert data['item']['display_duration'] == 15

    def test_remove_media_from_playlist(self, client, db, test_playlist, test_media):
        """测试从播放列表移除媒体"""
        from app.models.playlist import PlaylistItem

        # 先添加
        item = PlaylistItem(
            playlist_id=test_playlist.id,
            media_id=test_media.id,
            display_order=1,
            display_duration=10
        )
        db.session.add(item)
        db.session.commit()

        # 再移除
        response = client.delete(
            f'/api/v1/playlists/{test_playlist.id}/items/{item.id}'
        )

        assert response.status_code == 200
        data = response.json()

        assert data['message'] == 'Item removed from playlist successfully'

        # 验证已删除
        from sqlalchemy import select
        from app.models.playlist import PlaylistItem

        result = db.execute(select(PlaylistItem).where(
            PlaylistItem.id == item.id))
        deleted_item = result.scalar_one_or_none()

        assert deleted_item is None


class TestDevicePlaylist:
    """设备播放列表关联测试"""

    def test_assign_playlist_to_device(self, client, db, test_playlist):
        """测试分配播放列表到设备"""
        from app.models.device import Device

        unique_id = _generate_unique_id()
        device = Device(
            device_id=f'test-device-{unique_id}',
            device_name='Test Device',
            timezone='Asia/Shanghai'
        )
        db.session.add(device)
        db.session.commit()

        payload = {'playlist_id': test_playlist.id}

        response = client.post(
            f'/api/v1/devices/{device.id}/playlist',
            json=payload
        )

        assert response.status_code == 200
        data = response.json()

        assert data['message'] == 'Playlist assigned to device successfully'
        assert 'assignment' in data
        assert data['assignment']['playlist_id'] == test_playlist.id

    def test_get_device_playlist(self, client, db, test_playlist):
        """测试获取设备播放列表"""
        from app.models.device import Device
        from app.models.playlist import DevicePlaylist

        unique_id = _generate_unique_id()
        device = Device(
            device_id=f'test-device-{unique_id}',
            device_name='Test Device',
            timezone='Asia/Shanghai'
        )
        db.session.add(device)
        db.session.commit()

        # 创建关联
        dp = DevicePlaylist(
            device_id=device.id,
            playlist_id=test_playlist.id,
            is_active=True
        )
        db.session.add(dp)
        db.session.commit()

        response = client.get(f'/api/v1/devices/{device.id}/playlist')

        assert response.status_code == 200
        data = response.json()

        assert 'playlist' in data
        assert data['playlist']['id'] == test_playlist.id
