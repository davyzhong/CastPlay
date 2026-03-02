"""
PPT Converter Service
"""
import os
import subprocess
import hashlib
import logging
from typing import Optional, List

from flask import current_app

logger = logging.getLogger(__name__)


class PPTConverter:
    """PPT 转视频转换器"""

    def __init__(
        self,
        libreoffice_path: Optional[str] = None,
        ffmpeg_path: Optional[str] = None
    ) -> None:
        self.libreoffice_path = libreoffice_path or '/usr/bin/soffice'
        self.ffmpeg_path = ffmpeg_path or '/usr/bin/ffmpeg'

    def convert_to_video(
        self,
        ppt_path: str,
        output_dir: str,
        duration_per_slide: int = 5
    ) -> str:
        """
        将 PPT 转换为视频

        Args:
            ppt_path: PPT 文件路径
            output_dir: 输出目录
            duration_per_slide: 每张幻灯片持续时间（秒）

        Returns:
            str: 转换后的视频文件路径
        """
        # 第一步：PPT 转 PDF
        pdf_path = self._convert_to_pdf(ppt_path, output_dir)

        # 第二步：PDF 转图片序列
        images_dir = self._pdf_to_images(pdf_path, output_dir)

        # 第三步：图片序列转视频
        video_path = self._images_to_video(
            images_dir,
            output_dir,
            duration_per_slide
        )

        # 清理临时文件
        self._cleanup(pdf_path, images_dir)

        return video_path

    def _convert_to_pdf(self, ppt_path: str, output_dir: str) -> str:
        """将 PPT 转换为 PDF"""
        try:
            cmd = [
                self.libreoffice_path,
                '--headless',
                '--convert-to', 'pdf',
                '--outdir', output_dir,
                ppt_path
            ]

            subprocess.run(cmd, check=True, capture_output=True)

            # 获取生成的 PDF 文件路径
            base_name = os.path.splitext(os.path.basename(ppt_path))[0]
            pdf_path = os.path.join(output_dir, f"{base_name}.pdf")

            return pdf_path

        except subprocess.CalledProcessError as e:
            raise Exception(
                f"PPT to PDF conversion failed: {e.stderr.decode()}")

    def _pdf_to_images(self, pdf_path: str, output_dir: str) -> str:
        """将 PDF 转换为图片序列"""
        images_dir = os.path.join(output_dir, 'slides')
        os.makedirs(images_dir, exist_ok=True)

        try:
            # 使用 pdftoppm 或 ImageMagick 的 convert 命令
            # 这里使用 pdftoppm（通常随 poppler-utils 安装）
            cmd = [
                'pdftoppm',
                '-png',
                '-r', '150',  # DPI
                pdf_path,
                os.path.join(images_dir, 'slide')
            ]

            subprocess.run(cmd, check=True, capture_output=True)

            return images_dir

        except subprocess.CalledProcessError as e:
            # 尝试使用 ImageMagick 作为备选
            try:
                cmd = [
                    'convert',
                    '-density', '150',
                    pdf_path,
                    os.path.join(images_dir, 'slide-%03d.png')
                ]
                subprocess.run(cmd, check=True, capture_output=True)
                return images_dir
            except subprocess.CalledProcessError:
                raise Exception(
                    f"PDF to images conversion failed: {e.stderr.decode()}")

    def _images_to_video(
        self,
        images_dir: str,
        output_dir: str,
        duration_per_slide: int
    ) -> str:
        """将图片序列转换为视频"""
        # 查找所有图片文件
        image_files = sorted([
            f for f in os.listdir(images_dir)
            if f.endswith('.png')
        ])

        if not image_files:
            raise Exception("No images found for video conversion")

        # 生成输出视频文件名
        output_video = os.path.join(
            output_dir,
            f"converted_{hashlib.md5(images_dir.encode()).hexdigest()[:8]}.mp4"
        )

        try:
            # 创建 ffmpeg concat 文件（使用绝对路径避免路径问题）
            concat_file = os.path.join(images_dir, 'concat.txt')
            abs_images_dir = os.path.abspath(images_dir)
            with open(concat_file, 'w') as f:
                for img in image_files:
                    # 使用绝对路径
                    img_path = os.path.join(abs_images_dir, img)
                    f.write(f"file '{img_path}'\n")
                    f.write(f"duration {duration_per_slide}\n")
                # 最后一张图片需要再写一次（ffmpeg 要求）
                f.write(
                    f"file '{os.path.join(abs_images_dir, image_files[-1])}'\n")

            # 使用 ffmpeg 转换
            cmd = [
                self.ffmpeg_path,
                '-f', 'concat',
                '-safe', '0',
                '-i', concat_file,
                '-vsync', 'vfr',
                '-pix_fmt', 'yuv420p',
                '-c:v', 'libx264',
                '-preset', 'medium',
                '-crf', '23',
                output_video
            ]

            subprocess.run(cmd, check=True, capture_output=True)

            return output_video

        except subprocess.CalledProcessError as e:
            raise Exception(
                f"Images to video conversion failed: {e.stderr.decode()}")

    def _cleanup(self, pdf_path: str, images_dir: str) -> None:
        """清理临时文件"""
        try:
            # 删除 PDF 文件
            if os.path.exists(pdf_path):
                os.remove(pdf_path)

            # 删除图片目录
            if os.path.exists(images_dir):
                import shutil
                shutil.rmtree(images_dir)
        except Exception:
            pass  # 清理失败不影响主流程

    def generate_thumbnail(self, video_path: str, output_path: str) -> str:
        """生成视频缩略图"""
        try:
            cmd = [
                self.ffmpeg_path,
                '-i', video_path,
                '-ss', '00:00:01',
                '-vframes', '1',
                '-vf', 'scale=320:-1',
                output_path
            ]

            subprocess.run(cmd, check=True, capture_output=True)

            return output_path

        except subprocess.CalledProcessError as e:
            raise Exception(
                f"Thumbnail generation failed: {e.stderr.decode()}")

    def calculate_md5(self, file_path: str) -> str:
        """计算文件 MD5"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
