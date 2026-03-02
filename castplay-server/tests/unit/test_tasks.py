"""
Celery Tasks Tests - 简化版本，避免复杂的 Celery Mock
"""
import pytest
from unittest.mock import Mock, patch
import os
import tempfile


class TestConverterService:
    """转换器服务测试"""

    def test_images_to_video_no_images(self):
        """测试图片转视频 - 无图片"""
        from app.services.converter import PPTConverter

        with tempfile.TemporaryDirectory() as tmpdir:
            converter = PPTConverter()

            # 创建空目录
            images_dir = os.path.join(tmpdir, 'empty')
            os.makedirs(images_dir)

            with pytest.raises(Exception) as excinfo:
                converter._images_to_video(images_dir, tmpdir, 5)

            assert 'No images found' in str(excinfo.value)

    def test_calculate_md5_same_content(self):
        """测试 MD5 计算 - 相同内容"""
        from app.services.converter import PPTConverter

        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f1, \
                tempfile.NamedTemporaryFile(mode='w', delete=False) as f2:
            f1.write('same content')
            f2.write('same content')
            f1.flush()
            f2.flush()

            try:
                converter = PPTConverter()
                md5_1 = converter.calculate_md5(f1.name)
                md5_2 = converter.calculate_md5(f2.name)

                assert md5_1 == md5_2
            finally:
                os.unlink(f1.name)
                os.unlink(f2.name)

    def test_calculate_md5_different_content(self):
        """测试 MD5 计算 - 不同内容"""
        from app.services.converter import PPTConverter

        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f1, \
                tempfile.NamedTemporaryFile(mode='w', delete=False) as f2:
            f1.write('content A')
            f2.write('content B')
            f1.flush()
            f2.flush()

            try:
                converter = PPTConverter()
                md5_1 = converter.calculate_md5(f1.name)
                md5_2 = converter.calculate_md5(f2.name)

                assert md5_1 != md5_2
            finally:
                os.unlink(f1.name)
                os.unlink(f2.name)

    def test_cleanup_nonexistent_files(self):
        """测试清理不存在的文件"""
        from app.services.converter import PPTConverter

        converter = PPTConverter()

        # 不应抛出异常
        converter._cleanup('/nonexistent/path.pdf', '/nonexistent/images')

    def test_cleanup_existing_files(self):
        """测试清理存在的文件"""
        from app.services.converter import PPTConverter

        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建测试文件
            pdf_path = os.path.join(tmpdir, 'test.pdf')
            images_dir = os.path.join(tmpdir, 'images')
            os.makedirs(images_dir)

            with open(pdf_path, 'w') as f:
                f.write('fake pdf')

            converter = PPTConverter()
            converter._cleanup(pdf_path, images_dir)

            # 验证文件被删除
            assert not os.path.exists(pdf_path)
            assert not os.path.exists(images_dir)

    def test_convert_to_pdf_failure(self):
        """测试 PDF 转换失败"""
        from app.services.converter import PPTConverter

        with tempfile.TemporaryDirectory() as tmpdir:
            converter = PPTConverter(libreoffice_path='/nonexistent/soffice')

            # 创建假 PPT 文件
            ppt_path = os.path.join(tmpdir, 'test.pptx')
            with open(ppt_path, 'w') as f:
                f.write('fake ppt')

            with pytest.raises(Exception):
                converter._convert_to_pdf(ppt_path, tmpdir)

    def test_generate_thumbnail_failure(self):
        """测试缩略图生成失败"""
        from app.services.converter import PPTConverter

        converter = PPTConverter(ffmpeg_path='/nonexistent/ffmpeg')

        with pytest.raises(Exception):
            converter.generate_thumbnail(
                '/nonexistent/video.mp4', '/tmp/thumb.jpg')

    def test_converter_default_paths(self):
        """测试转换器默认路径"""
        from app.services.converter import PPTConverter

        converter = PPTConverter()

        # 默认路径可能是 soffice 或完整路径
        assert 'soffice' in converter.libreoffice_path
        assert 'ffmpeg' in converter.ffmpeg_path

    def test_converter_custom_paths(self):
        """测试转换器自定义路径"""
        from app.services.converter import PPTConverter

        converter = PPTConverter(
            libreoffice_path='/custom/soffice',
            ffmpeg_path='/custom/ffmpeg'
        )

        assert converter.libreoffice_path == '/custom/soffice'
        assert converter.ffmpeg_path == '/custom/ffmpeg'


class TestMediaFileStatus:
    """媒体文件状态测试"""

    def test_media_status_transitions(self, app):
        """测试媒体状态转换"""
        from app.models import MediaFile
        from app import db

        with app.app_context():
            media = MediaFile(
                file_name='test.pptx',
                file_type='ppt',
                file_path='/tmp/test.pptx',
                file_size=1024,
                status='pending'
            )
            db.session.add(media)
            db.session.commit()

            # 状态转换: pending -> processing
            media.status = 'processing'
            db.session.commit()
            assert media.status == 'processing'

            # 状态转换: processing -> ready
            media.status = 'ready'
            db.session.commit()
            assert media.status == 'ready'

    def test_media_converted_path(self, app):
        """测试媒体转换路径"""
        from app.models import MediaFile
        from app import db

        with app.app_context():
            media = MediaFile(
                file_name='presentation.pptx',
                file_type='ppt',
                file_path='/tmp/presentation.pptx',
                file_size=10240,
                status='pending'
            )
            db.session.add(media)
            db.session.commit()

            # 设置转换后路径
            media.converted_path = '/tmp/converted/presentation.mp4'
            media.thumbnail_path = '/tmp/thumbnails/presentation.jpg'
            media.status = 'ready'
            db.session.commit()

            # 验证
            assert media.converted_path == '/tmp/converted/presentation.mp4'
            assert media.thumbnail_path == '/tmp/thumbnails/presentation.jpg'
