"""
Unit Tests for PPT Converter Service
"""
import pytest
import os
import tempfile
from unittest.mock import Mock, patch, MagicMock
from app.services.converter import PPTConverter


class TestPPTConverter:
    """测试 PPT 转换服务"""

    def test_converter_initialization(self):
        """测试转换器初始化"""
        converter = PPTConverter()

        assert converter.libreoffice_path == '/usr/bin/soffice'
        assert converter.ffmpeg_path == '/usr/bin/ffmpeg'

    def test_converter_custom_paths(self):
        """测试自定义路径初始化"""
        converter = PPTConverter(
            libreoffice_path='/custom/soffice',
            ffmpeg_path='/custom/ffmpeg'
        )

        assert converter.libreoffice_path == '/custom/soffice'
        assert converter.ffmpeg_path == '/custom/ffmpeg'

    @patch('subprocess.run')
    def test_convert_to_pdf(self, mock_run):
        """测试 PPT 转 PDF"""
        mock_run.return_value = Mock(returncode=0)

        converter = PPTConverter()

        with tempfile.TemporaryDirectory() as tmpdir:
            ppt_path = os.path.join(tmpdir, 'test.pptx')
            # 创建假的 PPT 文件
            with open(ppt_path, 'w') as f:
                f.write('fake ppt')

            # 创建假的 PDF 输出
            pdf_path = os.path.join(tmpdir, 'test.pdf')
            with open(pdf_path, 'w') as f:
                f.write('fake pdf')

            result = converter._convert_to_pdf(ppt_path, tmpdir)

            assert result.endswith('test.pdf')
            mock_run.assert_called_once()

    @patch('subprocess.run')
    def test_convert_to_pdf_failure(self, mock_run):
        """测试 PPT 转 PDF 失败"""
        mock_run.side_effect = Exception("Conversion failed")

        converter = PPTConverter()

        with tempfile.TemporaryDirectory() as tmpdir:
            ppt_path = os.path.join(tmpdir, 'test.pptx')
            with open(ppt_path, 'w') as f:
                f.write('fake ppt')

            with pytest.raises(Exception):
                converter._convert_to_pdf(ppt_path, tmpdir)

    @patch('subprocess.run')
    def test_pdf_to_images(self, mock_run):
        """测试 PDF 转图片"""
        mock_run.return_value = Mock(returncode=0)

        converter = PPTConverter()

        with tempfile.TemporaryDirectory() as tmpdir:
            pdf_path = os.path.join(tmpdir, 'test.pdf')
            with open(pdf_path, 'w') as f:
                f.write('fake pdf')

            # 创建假的图片输出
            images_dir = os.path.join(tmpdir, 'slides')
            os.makedirs(images_dir, exist_ok=True)

            for i in range(3):
                img_path = os.path.join(images_dir, f'slide-{i+1}.png')
                with open(img_path, 'w') as f:
                    f.write('fake image')

            result = converter._pdf_to_images(pdf_path, tmpdir)

            assert result.endswith('slides')
            mock_run.assert_called_once()

    def test_calculate_md5(self):
        """测试 MD5 计算"""
        converter = PPTConverter()

        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write('test content')
            file_path = f.name

        try:
            md5_hash = converter.calculate_md5(file_path)

            assert isinstance(md5_hash, str)
            assert len(md5_hash) == 32  # MD5 是 32 个字符
        finally:
            os.unlink(file_path)

    def test_calculate_md5_same_content(self):
        """测试相同内容的 MD5 一致性"""
        converter = PPTConverter()
        content = 'test content for md5'

        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f1:
            f1.write(content)
            file1 = f1.name

        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f2:
            f2.write(content)
            file2 = f2.name

        try:
            md5_1 = converter.calculate_md5(file1)
            md5_2 = converter.calculate_md5(file2)

            assert md5_1 == md5_2
        finally:
            os.unlink(file1)
            os.unlink(file2)

    @patch('subprocess.run')
    def test_generate_thumbnail(self, mock_run):
        """测试生成缩略图"""
        mock_run.return_value = Mock(returncode=0)

        converter = PPTConverter()

        with tempfile.TemporaryDirectory() as tmpdir:
            video_path = os.path.join(tmpdir, 'video.mp4')
            thumb_path = os.path.join(tmpdir, 'thumb.jpg')

            # 创建假的视频文件
            with open(video_path, 'w') as f:
                f.write('fake video')

            # 创建假的缩略图
            with open(thumb_path, 'w') as f:
                f.write('fake thumbnail')

            result = converter.generate_thumbnail(video_path, thumb_path)

            assert result == thumb_path
            mock_run.assert_called_once()

    def test_cleanup(self):
        """测试清理临时文件"""
        converter = PPTConverter()

        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建测试文件和目录
            pdf_path = os.path.join(tmpdir, 'test.pdf')
            with open(pdf_path, 'w') as f:
                f.write('test')

            images_dir = os.path.join(tmpdir, 'images')
            os.makedirs(images_dir)
            img_path = os.path.join(images_dir, 'img.png')
            with open(img_path, 'w') as f:
                f.write('test')

            # 执行清理
            converter._cleanup(pdf_path, images_dir)

            # 验证文件已删除
            assert not os.path.exists(pdf_path)
            assert not os.path.exists(images_dir)

    def test_cleanup_nonexistent_files(self):
        """测试清理不存在的文件（不应该抛出异常）"""
        converter = PPTConverter()

        # 清理不存在的文件，不应该抛出异常
        converter._cleanup('/nonexistent/file.pdf', '/nonexistent/dir')


class TestPPTConverterIntegration:
    """集成测试（使用 Mock）"""

    @patch('subprocess.run')
    def test_full_conversion_flow_mocked(self, mock_run):
        """测试完整转换流程（使用 Mock）"""
        # 配置 mock 返回成功
        mock_run.return_value = Mock(returncode=0)

        converter = PPTConverter()

        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建测试文件
            ppt_path = os.path.join(tmpdir, 'test.pptx')
            with open(ppt_path, 'w') as f:
                f.write('fake ppt content')

            # 创建模拟的输出文件
            pdf_path = os.path.join(tmpdir, 'test.pdf')
            with open(pdf_path, 'w') as f:
                f.write('fake pdf')

            slides_dir = os.path.join(tmpdir, 'slides')
            os.makedirs(slides_dir)
            for i in range(3):
                img_path = os.path.join(slides_dir, f'slide-{i+1}.png')
                with open(img_path, 'w') as f:
                    f.write(f'fake image {i}')

            video_path = os.path.join(tmpdir, 'output.mp4')
            with open(video_path, 'w') as f:
                f.write('fake video')

            # 测试 PDF 转换
            result_pdf = converter._convert_to_pdf(ppt_path, tmpdir)
            assert result_pdf.endswith('.pdf')

            # 测试图片转换
            result_images = converter._pdf_to_images(pdf_path, tmpdir)
            assert 'slides' in result_images

            # 测试 MD5 计算
            md5_hash = converter.calculate_md5(video_path)
            assert len(md5_hash) == 32

    @patch('subprocess.run')
    def test_images_to_video_flow(self, mock_run):
        """测试图片转视频流程"""
        mock_run.return_value = Mock(returncode=0)

        converter = PPTConverter()

        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建测试图片
            images_dir = os.path.join(tmpdir, 'images')
            os.makedirs(images_dir)
            for i in range(5):
                img_path = os.path.join(images_dir, f'slide-{i+1}.png')
                with open(img_path, 'w') as f:
                    f.write(f'fake image {i}')

            # 创建输出视频
            video_path = os.path.join(tmpdir, 'output.mp4')
            with open(video_path, 'w') as f:
                f.write('fake video content')

            result = converter._images_to_video(
                images_dir, tmpdir, duration_per_slide=5)

            assert result.endswith('.mp4')
            mock_run.assert_called()
