"""
Tests for PPT Converter Service

测试 PPT 转视频转换功能
"""
import os
import subprocess
import pytest
from unittest.mock import Mock, patch, MagicMock
from app.services.converter import PPTConverter


class TestPPTConverter:
    """PPT 转换器测试类"""

    @pytest.fixture
    def converter(self):
        """创建转换器实例"""
        return PPTConverter(
            libreoffice_path='/usr/bin/soffice',
            ffmpeg_path='/usr/bin/ffmpeg'
        )

    @pytest.fixture
    def sample_ppt_path(self, tmp_path):
        """创建临时 PPT 文件路径"""
        ppt_file = tmp_path / "test.pptx"
        ppt_file.write_bytes(b"fake ppt content")
        return str(ppt_file)

    def test_init(self, converter):
        """测试初始化"""
        assert converter.libreoffice_path == '/usr/bin/soffice'
        assert converter.ffmpeg_path == '/usr/bin/ffmpeg'

    @patch('subprocess.run')
    def test_convert_to_pdf(self, mock_run, converter, sample_ppt_path, tmp_path):
        """测试 PPT 转 PDF"""
        # Mock subprocess 成功执行
        mock_run.return_value = Mock(returncode=0, stdout=b'', stderr=b'')

        pdf_path = converter._convert_to_pdf(sample_ppt_path, str(tmp_path))

        # 验证 LibreOffice 命令调用
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert 'soffice' in call_args[0]
        assert '--headless' in call_args
        assert '--convert-to' in call_args
        assert 'pdf' in call_args

        # 验证返回路径
        assert pdf_path.endswith('.pdf')
        assert os.path.basename(pdf_path) == 'test.pdf'

    @patch('subprocess.run')
    def test_pdf_to_images_with_pdftoppm(self, mock_run, converter, tmp_path):
        """测试 PDF 转图片（使用 pdftoppm）"""
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"fake pdf content")

        # Mock pdftoppm 成功执行
        mock_run.return_value = Mock(returncode=0, stdout=b'', stderr=b'')

        images_dir = converter._pdf_to_images(str(pdf_path), str(tmp_path))

        # 验证 pdftoppm 命令调用
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert 'pdftoppm' in call_args[0]
        assert '-png' in call_args
        assert '-r' in call_args
        assert '150' in call_args

        # 验证返回目录
        assert images_dir.endswith('slides')

    @patch('subprocess.run')
    def test_pdf_to_images_fallback_to_imagemagick(self, mock_run, converter, tmp_path):
        """测试 PDF 转图片（pdftoppm 失败，降级到 ImageMagick）"""
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"fake pdf content")

        # Mock pdftoppm 失败，ImageMagick 成功
        mock_run.side_effect = [
            subprocess.CalledProcessError(1, 'pdftoppm'),  # 第一次调用失败
            Mock(returncode=0, stdout=b'', stderr=b'')  # 第二次调用成功
        ]

        images_dir = converter._pdf_to_images(str(pdf_path), str(tmp_path))

        # 验证调用了两次（pdftoppm 和 convert）
        assert mock_run.call_count == 2

        # 验证第二次调用是 convert 命令
        second_call_args = mock_run.call_args_list[1][0][0]
        assert 'convert' in second_call_args[0]
        assert '-density' in second_call_args

        # 验证返回目录
        assert images_dir.endswith('slides')

    @patch('subprocess.run')
    def test_images_to_video(self, mock_run, converter, tmp_path):
        """测试图片序列转视频"""
        # 创建临时图片文件
        images_dir = tmp_path / "slides"
        images_dir.mkdir()
        (images_dir / "slide-001.png").write_bytes(b"image 1")
        (images_dir / "slide-002.png").write_bytes(b"image 2")
        (images_dir / "slide-003.png").write_bytes(b"image 3")

        # Mock ffmpeg 成功执行
        mock_run.return_value = Mock(returncode=0, stdout=b'', stderr=b'')

        video_path = converter._images_to_video(
            str(images_dir), str(tmp_path), 5)

        # 验证创建了 concat 文件
        concat_file = images_dir / "concat.txt"
        assert concat_file.exists()

        # 验证 concat 文件内容
        content = concat_file.read_text()
        assert "file '" in content
        assert "duration 5" in content

        # 验证 ffmpeg 命令调用
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert 'ffmpeg' in call_args[0]
        assert '-f' in call_args
        assert 'concat' in call_args
        assert '-c:v' in call_args
        assert 'libx264' in call_args

        # 验证返回路径
        assert video_path.endswith('.mp4')

    @patch('os.remove')
    @patch('shutil.rmtree')
    def test_cleanup(self, mock_rmtree, mock_remove, converter, tmp_path):
        """测试清理临时文件"""
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"fake pdf")
        images_dir = tmp_path / "slides"
        images_dir.mkdir()

        converter._cleanup(str(pdf_path), str(images_dir))

        # 验证删除操作被调用
        mock_remove.assert_called_once()
        mock_rmtree.assert_called_once()

    @patch('subprocess.run')
    def test_generate_thumbnail(self, mock_run, converter, tmp_path):
        """测试生成视频缩略图"""
        video_path = tmp_path / "video.mp4"
        video_path.write_bytes(b"fake video")
        output_path = tmp_path / "thumbnail.jpg"

        # Mock ffmpeg 成功执行
        mock_run.return_value = Mock(returncode=0, stdout=b'', stderr=b'')

        result_path = converter.generate_thumbnail(
            str(video_path), str(output_path))

        # 验证 ffmpeg 命令调用
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert 'ffmpeg' in call_args[0]
        assert '-i' in call_args
        assert '-ss' in call_args
        assert '00:00:01' in call_args  # 第 1 秒
        assert '-vframes' in call_args
        assert '1' in call_args
        assert '-vf' in call_args
        assert 'scale=320:-1' in call_args  # 缩放到 320px 宽度

        # 验证返回路径
        assert result_path == str(output_path)

    def test_calculate_md5(self, converter, tmp_path):
        """测试计算文件 MD5"""
        test_file = tmp_path / "test.txt"
        test_file.write_bytes(b"test content")

        md5 = converter.calculate_md5(str(test_file))

        # 验证 MD5 格式正确（32 位十六进制）
        assert len(md5) == 32
        assert all(c in '0123456789abcdef' for c in md5)

    @patch('subprocess.run')
    def test_convert_to_video_full_flow(
        self, mock_run, converter, sample_ppt_path, tmp_path
    ):
        """测试完整的 PPT 转视频流程"""
        # Mock 所有 subprocess 调用成功
        mock_run.return_value = Mock(returncode=0, stdout=b'', stderr=b'')

        # 执行转换
        video_path = converter.convert_to_video(
            sample_ppt_path, str(tmp_path), 5)

        # 验证最终返回视频路径
        assert video_path.endswith('.mp4')


class TestPPTConverterErrors:
    """PPT 转换器错误处理测试"""

    @pytest.fixture
    def converter(self):
        return PPTConverter()

    @pytest.fixture
    def sample_ppt_path(self, tmp_path):
        """创建临时 PPT 文件路径"""
        ppt_file = tmp_path / "test.pptx"
        ppt_file.write_bytes(b"fake ppt content")
        return str(ppt_file)

    @patch('subprocess.run')
    def test_convert_to_pdf_error(self, mock_run, converter, sample_ppt_path, tmp_path):
        """测试 PPT 转 PDF 失败处理"""
        # Mock subprocess 失败
        mock_run.side_effect = Exception("LibreOffice not found")

        with pytest.raises(Exception) as exc_info:
            converter._convert_to_pdf(sample_ppt_path, str(tmp_path))

        assert "LibreOffice" in str(exc_info.value)

    @patch('subprocess.run')
    def test_pdf_to_images_both_methods_fail(self, mock_run, converter, tmp_path):
        """测试 PDF 转图片两种方法都失败"""
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"fake pdf")

        # Mock 两种方法都失败
        mock_run.side_effect = [
            subprocess.CalledProcessError(1, 'pdftoppm'),
            subprocess.CalledProcessError(1, 'convert')
        ]

        with pytest.raises(Exception) as exc_info:
            converter._pdf_to_images(str(pdf_path), str(tmp_path))

        # 验证错误信息包含转换失败
        assert "PDF to images conversion failed" in str(exc_info.value)

    @patch('subprocess.run')
    def test_images_to_video_no_images(self, mock_run, converter, tmp_path):
        """测试图片序列转视频 - 没有图片文件"""
        images_dir = tmp_path / "slides"
        images_dir.mkdir()

        with pytest.raises(Exception) as exc_info:
            converter._images_to_video(str(images_dir), str(tmp_path), 5)

        assert "No images found" in str(exc_info.value)

    @patch('subprocess.run')
    def test_generate_thumbnail_error(self, mock_run, converter, tmp_path):
        """测试生成缩略图失败"""
        video_path = tmp_path / "video.mp4"
        video_path.write_bytes(b"fake video")
        output_path = tmp_path / "thumb.jpg"

        # Mock ffmpeg 失败
        mock_run.side_effect = subprocess.CalledProcessError(1, 'ffmpeg')

        with pytest.raises(Exception) as exc_info:
            converter.generate_thumbnail(str(video_path), str(output_path))

        # 验证错误信息
        assert "thumbnail generation failed" in str(exc_info.value)
