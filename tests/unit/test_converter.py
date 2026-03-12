"""
PPT 转换服务单元测试

测试 PPT 转换流程中的各个步骤
"""
import pytest
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, call


class TestPPTConverterInit:
    """PPT 转换器初始化测试"""

    def test_init_with_all_tools(self):
        """测试所有工具都可用时的初始化"""
        with patch.object(Path, 'exists', return_value=True):
            with patch('subprocess.run') as mock_run:
                mock_run.return_value = MagicMock(returncode=0, stdout='/usr/bin/ffmpeg\n')
                from app.services.converter import PPTConverter
                converter = PPTConverter()

                assert converter.libreoffice_path is not None or converter.ffmpeg_path is not None

    def test_init_without_tools(self):
        """测试没有工具时的初始化"""
        with patch.object(Path, 'exists', return_value=False):
            with patch('subprocess.run') as mock_run:
                mock_run.side_effect = Exception("Command not found")
                from app.services.converter import PPTConverter
                converter = PPTConverter()

                # 应该不抛出异常
                assert converter is not None


class TestFindLibreOffice:
    """LibreOffice 查找测试"""

    @patch('os.path.exists')
    def test_find_libreoffice_macos(self, mock_exists):
        """测试在 macOS 上查找 LibreOffice"""
        from app.services.converter import PPTConverter

        def exists_side_effect(path):
            return path == "/Applications/LibreOffice.app/Contents/MacOS/soffice"

        mock_exists.side_effect = exists_side_effect

        # 重新创建实例来测试查找
        converter = PPTConverter.__new__(PPTConverter)
        converter.libreoffice_path = converter._find_libreoffice()

        assert converter.libreoffice_path == "/Applications/LibreOffice.app/Contents/MacOS/soffice"

    @patch('os.path.exists')
    def test_find_libreoffice_linux(self, mock_exists):
        """测试在 Linux 上查找 LibreOffice"""
        from app.services.converter import PPTConverter

        def exists_side_effect(path):
            return path == "/usr/bin/libreoffice"

        mock_exists.side_effect = exists_side_effect

        converter = PPTConverter.__new__(PPTConverter)
        converter.libreoffice_path = converter._find_libreoffice()

        assert converter.libreoffice_path == "/usr/bin/libreoffice"

    @patch('os.path.exists', return_value=False)
    def test_find_libreoffice_not_found(self, mock_exists):
        """测试 LibreOffice 未找到"""
        from app.services.converter import PPTConverter

        converter = PPTConverter.__new__(PPTConverter)
        result = converter._find_libreoffice()

        assert result is None


class TestFindFFmpeg:
    """FFmpeg 查找测试"""

    @patch('subprocess.run')
    def test_find_ffmpeg_success(self, mock_run):
        """测试成功找到 FFmpeg"""
        from app.services.converter import PPTConverter

        mock_run.return_value = MagicMock(returncode=0, stdout='/usr/bin/ffmpeg\n')

        converter = PPTConverter.__new__(PPTConverter)
        result = converter._find_ffmpeg()

        assert result == '/usr/bin/ffmpeg'

    @patch('subprocess.run')
    def test_find_ffmpeg_not_found(self, mock_run):
        """测试 FFmpeg 未找到"""
        from app.services.converter import PPTConverter

        mock_run.return_value = MagicMock(returncode=1)

        converter = PPTConverter.__new__(PPTConverter)
        result = converter._find_ffmpeg()

        assert result is None

    @patch('subprocess.run')
    def test_find_ffmpeg_exception(self, mock_run):
        """测试查找 FFmpeg 时发生异常"""
        from app.services.converter import PPTConverter

        mock_run.side_effect = Exception("Command failed")

        converter = PPTConverter.__new__(PPTConverter)
        result = converter._find_ffmpeg()

        assert result is None


class TestIsAvailable:
    """工具可用性检查测试"""

    @patch('subprocess.run')
    def test_is_available_all_tools_present(self, mock_run):
        """测试所有工具都可用"""
        from app.services.converter import PPTConverter

        mock_run.return_value = MagicMock(returncode=0)

        with patch.object(Path, 'exists', return_value=True):
            converter = PPTConverter.__new__(PPTConverter)
            converter.libreoffice_path = "/usr/bin/libreoffice"
            converter.ffmpeg_path = "/usr/bin/ffmpeg"

            available, message = converter.is_available()

            assert available is True
            assert "available" in message.lower()

    def test_is_available_missing_libreoffice(self):
        """测试缺少 LibreOffice"""
        from app.services.converter import PPTConverter

        converter = PPTConverter.__new__(PPTConverter)
        converter.libreoffice_path = None
        converter.ffmpeg_path = "/usr/bin/ffmpeg"

        available, message = converter.is_available()

        assert available is False
        assert "LibreOffice" in message

    def test_is_available_missing_ffmpeg(self):
        """测试缺少 FFmpeg"""
        from app.services.converter import PPTConverter

        converter = PPTConverter.__new__(PPTConverter)
        converter.libreoffice_path = "/usr/bin/libreoffice"
        converter.ffmpeg_path = None

        available, message = converter.is_available()

        assert available is False
        assert "ffmpeg" in message

    def test_is_available_missing_all_tools(self):
        """测试缺少所有工具"""
        from app.services.converter import PPTConverter

        converter = PPTConverter.__new__(PPTConverter)
        converter.libreoffice_path = None
        converter.ffmpeg_path = None

        available, message = converter.is_available()

        assert available is False
        assert "LibreOffice" in message
        assert "ffmpeg" in message


class TestPPTtoPDF:
    """PPT 转 PDF 测试"""

    @pytest.fixture
    def converter(self):
        """创建转换器实例"""
        from app.services.converter import PPTConverter
        converter = PPTConverter.__new__(PPTConverter)
        converter.libreoffice_path = "/usr/bin/libreoffice"
        converter.ffmpeg_path = "/usr/bin/ffmpeg"
        return converter

    @patch('subprocess.run')
    @patch('pathlib.Path.mkdir')
    @patch('pathlib.Path.exists')
    def test_ppt_to_pdf_success(self, mock_exists, mock_mkdir, mock_run, converter):
        """测试 PPT 转 PDF 成功"""
        mock_run.return_value = MagicMock(returncode=0, stderr="")
        mock_exists.return_value = True

        with patch('app.services.converter.settings') as mock_settings:
            mock_settings.CONVERTED_DIR = Path("/tmp/converted")

            result = converter._ppt_to_pdf("/tmp/test.pptx")

            # 应该调用了 LibreOffice 命令
            assert mock_run.called
            call_args = mock_run.call_args[0][0]
            assert "soffice" in call_args[0] or "libreoffice" in call_args[0]

    @patch('subprocess.run')
    def test_ppt_to_pdf_libreoffice_error(self, mock_run, converter):
        """测试 LibreOffice 转换失败"""
        mock_run.return_value = MagicMock(
            returncode=1,
            stderr="LibreOffice error"
        )

        with patch('pathlib.Path.mkdir'):
            with patch('app.services.converter.settings') as mock_settings:
                mock_settings.CONVERTED_DIR = Path("/tmp/converted")

                result = converter._ppt_to_pdf("/tmp/test.pptx")

                assert result is None

    @patch('subprocess.run')
    def test_ppt_to_pdf_timeout(self, mock_run, converter):
        """测试 LibreOffice 转换超时"""
        import subprocess
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="libreoffice", timeout=120)

        with patch('pathlib.Path.mkdir'):
            with patch('app.services.converter.settings') as mock_settings:
                mock_settings.CONVERTED_DIR = Path("/tmp/converted")

                result = converter._ppt_to_pdf("/tmp/test.pptx")

                assert result is None

    def test_ppt_to_pdf_no_libreoffice(self, converter):
        """测试没有 LibreOffice"""
        converter.libreoffice_path = None

        result = converter._ppt_to_pdf("/tmp/test.pptx")

        assert result is None


class TestPDFtoImages:
    """PDF 转图片测试"""

    @pytest.fixture
    def converter(self):
        """创建转换器实例"""
        from app.services.converter import PPTConverter
        converter = PPTConverter.__new__(PPTConverter)
        converter.libreoffice_path = "/usr/bin/libreoffice"
        converter.ffmpeg_path = "/usr/bin/ffmpeg"
        return converter

    @patch('subprocess.run')
    @patch('pathlib.Path.glob')
    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.mkdir')
    def test_pdf_to_images_success(self, mock_mkdir, mock_exists, mock_glob, mock_run, converter):
        """测试 PDF 转图片成功"""
        mock_run.return_value = MagicMock(returncode=0, stderr="")
        mock_exists.return_value = True
        mock_glob.return_value = [Path("/tmp/slides/slide-1.jpg")]

        with patch('app.services.converter.settings') as mock_settings:
            mock_settings.CONVERTED_DIR = Path("/tmp/converted")

            result = converter._pdf_to_images("/tmp/test.pdf")

            assert mock_run.called

    @patch('subprocess.run')
    def test_pdf_to_images_fallback_to_imagemagick(self, mock_run, converter):
        """测试 pdftoppm 失败时回退到 ImageMagick"""
        # 第一次调用 pdftoppm 失败
        # 第二次调用 ImageMagick 成功
        mock_run.side_effect = [
            MagicMock(returncode=1, stderr="pdftoppm error"),
            MagicMock(returncode=0, stderr="")
        ]

        with patch('pathlib.Path.mkdir'):
            with patch('pathlib.Path.exists', return_value=True):
                with patch('pathlib.Path.glob') as mock_glob:
                    mock_glob.return_value = [Path("/tmp/slides/slide-0.jpg")]

                    with patch('app.services.converter.settings') as mock_settings:
                        mock_settings.CONVERTED_DIR = Path("/tmp/converted")

                        result = converter._pdf_to_images("/tmp/test.pdf")

                        # 应该调用了两次 run（pdftoppm 和 ImageMagick）
                        assert mock_run.call_count == 2


class TestImagesToVideo:
    """图片转视频测试"""

    @pytest.fixture
    def converter(self):
        """创建转换器实例"""
        from app.services.converter import PPTConverter
        converter = PPTConverter.__new__(PPTConverter)
        converter.libreoffice_path = "/usr/bin/libreoffice"
        converter.ffmpeg_path = "/usr/bin/ffmpeg"
        return converter

    @patch('subprocess.run')
    @patch('pathlib.Path.exists')
    def test_images_to_video_success(self, mock_exists, mock_run, converter):
        """测试图片转视频成功"""
        mock_run.return_value = MagicMock(returncode=0, stderr="")
        mock_exists.return_value = True

        with patch('app.services.converter.settings') as mock_settings:
            mock_settings.CONVERTED_DIR = Path("/tmp/converted")

            result = converter._images_to_video("/tmp/slides", "/tmp/test.pptx")

            assert mock_run.called
            call_args = mock_run.call_args[0][0]
            assert "ffmpeg" in call_args[0]

    @patch('subprocess.run')
    def test_images_to_video_ffmpeg_error(self, mock_run, converter):
        """测试 FFmpeg 转换失败"""
        mock_run.return_value = MagicMock(
            returncode=1,
            stderr="FFmpeg error"
        )

        with patch('pathlib.Path.exists', return_value=False):
            with patch('app.services.converter.settings') as mock_settings:
                mock_settings.CONVERTED_DIR = Path("/tmp/converted")

                result = converter._images_to_video("/tmp/slides", "/tmp/test.pptx")

                assert result is None

    def test_images_to_video_no_ffmpeg(self, converter):
        """测试没有 FFmpeg"""
        converter.ffmpeg_path = None

        result = converter._images_to_video("/tmp/slides", "/tmp/test.pptx")

        assert result is None


class TestGenerateVideoThumbnail:
    """生成视频缩略图测试"""

    @pytest.fixture
    def converter(self):
        """创建转换器实例"""
        from app.services.converter import PPTConverter
        converter = PPTConverter.__new__(PPTConverter)
        converter.libreoffice_path = "/usr/bin/libreoffice"
        converter.ffmpeg_path = "/usr/bin/ffmpeg"
        return converter

    @patch('subprocess.run')
    @patch('pathlib.Path.exists')
    def test_generate_thumbnail_success(self, mock_exists, mock_run, converter):
        """测试生成缩略图成功"""
        mock_run.return_value = MagicMock(returncode=0, stderr="")
        mock_exists.return_value = True

        with patch('app.services.converter.settings') as mock_settings:
            mock_settings.THUMBNAILS_DIR = Path("/tmp/thumbnails")

            result = converter._generate_video_thumbnail("/tmp/test.mp4")

            assert mock_run.called
            assert result is not None

    @patch('subprocess.run')
    @patch('pathlib.Path.exists')
    def test_generate_thumbnail_failure(self, mock_exists, mock_run, converter):
        """测试生成缩略图失败"""
        mock_run.return_value = MagicMock(
            returncode=1,
            stderr="FFmpeg error"
        )
        mock_exists.return_value = False

        result = converter._generate_video_thumbnail("/tmp/test.mp4")

        assert result is None


class TestGetVideoDuration:
    """获取视频时长测试"""

    @pytest.fixture
    def converter(self):
        """创建转换器实例"""
        from app.services.converter import PPTConverter
        converter = PPTConverter.__new__(PPTConverter)
        converter.libreoffice_path = "/usr/bin/libreoffice"
        converter.ffmpeg_path = "/usr/bin/ffmpeg"
        return converter

    @patch('subprocess.run')
    def test_get_duration_success(self, mock_run, converter):
        """测试获取视频时长成功"""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="Duration: 00:01:30.00, start: 0.000000, bitrate: 1000 kb/s\n"
        )

        result = converter._get_video_duration("/tmp/test.mp4")

        assert result == 90.0  # 1分30秒

    @patch('subprocess.run')
    def test_get_duration_no_duration_in_output(self, mock_run, converter):
        """测试输出中没有时长信息"""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="No duration info here"
        )

        result = converter._get_video_duration("/tmp/test.mp4")

        assert result is None

    @patch('subprocess.run')
    def test_get_duration_exception(self, mock_run, converter):
        """测试获取时长时发生异常"""
        mock_run.side_effect = Exception("FFmpeg error")

        result = converter._get_video_duration("/tmp/test.mp4")

        assert result is None


class TestCleanupTempFiles:
    """临时文件清理测试"""

    @pytest.fixture
    def converter(self):
        """创建转换器实例"""
        from app.services.converter import PPTConverter
        converter = PPTConverter.__new__(PPTConverter)
        return converter

    @patch('os.path.exists')
    @patch('os.remove')
    @patch('shutil.rmtree')
    def test_cleanup_success(self, mock_rmtree, mock_remove, mock_exists, converter):
        """测试清理临时文件成功"""
        mock_exists.return_value = True

        converter._cleanup_temp_files("/tmp/test.pdf", "/tmp/slides")

        mock_remove.assert_called_once_with("/tmp/test.pdf")
        mock_rmtree.assert_called_once_with("/tmp/slides")

    @patch('os.path.exists')
    @patch('os.remove')
    def test_cleanup_pdf_not_exists(self, mock_remove, mock_exists, converter):
        """测试 PDF 文件不存在"""
        mock_exists.return_value = False

        converter._cleanup_temp_files("/tmp/test.pdf", None)

        mock_remove.assert_not_called()

    @patch('os.path.exists')
    @patch('os.remove')
    def test_cleanup_handles_exception(self, mock_remove, mock_exists, converter):
        """测试清理时处理异常"""
        mock_exists.return_value = True
        mock_remove.side_effect = Exception("Permission denied")

        # 应该不抛出异常
        converter._cleanup_temp_files("/tmp/test.pdf", None)


class TestConvert:
    """完整转换流程测试"""

    @pytest.fixture
    def converter(self):
        """创建转换器实例"""
        from app.services.converter import PPTConverter
        converter = PPTConverter.__new__(PPTConverter)
        converter.libreoffice_path = "/usr/bin/libreoffice"
        converter.ffmpeg_path = "/usr/bin/ffmpeg"
        return converter

    def test_convert_success(self, converter):
        """测试完整转换成功"""
        with patch.object(converter, '_ppt_to_pdf', return_value="/tmp/test.pdf"):
            with patch.object(converter, '_pdf_to_images', return_value="/tmp/slides"):
                with patch.object(converter, '_images_to_video', return_value="/tmp/test.mp4"):
                    with patch.object(converter, '_generate_video_thumbnail', return_value="/tmp/thumb.jpg"):
                        with patch.object(converter, '_get_video_duration', return_value=90.0):
                            with patch.object(converter, '_cleanup_temp_files'):
                                result = converter.convert("/tmp/test.pptx", 1)

                                assert result["success"] is True
                                assert result["converted_path"] == "/tmp/test.mp4"
                                assert result["thumbnail_path"] == "/tmp/thumb.jpg"
                                assert result["duration"] == 90.0

    def test_convert_ppt_to_pdf_fails(self, converter):
        """测试 PPT 转 PDF 失败"""
        with patch.object(converter, '_ppt_to_pdf', return_value=None):
            result = converter.convert("/tmp/test.pptx", 1)

            assert result["success"] is False
            assert "error" in result

    def test_convert_pdf_to_images_fails(self, converter):
        """测试 PDF 转图片失败"""
        with patch.object(converter, '_ppt_to_pdf', return_value="/tmp/test.pdf"):
            with patch.object(converter, '_pdf_to_images', return_value=None):
                result = converter.convert("/tmp/test.pptx", 1)

                assert result["success"] is False

    def test_convert_images_to_video_fails(self, converter):
        """测试图片转视频失败"""
        with patch.object(converter, '_ppt_to_pdf', return_value="/tmp/test.pdf"):
            with patch.object(converter, '_pdf_to_images', return_value="/tmp/slides"):
                with patch.object(converter, '_images_to_video', return_value=None):
                    result = converter.convert("/tmp/test.pptx", 1)

                    assert result["success"] is False

    def test_convert_exception_handling(self, converter):
        """测试转换异常处理"""
        with patch.object(converter, '_ppt_to_pdf', side_effect=Exception("Unexpected error")):
            result = converter.convert("/tmp/test.pptx", 1)

            assert result["success"] is False
            assert "Unexpected error" in result["error"]
