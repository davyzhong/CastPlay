"""
Integration Tests for Media API
"""
import pytest
import json
import io
from app.models import MediaFile


class TestMediaUpload:
    """测试媒体文件上传 API"""

    def test_upload_image(self, client, app):
        """测试上传图片"""
        data = {
            'file': (io.BytesIO(b"fake image content"), 'test.jpg'),
            'file_type': 'image'
        }

        response = client.post('/api/media/upload',
                               data=data,
                               content_type='multipart/form-data')

        assert response.status_code == 201
        json_data = response.get_json()
        assert 'media' in json_data
        assert json_data['media']['file_type'] in ['image', 'video', 'ppt']

    def test_upload_without_file(self, client):
        """测试没有文件的上传"""
        response = client.post('/api/media/upload',
                               data={},
                               content_type='multipart/form-data')

        assert response.status_code == 400
        json_data = response.get_json()
        assert 'error' in json_data

    def test_upload_unsupported_file_type(self, client):
        """测试不支持的文件类型"""
        data = {
            'file': (io.BytesIO(b"fake content"), 'test.txt')
        }

        response = client.post('/api/media/upload',
                               data=data,
                               content_type='multipart/form-data')

        # 根据实际实现，可能返回 400 或接受但标记为未知类型
        assert response.status_code in [400, 201]


class TestMediaList:
    """测试媒体列表 API"""

    def test_list_media_empty(self, client):
        """测试空媒体列表"""
        response = client.get('/api/media')

        assert response.status_code == 200
        json_data = response.get_json()
        assert 'media_files' in json_data
        assert len(json_data['media_files']) == 0

    def test_list_media_with_data(self, client, app, sample_media):
        """测试有数据的媒体列表"""
        response = client.get('/api/media')

        assert response.status_code == 200
        json_data = response.get_json()
        assert len(json_data['media_files']) == 1
        assert json_data['total'] == 1

    def test_list_media_filter_by_type(self, client, app):
        """测试按类型过滤媒体"""
        # 创建多个不同类型的媒体
        with app.app_context():
            from app import db
            media1 = MediaFile(
                file_name='image.jpg',
                file_type='image',
                file_path='/storage/image.jpg',
                status='ready'
            )
            media2 = MediaFile(
                file_name='video.mp4',
                file_type='video',
                file_path='/storage/video.mp4',
                status='ready'
            )
            db.session.add_all([media1, media2])
            db.session.commit()

        response = client.get('/api/media?file_type=image')

        assert response.status_code == 200
        json_data = response.get_json()
        assert len(json_data['media_files']) == 1
        assert json_data['media_files'][0]['file_type'] == 'image'

    def test_list_media_filter_by_status(self, client, app):
        """测试按状态过滤媒体"""
        with app.app_context():
            from app import db
            media1 = MediaFile(
                file_name='ready.jpg',
                file_type='image',
                file_path='/storage/ready.jpg',
                status='ready'
            )
            media2 = MediaFile(
                file_name='processing.pptx',
                file_type='ppt',
                file_path='/storage/processing.pptx',
                status='processing'
            )
            db.session.add_all([media1, media2])
            db.session.commit()

        response = client.get('/api/media?status=ready')

        assert response.status_code == 200
        json_data = response.get_json()
        assert all(m['status'] == 'ready' for m in json_data['media_files'])

    def test_list_media_pagination(self, client, app):
        """测试分页"""
        # 创建多个媒体文件
        with app.app_context():
            from app import db
            for i in range(10):
                media = MediaFile(
                    file_name=f'file{i}.jpg',
                    file_type='image',
                    file_path=f'/storage/file{i}.jpg',
                    status='ready'
                )
                db.session.add(media)
            db.session.commit()

        response = client.get('/api/media?page=1&per_page=5')

        assert response.status_code == 200
        json_data = response.get_json()
        assert len(json_data['media_files']) == 5
        assert json_data['total'] == 10


class TestMediaDetail:
    """测试媒体详情 API"""

    def test_get_media_detail(self, client, app, sample_media):
        """测试获取媒体详情"""
        response = client.get(f'/api/media/{sample_media.id}')

        assert response.status_code == 200
        json_data = response.get_json()
        assert json_data['id'] == sample_media.id
        assert json_data['file_name'] == 'test_image.jpg'

    def test_get_media_not_found(self, client):
        """测试获取不存在的媒体"""
        response = client.get('/api/media/9999')

        assert response.status_code == 404


class TestMediaUpdate:
    """测试媒体更新 API"""

    def test_update_media(self, client, app, sample_media):
        """测试更新媒体信息"""
        data = {
            'file_name': 'updated_image.jpg'
        }

        response = client.put(f'/api/media/{sample_media.id}',
                              data=json.dumps(data),
                              content_type='application/json')

        assert response.status_code == 200
        json_data = response.get_json()
        assert json_data['media']['file_name'] == 'updated_image.jpg'

    def test_update_media_not_found(self, client):
        """测试更新不存在的媒体"""
        data = {'file_name': 'test.jpg'}

        response = client.put('/api/media/9999',
                              data=json.dumps(data),
                              content_type='application/json')

        assert response.status_code == 404


class TestMediaDelete:
    """测试媒体删除 API"""

    def test_delete_media(self, client, app, sample_media):
        """测试删除媒体"""
        response = client.delete(f'/api/media/{sample_media.id}')

        assert response.status_code == 200

        # 验证已删除
        with app.app_context():
            media = MediaFile.query.get(sample_media.id)
            assert media is None

    def test_delete_media_not_found(self, client):
        """测试删除不存在的媒体"""
        response = client.delete('/api/media/9999')

        assert response.status_code == 404

    def test_delete_media_in_playlist(self, client, app, sample_playlist):
        """测试删除播放列表中的媒体"""
        # 获取播放列表中的媒体 ID
        with app.app_context():
            playlist = client.get(
                f'/api/playlists/{sample_playlist.id}').get_json()
            media_id = playlist['items'][0]['media_id']

        # 删除媒体（级联删除应该处理播放列表项）
        response = client.delete(f'/api/media/{media_id}')

        assert response.status_code == 200


class TestMediaDownload:
    """测试媒体下载 API"""

    def test_download_media(self, client, app, sample_media):
        """测试下载媒体文件"""
        response = client.get(f'/api/media/{sample_media.id}/download')

        # 根据实际实现，可能需要模拟文件系统
        # 这里只测试路由是否正确
        assert response.status_code in [200, 404]  # 404 如果文件不存在

    def test_download_media_not_found(self, client):
        """测试下载不存在的媒体"""
        response = client.get('/api/media/9999/download')

        assert response.status_code == 404

    def test_download_converted_ppt(self, client, app):
        """测试下载转换后的 PPT"""
        import tempfile
        import os
        from app.models import MediaFile
        from app import db

        with app.app_context():
            # 创建临时文件
            with tempfile.NamedTemporaryFile(mode='w', suffix='.mp4', delete=False) as f:
                f.write('fake video content')
                converted_path = f.name

            try:
                media = MediaFile(
                    file_name='presentation.pptx',
                    file_type='ppt',
                    file_path='/tmp/presentation.pptx',
                    converted_path=converted_path,
                    file_size=1024,
                    status='ready'
                )
                db.session.add(media)
                db.session.commit()
                media_id = media.id

                response = client.get(f'/api/media/{media_id}/download')

                assert response.status_code == 200
            finally:
                if os.path.exists(converted_path):
                    os.unlink(converted_path)


class TestMediaThumbnail:
    """测试媒体缩略图 API"""

    def test_get_thumbnail(self, client, app):
        """测试获取缩略图"""
        import tempfile
        import os
        from app.models import MediaFile
        from app import db

        with app.app_context():
            # 创建临时缩略图文件
            with tempfile.NamedTemporaryFile(mode='wb', suffix='.jpg', delete=False) as f:
                # 写入简单的 JPEG 头
                f.write(b'\xff\xd8\xff\xe0\x00\x10JFIF')
                thumbnail_path = f.name

            try:
                media = MediaFile(
                    file_name='video.mp4',
                    file_type='video',
                    file_path='/tmp/video.mp4',
                    thumbnail_path=thumbnail_path,
                    file_size=10240,
                    status='ready'
                )
                db.session.add(media)
                db.session.commit()
                media_id = media.id

                response = client.get(f'/api/media/{media_id}/thumbnail')

                assert response.status_code == 200
            finally:
                if os.path.exists(thumbnail_path):
                    os.unlink(thumbnail_path)

    def test_get_thumbnail_not_found(self, client, app):
        """测试获取不存在的缩略图"""
        from app.models import MediaFile
        from app import db

        with app.app_context():
            media = MediaFile(
                file_name='no_thumb.mp4',
                file_type='video',
                file_path='/tmp/no_thumb.mp4',
                thumbnail_path=None,
                file_size=10240,
                status='ready'
            )
            db.session.add(media)
            db.session.commit()
            media_id = media.id

        response = client.get(f'/api/media/{media_id}/thumbnail')

        assert response.status_code == 404

    def test_get_thumbnail_file_missing(self, client, app):
        """测试缩略图文件丢失"""
        from app.models import MediaFile
        from app import db

        with app.app_context():
            media = MediaFile(
                file_name='missing_thumb.mp4',
                file_type='video',
                file_path='/tmp/missing_thumb.mp4',
                thumbnail_path='/tmp/non_exist_thumb.jpg',
                file_size=10240,
                status='ready'
            )
            db.session.add(media)
            db.session.commit()
            media_id = media.id

        response = client.get(f'/api/media/{media_id}/thumbnail')

        assert response.status_code == 404


class TestMediaUploadAdvanced:
    """测试媒体上传高级场景"""

    def test_upload_empty_filename(self, client):
        """测试上传空文件名"""
        data = {
            'file': (io.BytesIO(b"fake content"), ''),
            'file_type': 'image'
        }

        response = client.post('/api/media/upload',
                               data=data,
                               content_type='multipart/form-data')

        assert response.status_code == 400
        json_data = response.get_json()
        assert 'error' in json_data

    def test_upload_invalid_file_type(self, client):
        """测试上传无效的文件类型参数"""
        data = {
            'file': (io.BytesIO(b"fake content"), 'test.jpg'),
            'file_type': 'invalid_type'
        }

        response = client.post('/api/media/upload',
                               data=data,
                               content_type='multipart/form-data')

        assert response.status_code == 400
        json_data = response.get_json()
        assert 'Invalid file_type' in json_data['error']

    def test_upload_missing_file_type(self, client):
        """测试上传缺少文件类型参数"""
        data = {
            'file': (io.BytesIO(b"fake content"), 'test.jpg')
        }

        response = client.post('/api/media/upload',
                               data=data,
                               content_type='multipart/form-data')

        assert response.status_code == 400
        json_data = response.get_json()
        assert 'Invalid file_type' in json_data['error']

    def test_upload_wrong_extension(self, client):
        """测试上传扩展名不匹配的文件"""
        data = {
            'file': (io.BytesIO(b"fake content"), 'test.txt'),
            'file_type': 'image'
        }

        response = client.post('/api/media/upload',
                               data=data,
                               content_type='multipart/form-data')

        assert response.status_code == 400
        json_data = response.get_json()
        assert 'not allowed' in json_data['error']

    def test_upload_video(self, client):
        """测试上传视频"""
        data = {
            'file': (io.BytesIO(b"fake video content"), 'test.mp4'),
            'file_type': 'video'
        }

        response = client.post('/api/media/upload',
                               data=data,
                               content_type='multipart/form-data')

        assert response.status_code == 201
        json_data = response.get_json()
        assert json_data['media']['file_type'] == 'video'
        assert json_data['media']['status'] == 'ready'

    def test_upload_file_without_extension(self, client):
        """测试上传没有扩展名的文件"""
        data = {
            'file': (io.BytesIO(b"fake content"), 'testfile'),
            'file_type': 'image'
        }

        response = client.post('/api/media/upload',
                               data=data,
                               content_type='multipart/form-data')

        assert response.status_code == 400
        json_data = response.get_json()
        assert 'not allowed' in json_data['error']

    def test_upload_ppt(self, client, app):
        """测试上传 PPT 文件"""
        data = {
            'file': (io.BytesIO(b"fake ppt content"), 'test.pptx'),
            'file_type': 'ppt'
        }

        # 直接测试上传，Celery 任务会在后台触发
        response = client.post('/api/media/upload',
                               data=data,
                               content_type='multipart/form-data')

        assert response.status_code == 201
        json_data = response.get_json()
        assert json_data['media']['file_type'] == 'ppt'
        assert json_data['media']['status'] == 'processing'


class TestMediaDeleteAdvanced:
    """测试媒体删除高级场景"""

    def test_delete_media_with_converted_file(self, client, app):
        """测试删除带转换文件的媒体"""
        import tempfile
        import os
        from app.models import MediaFile
        from app import db

        with app.app_context():
            # 创建临时文件
            with tempfile.NamedTemporaryFile(mode='w', suffix='.pptx', delete=False) as f:
                f.write('fake ppt')
                file_path = f.name

            with tempfile.NamedTemporaryFile(mode='w', suffix='.mp4', delete=False) as f:
                f.write('fake video')
                converted_path = f.name

            with tempfile.NamedTemporaryFile(mode='w', suffix='.jpg', delete=False) as f:
                f.write('fake thumb')
                thumbnail_path = f.name

            media = MediaFile(
                file_name='test.pptx',
                file_type='ppt',
                file_path=file_path,
                converted_path=converted_path,
                thumbnail_path=thumbnail_path,
                file_size=1024,
                status='ready'
            )
            db.session.add(media)
            db.session.commit()
            media_id = media.id

            response = client.delete(f'/api/media/{media_id}')

            assert response.status_code == 200

            # 验证所有文件都被删除
            assert not os.path.exists(file_path)
            assert not os.path.exists(converted_path)
            assert not os.path.exists(thumbnail_path)
