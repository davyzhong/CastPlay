"""
Player API Tests
"""
import pytest
import io
import os
from datetime import time


class TestPlayerInit:
    """Player 初始化接口测试"""

    def test_player_init_success(self, client, app):
        """测试播放端初始化成功"""
        from app.models import Device, Playlist, PlaylistItem, MediaFile, DevicePlaylist
        from app import db

        with app.app_context():
            # 创建测试设备
            device = Device(
                device_id='PLAYER-001',
                device_name='Test Player',
                timezone='Asia/Shanghai',
                status='offline'
            )
            db.session.add(device)
            db.session.commit()

            response = client.post('/api/player/init', json={
                'device_id': 'PLAYER-001'
            })

            assert response.status_code == 200
            data = response.get_json()
            assert 'device' in data
            assert data['device']['device_id'] == 'PLAYER-001'
            assert 'playlists' in data
            assert 'schedule' in data
            assert 'websocket_url' in data

    def test_player_init_missing_device_id(self, client, app):
        """测试播放端初始化缺少 device_id"""
        response = client.post('/api/player/init', json={})

        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        assert 'device_id is required' in data['error']

    def test_player_init_device_not_found(self, client, app):
        """测试播放端初始化设备未注册"""
        response = client.post('/api/player/init', json={
            'device_id': 'NON-EXIST-DEVICE'
        })

        assert response.status_code == 404
        data = response.get_json()
        assert 'error' in data
        assert 'not registered' in data['error']

    def test_player_init_with_playlist(self, client, app):
        """测试播放端初始化带播放列表"""
        from app.models import Device, Playlist, PlaylistItem, MediaFile, DevicePlaylist
        from app import db

        with app.app_context():
            # 创建设备
            device = Device(
                device_id='PLAYER-002',
                device_name='Test Player 2',
                timezone='Asia/Shanghai'
            )
            db.session.add(device)
            db.session.commit()

            # 创建媒体文件
            media = MediaFile(
                file_name='test.jpg',
                file_type='image',
                file_path='/tmp/test.jpg',
                file_size=1024,
                status='ready'
            )
            db.session.add(media)
            db.session.commit()

            # 创建播放列表
            playlist = Playlist(name='Test Playlist')
            db.session.add(playlist)
            db.session.commit()

            # 添加播放项
            item = PlaylistItem(
                playlist_id=playlist.id,
                media_id=media.id,
                display_order=1,
                display_duration=5
            )
            db.session.add(item)
            db.session.commit()

            # 分配播放列表到设备
            dp = DevicePlaylist(
                device_id=device.id,
                playlist_id=playlist.id,
                is_active=True
            )
            db.session.add(dp)
            db.session.commit()

            response = client.post('/api/player/init', json={
                'device_id': 'PLAYER-002'
            })

            assert response.status_code == 200
            data = response.get_json()
            assert len(data['playlists']) == 1
            assert data['playlists'][0]['name'] == 'Test Playlist'
            assert len(data['playlists'][0]['items']) == 1

    def test_player_init_with_schedule(self, client, app):
        """测试播放端初始化带定时配置"""
        from app.models import Device, DeviceSchedule
        from app import db

        with app.app_context():
            # 创建设备
            device = Device(
                device_id='PLAYER-003',
                device_name='Test Player 3',
                timezone='Asia/Shanghai'
            )
            db.session.add(device)
            db.session.commit()

            # 创建定时配置
            schedule = DeviceSchedule(
                device_id=device.id,
                power_on_time=time(8, 0),
                power_off_time=time(18, 0),
                is_enabled=True,
                weekdays='1,2,3,4,5'
            )
            db.session.add(schedule)
            db.session.commit()

            response = client.post('/api/player/init', json={
                'device_id': 'PLAYER-003'
            })

            assert response.status_code == 200
            data = response.get_json()
            assert data['schedule'] is not None
            assert data['schedule']['weekdays'] == [1, 2, 3, 4, 5]

    def test_player_init_with_ppt_media(self, client, app):
        """测试播放端初始化带 PPT 转换后的媒体"""
        from app.models import Device, Playlist, PlaylistItem, MediaFile, DevicePlaylist
        from app import db

        with app.app_context():
            # 创建设备
            device = Device(
                device_id='PLAYER-004',
                device_name='Test Player 4',
                timezone='Asia/Shanghai'
            )
            db.session.add(device)
            db.session.commit()

            # 创建 PPT 媒体文件（已转换）
            media = MediaFile(
                file_name='presentation.pptx',
                file_type='ppt',
                file_path='/tmp/presentation.pptx',
                converted_path='/tmp/presentation.mp4',
                file_size=10240,
                status='ready'
            )
            db.session.add(media)
            db.session.commit()

            # 创建播放列表
            playlist = Playlist(name='PPT Playlist')
            db.session.add(playlist)
            db.session.commit()

            # 添加播放项
            item = PlaylistItem(
                playlist_id=playlist.id,
                media_id=media.id,
                display_order=1,
                display_duration=60
            )
            db.session.add(item)
            db.session.commit()

            # 分配播放列表到设备
            dp = DevicePlaylist(
                device_id=device.id,
                playlist_id=playlist.id,
                is_active=True
            )
            db.session.add(dp)
            db.session.commit()

            response = client.post('/api/player/init', json={
                'device_id': 'PLAYER-004'
            })

            assert response.status_code == 200
            data = response.get_json()
            # PPT 应使用 converted 路径
            assert '/converted' in data['playlists'][0]['items'][0]['file_url']


class TestPlaylistVersionCheck:
    """播放列表版本检查测试"""

    def test_check_playlist_version_needs_update(self, client, app):
        """测试检查播放列表版本 - 需要更新"""
        from app.models import Playlist
        from app import db

        with app.app_context():
            playlist = Playlist(name='Version Check Playlist')
            db.session.add(playlist)
            db.session.commit()

            response = client.post(f'/api/player/playlist/{playlist.id}/check', json={
                'version': '2020-01-01T00:00:00'
            })

            assert response.status_code == 200
            data = response.get_json()
            assert data['needs_update'] is True

    def test_check_playlist_version_no_update(self, client, app):
        """测试检查播放列表版本 - 不需要更新"""
        from app.models import Playlist
        from app import db

        with app.app_context():
            playlist = Playlist(name='Version Check Playlist 2')
            db.session.add(playlist)
            db.session.commit()
            playlist_id = playlist.id

            # 先查询一次获取服务器版本
            response = client.post(f'/api/player/playlist/{playlist_id}/check', json={
                'version': '2020-01-01T00:00:00'
            })
            data = response.get_json()
            server_version = data['server_version']

            # 再次检查使用服务器版本
            response = client.post(f'/api/player/playlist/{playlist_id}/check', json={
                'version': server_version
            })

            assert response.status_code == 200
            data = response.get_json()
            assert data['needs_update'] is False

    def test_check_playlist_version_not_found(self, client, app):
        """测试检查播放列表版本 - 播放列表不存在"""
        response = client.post('/api/player/playlist/99999/check', json={
            'version': '2020-01-01T00:00:00'
        })

        assert response.status_code == 404


class TestMediaDownload:
    """媒体下载测试"""

    def test_download_media_success(self, client, app, sample_media_with_file):
        """测试下载媒体文件成功"""
        response = client.get(
            f'/api/player/media/{sample_media_with_file.id}/download')

        assert response.status_code == 200

    def test_download_media_file_not_found(self, client, app, db):
        """测试下载媒体文件 - 文件不存在"""
        from app.models import MediaFile

        upload_folder = app.config.get('UPLOAD_FOLDER')

        media = MediaFile(
            file_name='non_exist.jpg',
            file_type='image',
            file_path=f'{upload_folder}/non_exist_file.jpg',
            file_size=0,
            status='ready'
        )
        db.session.add(media)
        db.session.commit()

        response = client.get(f'/api/player/media/{media.id}/download')

        assert response.status_code == 404

    def test_download_media_not_found(self, client, app):
        """测试下载媒体文件 - 记录不存在"""
        response = client.get('/api/player/media/99999/download')
        assert response.status_code == 404


class TestConvertedMediaDownload:
    """转换后媒体下载测试"""

    def test_download_converted_media_success(self, client, app, sample_media_with_converted):
        """测试下载转换后媒体文件成功"""
        response = client.get(
            f'/api/player/media/{sample_media_with_converted.id}/converted')

        assert response.status_code == 200

    def test_download_converted_media_not_converted(self, client, app, db):
        """测试下载转换后媒体文件 - 未转换"""
        from app.models import MediaFile

        upload_folder = app.config.get('UPLOAD_FOLDER')

        media = MediaFile(
            file_name='presentation.pptx',
            file_type='ppt',
            file_path=f'{upload_folder}/presentation.pptx',
            converted_path=None,
            file_size=1024,
            status='processing'
        )
        db.session.add(media)
        db.session.commit()

        response = client.get(f'/api/player/media/{media.id}/converted')

        assert response.status_code == 404

    def test_download_converted_media_file_missing(self, client, app, db):
        """测试下载转换后媒体文件 - 转换文件不存在"""
        from app.models import MediaFile

        upload_folder = app.config.get('UPLOAD_FOLDER')
        converted_folder = app.config.get('CONVERTED_FOLDER')

        media = MediaFile(
            file_name='presentation.pptx',
            file_type='ppt',
            file_path=f'{upload_folder}/presentation.pptx',
            converted_path=f'{converted_folder}/non_exist_video.mp4',
            file_size=1024,
            status='ready'
        )
        db.session.add(media)
        db.session.commit()

        response = client.get(f'/api/player/media/{media.id}/converted')

        assert response.status_code == 404


class TestPlayerStatus:
    """播放端状态上报测试"""

    def test_report_status_success(self, client, app):
        """测试上报状态成功"""
        from app.models import Device
        from app import db

        with app.app_context():
            device = Device(
                device_id='STATUS-001',
                device_name='Status Test Device',
                status='offline'
            )
            db.session.add(device)
            db.session.commit()

            response = client.post('/api/player/status', json={
                'device_id': 'STATUS-001',
                'status': 'playing'
            })

            assert response.status_code == 200
            data = response.get_json()
            assert data['message'] == 'Status reported successfully'

            # 验证状态更新
            device = Device.query.filter_by(device_id='STATUS-001').first()
            assert device.status == 'playing'

    def test_report_status_missing_device_id(self, client, app):
        """测试上报状态缺少 device_id"""
        response = client.post('/api/player/status', json={
            'status': 'playing'
        })

        assert response.status_code == 400
        data = response.get_json()
        assert 'device_id is required' in data['error']

    def test_report_status_device_not_found(self, client, app):
        """测试上报状态设备不存在"""
        response = client.post('/api/player/status', json={
            'device_id': 'NON-EXIST-STATUS',
            'status': 'playing'
        })

        assert response.status_code == 404
        data = response.get_json()
        assert 'Device not found' in data['error']

    def test_report_status_default_status(self, client, app):
        """测试上报状态默认为 online"""
        from app.models import Device
        from app import db

        with app.app_context():
            device = Device(
                device_id='STATUS-002',
                device_name='Status Test Device 2',
                status='offline'
            )
            db.session.add(device)
            db.session.commit()

            # 不传 status 参数
            response = client.post('/api/player/status', json={
                'device_id': 'STATUS-002'
            })

            assert response.status_code == 200

            # 验证默认状态
            device = Device.query.filter_by(device_id='STATUS-002').first()
            assert device.status == 'online'
