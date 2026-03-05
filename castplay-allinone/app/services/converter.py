"""
PPT 转换服务
支持 PPT → PDF → 图片序列 → 视频的转换流程
"""
import subprocess
import os
from pathlib import Path
from typing import Optional, Tuple
from loguru import logger

from app.config import settings
from app.utils.file_utils import (
    calculate_md5,
    generate_thumbnail,
    get_unique_filename
)


class PPTConverter:
    """
    PPT 转换器

    转换流程：PPT → PDF → 图片序列 → 视频
    """

    def __init__(self):
        """初始化转换器"""
        self.libreoffice_path = self._find_libreoffice()
        self.ffmpeg_path = self._find_ffmpeg()

    def _find_libreoffice(self) -> Optional[str]:
        """查找 LibreOffice 可执行文件"""
        possible_paths = [
            "/Applications/LibreOffice.app/Contents/MacOS/soffice",  # macOS
            "/usr/bin/libreoffice",  # Linux
            "/usr/bin/soffice",  # Linux
            "C:\\Program Files\\LibreOffice\\program\\soffice.exe",  # Windows
            "C:\\Program Files (x86)\\LibreOffice\\program\\soffice.exe",  # Windows x86
        ]

        for path in possible_paths:
            if os.path.exists(path):
                return path

        return None

    def _find_ffmpeg(self) -> Optional[str]:
        """查找 ffmpeg 可执行文件"""
        try:
            result = subprocess.run(["which", "ffmpeg"], capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass

        return None

    def convert(self, file_path: str, media_id: int) -> dict:
        """
        执行完整的 PPT 转换流程

        Args:
            file_path: PPT 文件路径
            media_id: 媒体文件 ID（用于更新数据库）

        Returns:
            转换结果字典
        """
        logger.info(f"Starting PPT conversion: {file_path}")

        try:
            # 步骤 1: PPT → PDF
            pdf_path = self._ppt_to_pdf(file_path)
            if not pdf_path:
                raise Exception("Failed to convert PPT to PDF")

            # 步骤 2: PDF → 图片序列
            images_dir = self._pdf_to_images(pdf_path)
            if not images_dir:
                raise Exception("Failed to convert PDF to images")

            # 步骤 3: 图片序列 → 视频
            video_path = self._images_to_video(images_dir, file_path)
            if not video_path:
                raise Exception("Failed to convert images to video")

            # 步骤 4: 生成缩略图
            thumbnail_path = self._generate_video_thumbnail(video_path)

            # 步骤 5: 计算视频时长
            duration = self._get_video_duration(video_path)

            # 清理临时文件
            self._cleanup_temp_files(pdf_path, images_dir)

            logger.info(f"PPT conversion completed: {video_path}")

            return {
                "success": True,
                "converted_path": video_path,
                "thumbnail_path": thumbnail_path,
                "duration": duration
            }

        except Exception as e:
            logger.error(f"PPT conversion failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def _ppt_to_pdf(self, ppt_path: str) -> Optional[str]:
        """
        将 PPT 转换为 PDF

        Args:
            ppt_path: PPT 文件路径

        Returns:
            PDF 文件路径，失败返回 None
        """
        if not self.libreoffice_path:
            logger.error("LibreOffice not found!")
            return None

        try:
            # 创建输出目录
            output_dir = settings.CONVERTED_DIR
            output_dir.mkdir(exist_ok=True)

            # 执行 LibreOffice 转换命令
            cmd = [
                self.libreoffice_path,
                "--headless",
                "--convert-to", "pdf",
                "--outdir", str(output_dir),
                ppt_path
            ]

            logger.info(f"Running: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

            if result.returncode != 0:
                logger.error(f"LibreOffice error: {result.stderr}")
                return None

            # 生成的 PDF 文件路径
            pdf_path = output_dir / f"{Path(ppt_path).stem}.pdf"

            if pdf_path.exists():
                logger.info(f"PDF created: {pdf_path}")
                return str(pdf_path)
            else:
                logger.error("PDF file not found after conversion")
                return None

        except subprocess.TimeoutExpired:
            logger.error("LibreOffice conversion timed out")
            return None
        except Exception as e:
            logger.error(f"PPT to PDF conversion failed: {e}")
            return None

    def _pdf_to_images(self, pdf_path: str) -> Optional[str]:
        """
        将 PDF 转换为图片序列

        Args:
            pdf_path: PDF 文件路径

        Returns:
            图片目录路径，失败返回 None
        """
        try:
            # 创建输出目录
            output_dir = settings.CONVERTED_DIR / "slides"
            output_dir.mkdir(exist_ok=True)

            # 使用 pdftoppm 或 ImageMagick 转换
            # 优先使用 pdftoppm，使用 300 DPI 获得更高质量的图片
            cmd = ["pdftoppm", "-jpeg", "-r", "300", pdf_path, str(output_dir / "slide")]

            logger.info(f"Running: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

            if result.returncode != 0:
                logger.warning(f"pdftoppm error, trying ImageMagick: {result.stderr}")
                # 尝试使用 ImageMagick
                return self._pdf_to_images_imagemagick(pdf_path, output_dir)

            if output_dir.exists() and list(output_dir.glob("slide-*.jpg")):
                logger.info(f"Images created in: {output_dir}")
                return str(output_dir)
            else:
                logger.error("No images generated")
                return None

        except Exception as e:
            logger.error(f"PDF to images conversion failed: {e}")
            return None

    def _pdf_to_images_imagemagick(self, pdf_path: str, output_dir: Path) -> Optional[str]:
        """
        使用 ImageMagick 将 PDF 转换为图片

        Args:
            pdf_path: PDF 文件路径
            output_dir: 输出目录

        Returns:
            图片目录路径，失败返回 None
        """
        try:
            cmd = ["convert", pdf_path, str(output_dir / "slide-%d.jpg")]

            logger.info(f"Running ImageMagick: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

            if result.returncode != 0:
                logger.error(f"ImageMagick error: {result.stderr}")
                return None

            if output_dir.exists() and list(output_dir.glob("slide-*.jpg")):
                logger.info(f"Images created with ImageMagick: {output_dir}")
                return str(output_dir)
            else:
                return None

        except FileNotFoundError:
            logger.warning("ImageMagick convert not found, using pdftoppm only")
            return None
        except Exception as e:
            logger.error(f"ImageMagick conversion failed: {e}")
            return None

    def _images_to_video(self, images_dir: str, original_path: str) -> Optional[str]:
        """
        将图片序列转换为视频

        Args:
            images_dir: 图片目录
            original_path: 原始文件路径（用于命名）

        Returns:
            视频文件路径，失败返回 None
        """
        if not self.ffmpeg_path:
            logger.error("ffmpeg not found!")
            return None

        try:
            # 创建输出视频文件名
            original_name = Path(original_path).stem
            output_path = settings.CONVERTED_DIR / f"{original_name}.mp4"

            # 构建 ffmpeg 命令
            # 注意：pdftoppm 生成的文件名是 slide-1.jpg, slide-2.jpg（不是 slide-01.jpg）
            # 使用 %d 模式匹配
            cmd = [
                self.ffmpeg_path,
                "-y",  # 覆盖输出文件
                "-framerate", "1/5",  # 每张幻灯片 5 秒
                "-i", f"{images_dir}/slide-%d.jpg",  # 输入文件模式
                "-c:v", "libx264",  # 视频编码
                "-pix_fmt", "yuv420p",  # 像素格式
                "-preset", "fast",  # 编码预设
                "-crf", "23",  # 质量控制
                "-vf", "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:black",  # 缩放到 1080p 并居中加黑边
                str(output_path)
            ]

            logger.info(f"Running: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

            if result.returncode != 0:
                logger.error(f"ffmpeg error: {result.stderr}")
                return None

            if output_path.exists():
                logger.info(f"Video created: {output_path}")
                return str(output_path)
            else:
                logger.error("Video file not found after conversion")
                return None

        except Exception as e:
            logger.error(f"Images to video conversion failed: {e}")
            return None

    def _generate_video_thumbnail(self, video_path: str) -> Optional[str]:
        """
        生成视频缩略图

        Args:
            video_path: 视频文件路径

        Returns:
            缩略图路径
        """
        try:
            # 生成缩略图文件名
            original_name = Path(video_path).stem
            thumbnail_path = settings.THUMBNAILS_DIR / f"thumb_{original_name}.jpg"

            # 构建 ffmpeg 命令，生成 640 像素宽度的缩略图
            cmd = [
                self.ffmpeg_path,
                "-i", video_path,
                "-ss", "00:00:01",  # 从第 1 秒开始
                "-vframes", "1",  # 只取 1 帧
                "-vf", "scale=640:-1",  # 缩放到宽度 640
                "-y",
                str(thumbnail_path)
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode == 0 and thumbnail_path.exists():
                logger.info(f"Thumbnail created: {thumbnail_path}")
                return str(thumbnail_path)
            else:
                logger.warning(f"Failed to create thumbnail: {result.stderr}")
                return None

        except Exception as e:
            logger.warning(f"Thumbnail generation failed: {e}")
            return None

    def _get_video_duration(self, video_path: str) -> Optional[float]:
        """
        获取视频时长（秒）

        Args:
            video_path: 视频文件路径

        Returns:
            视频时长（秒）
        """
        try:
            cmd = [
                self.ffmpeg_path,
                "-i", video_path,
                "-f", "null",
                "-"
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, stderr=subprocess.STDOUT, timeout=30)

            # 解析输出获取时长
            for line in result.stdout.split('\n'):
                if 'Duration:' in line:
                    duration_part = line.split('Duration:')[1].split(',')[0].strip()
                    h, m, s = duration_part.split(':')
                    duration = float(h) * 3600 + float(m) * 60 + float(s)
                    logger.info(f"Video duration: {duration} seconds")
                    return duration

            return None

        except Exception as e:
            logger.warning(f"Failed to get video duration: {e}")
            return None

    def _cleanup_temp_files(self, pdf_path: Optional[str], images_dir: Optional[str]):
        """
        清理临时文件

        Args:
            pdf_path: PDF 文件路径
            images_dir: 图片目录路径
        """
        try:
            if pdf_path and os.path.exists(pdf_path):
                os.remove(pdf_path)
                logger.info(f"Deleted PDF: {pdf_path}")

            if images_dir and os.path.exists(images_dir):
                import shutil
                shutil.rmtree(images_dir)
                logger.info(f"Deleted images dir: {images_dir}")

        except Exception as e:
            logger.warning(f"Cleanup failed: {e}")

    def is_available(self) -> Tuple[bool, str]:
        """
        检查转换工具是否可用

        Returns:
            (是否可用, 状态消息)
        """
        issues = []

        if not self.libreoffice_path:
            issues.append("LibreOffice not found. Please install LibreOffice.")
        if not self.ffmpeg_path:
            issues.append("ffmpeg not found. Please install ffmpeg.")

        # 检查 pdftoppm
        try:
            subprocess.run(["which", "pdftoppm"], capture_output=True, check=True)
        except Exception:
            issues.append("pdftoppm not found. Using ImageMagick as fallback.")

        if issues:
            return False, "; ".join(issues)
        else:
            return True, "All conversion tools are available."
