"""
Tests for Media API

测试媒体文件管理 API
"""
import os
import pytest
from unittest.mock import Mock, patch, MagicMock
from io import BytesIO


class TestMediaUpload:
    """媒体上传功能测试"""

    @pytest.fixture
    def mock_db(self):
        """Mock 数据库会话"""
        db = Mock()
        db.add = Mock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()
        return db

    @pytest.fixture
    def mock_current_user(self):
        """Mock 当前用户"""
        return "test_user"

    @pytest.mark.asyncio
    @patch('app.api.v1.media.aiofiles')
    async def test_upload_image_file(
        self, mock_aiofiles, mock_db, mock_current_user, client
    ):
        """测试上传图片文件"""
        # 准备测试文件
        file_data = BytesIO(b"fake image content")
        file_data.name = "test.jpg"

        with patch('app.api.v1.media.allowed_file', return_value=True):
            response = client.post(
                '/api/v1/media/upload',
                data={
                    'file': (file_data, 'test.jpg'),
                    'file_type': 'image'
                },
                headers={'Authorization': 'Bearer token'}
            )

        assert response.status_code == 201
        data = response.json()
        assert data['message'] == 'File uploaded successfully'
        assert 'media' in data

    @pytest.mark.asyncio
    async def test_upload_invalid_file_type(self, mock_db, mock_current_user, client):
        """测试上传不支持的文件类型"""
        file_data = BytesIO(b"fake content")
        file_data.name = "test.xyz"

        response = client.post(
            '/api/v1/media/upload',
            data={
                'file': (file_data, 'test.xyz'),
                'file_type': 'invalid'
            },
            headers={'Authorization': 'Bearer token'}
        )

        assert response.status_code == 400
        assert 'Invalid file_type' in response.json()['detail']

    @pytest.mark.asyncio
    @patch('app.tasks.rq_tasks.convert_ppt_to_video')
    async def test_upload_ppt_triggers_conversion(
        self, mock_convert, mock_db, mock_current_user, client
    ):
        """测试上传 PPT 自动触发转换任务"""
        file_data = BytesIO(b"fake ppt content")
        file_data.name = "test.pptx"

        with patch('app.api.v1.media.allowed_file', return_value=True):
            response = client.post(
                '/api/v1/media/upload',
                data={
                    'file': (file_data, 'test.pptx'),
                    'file_type': 'ppt'
                },
                headers={'Authorization': 'Bearer token'}
            )

        assert response.status_code == 201

        # 验证触发了转换任务
        mock_convert.assert_called_once()


class TestMediaThumbnail:
    """媒体缩略图功能测试"""

    @pytest.mark.asyncio
    async def test_get_thumbnail_with_saved_path(self, mock_db, mock_current_user, client):
        """测试获取已保存的缩略图"""
        # Mock 媒体记录
        mock_media = Mock()
        mock_media.thumbnail_path = '/path/to/thumb.jpg'
        mock_media.file_type = 'image'

        mock_db.execute = AsyncMock(return_value=Mock(
            scalar_one_or_none=Mock(return_value=mock_media)
        ))

        with patch('app.api.v1.media.os.path.exists', return_value=True):
            response = client.get(
                f'/api/v1/media/{1}/thumbnail',
                headers={'Authorization': 'Bearer token'}
            )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_thumbnail_for_image_file(self, mock_db, mock_current_user, client):
        """测试获取图片类型的缩略图（返回原图）"""
        mock_media = Mock()
        mock_media.thumbnail_path = None
        mock_media.file_type = 'image'
        mock_media.file_path = '/path/to/image.jpg'
        mock_media.file_name = 'image.jpg'

        mock_db.execute = AsyncMock(return_value=Mock(
            scalar_one_or_none=Mock(return_value=mock_media)
        ))

        with patch('app.api.v1.media.os.path.exists', return_value=True):
            response = client.get(
                f'/api/v1/media/{1}/thumbnail',
                headers={'Authorization': 'Bearer token'}
            )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_thumbnail_not_found(self, mock_db, mock_current_user, client):
        """测试缩略图不存在"""
        mock_db.execute = AsyncMock(return_value=Mock(
            scalar_one_or_none=Mock(return_value=None)
        ))

        response = client.get(
            f'/api/v1/media/{1}/thumbnail',
            headers={'Authorization': 'Bearer token'}
        )

        assert response.status_code == 404
        assert 'Media not found' in response.json()['detail']


class TestMediaAllowedFile:
    """文件类型验证测试"""

    def test_allowed_image_extensions(self):
        """测试允许的图片扩展名"""
        from app.api.v1.media import allowed_file

        assert allowed_file('test.jpg', 'image') is True
        assert allowed_file('test.jpeg', 'image') is True
        assert allowed_file('test.png', 'image') is True
        assert allowed_file('test.gif', 'image') is True
        assert allowed_file('test.bmp', 'image') is True
        assert allowed_file('test.webp', 'image') is True

    def test_allowed_video_extensions(self):
        """测试允许的视频扩展名"""
        from app.api.v1.media import allowed_file

        assert allowed_file('test.mp4', 'video') is True
        assert allowed_file('test.avi', 'video') is True
        assert allowed_file('test.mov', 'video') is True
        assert allowed_file('test.mkv', 'video') is True

    def test_allowed_ppt_extensions(self):
        """测试允许的 PPT 扩展名"""
        from app.api.v1.media import allowed_file

        assert allowed_file('test.ppt', 'ppt') is True
        assert allowed_file('test.pptx', 'ppt') is True

    def test_disallowed_extensions(self):
        """测试不允许的扩展名"""
        from app.api.v1.media import allowed_file

        assert allowed_file('test.txt', 'image') is False
        assert allowed_file('test.pdf', 'video') is False
        assert allowed_file('test.doc', 'ppt') is False

    def test_no_extension(self):
        """测试没有扩展名的文件"""
        from app.api.v1.media import allowed_file

        assert allowed_file('testfile', 'image') is False

    def test_case_insensitive(self):
        """测试扩展名大小写不敏感"""
        from app.api.v1.media import allowed_file

        assert allowed_file('test.JPG', 'image') is True
        assert allowed_file('test.Mp4', 'video') is True
        assert allowed_file('test.PPTX', 'ppt') is True


# Async Mock 辅助类
class AsyncMock(Mock):
    async def __call__(self, *args, **kwargs):
        return super().__call__(*args, **kwargs)
