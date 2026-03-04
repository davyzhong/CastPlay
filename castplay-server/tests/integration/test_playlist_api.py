"""
Integration Tests for Playlist API
"""
import pytest
import json
from app.models import Playlist, PlaylistItem, DevicePlaylist


class TestPlaylistCRUD:
    """测试播放列表 CRUD API"""

    def test_create_playlist(self, client):
        """测试创建播放列表"""
        data = {
            'name': 'New Playlist',
            'description': 'Test description'
        }

        response = client.post('/api/playlists',
                               data=json.dumps(data),
                               content_type='application/json')

        assert response.status_code == 201
        json_data = response.get_json()
        assert 'playlist' in json_data
        assert json_data['playlist']['name'] == 'New Playlist'

    def test_create_playlist_missing_name(self, client):
        """测试缺少 name 的情况"""
        data = {'description': 'Test'}

        response = client.post('/api/playlists',
                               data=json.dumps(data),
                               content_type='application/json')

        assert response.status_code == 400

    def test_list_playlists(self, client, app, sample_playlist):
        """测试获取播放列表列表"""
        response = client.get('/api/playlists')

        assert response.status_code == 200
        json_data = response.get_json()
        assert 'playlists' in json_data
        assert len(json_data['playlists']) == 1

    def test_get_playlist_detail(self, client, app, sample_playlist):
        """测试获取播放列表详情"""
        response = client.get(f'/api/playlists/{sample_playlist.id}')

        assert response.status_code == 200
        json_data = response.get_json()
        assert json_data['id'] == sample_playlist.id
        assert 'items' in json_data
        assert 'devices' in json_data

    def test_update_playlist(self, client, app, sample_playlist):
        """测试更新播放列表"""
        data = {
            'name': 'Updated Playlist',
            'description': 'Updated description'
        }

        response = client.put(f'/api/playlists/{sample_playlist.id}',
                              data=json.dumps(data),
                              content_type='application/json')

        assert response.status_code == 200
        json_data = response.get_json()
        assert json_data['playlist']['name'] == 'Updated Playlist'

    def test_delete_playlist(self, client, app, sample_playlist):
        """测试删除播放列表"""
        response = client.delete(f'/api/playlists/{sample_playlist.id}')

        assert response.status_code == 200

        # 验证已删除
        with app.app_context():
            playlist = Playlist.query.get(sample_playlist.id)
            assert playlist is None


class TestPlaylistItems:
    """测试播放列表项 API"""

    def test_add_media_to_playlist(self, client, app, sample_playlist, sample_media):
        """测试添加媒体到播放列表"""
        data = {
            'media_id': sample_media.id,
            'display_duration': 10
        }

        response = client.post(f'/api/playlists/{sample_playlist.id}/items',
                               data=json.dumps(data),
                               content_type='application/json')

        assert response.status_code == 201
        json_data = response.get_json()
        assert 'item' in json_data
        assert json_data['item']['media_id'] == sample_media.id
        assert json_data['item']['display_duration'] == 10

    def test_add_media_missing_media_id(self, client, app, sample_playlist):
        """测试缺少 media_id"""
        data = {'display_duration': 10}

        response = client.post(f'/api/playlists/{sample_playlist.id}/items',
                               data=json.dumps(data),
                               content_type='application/json')

        assert response.status_code == 400

    def test_remove_media_from_playlist(self, client, app, sample_playlist_with_item):
        """测试从播放列表移除媒体"""
        playlist, media, item = sample_playlist_with_item

        response = client.delete(
            f'/api/playlists/{playlist.id}/items/{item.id}')

        assert response.status_code == 200

        # 验证已删除
        with app.app_context():
            deleted_item = PlaylistItem.query.get(item.id)
            assert deleted_item is None

    def test_reorder_playlist_items(self, client, app, sample_playlist, sample_media):
        """测试重新排序播放列表项"""
        # 先添加一个项
        with app.app_context():
            from app import db
            item2 = PlaylistItem(
                playlist_id=sample_playlist.id,
                media_id=sample_media.id,
                display_order=2,
                display_duration=5
            )
            db.session.add(item2)
            db.session.commit()
            item2_id = item2.id

            playlist = Playlist.query.get(sample_playlist.id)
            item1_id = playlist.items[0].id

        # 重新排序
        data = {
            'items': [
                {'id': item2_id, 'order': 0},
                {'id': item1_id, 'order': 1}
            ]
        }

        response = client.put(f'/api/playlists/{sample_playlist.id}/items/reorder',
                              data=json.dumps(data),
                              content_type='application/json')

        assert response.status_code == 200


class TestDevicePlaylistAssignment:
    """测试设备播放列表分配 API"""

    def test_assign_playlist_to_device(self, client, app, sample_device, sample_playlist):
        """测试分配播放列表到设备"""
        response = client.post(
            f'/api/playlists/{sample_playlist.id}/devices/{sample_device.id}')

        assert response.status_code == 201
        json_data = response.get_json()
        assert 'assignment' in json_data
        assert json_data['assignment']['device_id'] == sample_device.id
        assert json_data['assignment']['playlist_id'] == sample_playlist.id

    def test_assign_playlist_already_assigned(self, client, app, sample_device, sample_playlist):
        """测试重复分配"""
        # 先分配一次
        with app.app_context():
            from app import db
            dp = DevicePlaylist(
                device_id=sample_device.id,
                playlist_id=sample_playlist.id
            )
            db.session.add(dp)
            db.session.commit()

        # 再次分配
        response = client.post(
            f'/api/playlists/{sample_playlist.id}/devices/{sample_device.id}')

        assert response.status_code == 200  # 已存在，返回成功

    def test_unassign_playlist_from_device(self, client, app, sample_device, sample_playlist):
        """测试取消分配播放列表"""
        # 先分配
        with app.app_context():
            from app import db
            dp = DevicePlaylist(
                device_id=sample_device.id,
                playlist_id=sample_playlist.id
            )
            db.session.add(dp)
            db.session.commit()

        # 取消分配
        response = client.delete(
            f'/api/playlists/{sample_playlist.id}/devices/{sample_device.id}')

        assert response.status_code == 200

        # 验证已删除
        with app.app_context():
            dp = DevicePlaylist.query.filter_by(
                device_id=sample_device.id,
                playlist_id=sample_playlist.id
            ).first()
            assert dp is None

    def test_activate_playlist(self, client, app, sample_device, sample_playlist):
        """测试激活/停用播放列表"""
        # 先分配
        with app.app_context():
            from app import db
            dp = DevicePlaylist(
                device_id=sample_device.id,
                playlist_id=sample_playlist.id,
                is_active=False
            )
            db.session.add(dp)
            db.session.commit()

        # 激活
        data = {'is_active': True}
        response = client.put(f'/api/playlists/{sample_playlist.id}/devices/{sample_device.id}/activate',
                              data=json.dumps(data),
                              content_type='application/json')

        assert response.status_code == 200

        # 验证状态已更新
        with app.app_context():
            dp = DevicePlaylist.query.filter_by(
                device_id=sample_device.id,
                playlist_id=sample_playlist.id
            ).first()
            assert dp.is_active is True
