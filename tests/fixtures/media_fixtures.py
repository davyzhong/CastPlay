"""
媒体文件测试数据 fixtures

提供用于测试的媒体文件生成器
"""
from pathlib import Path
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import pytest


# ============================================================================
# 图片生成器
# ============================================================================

class ImageGenerator:
    """测试图片生成器"""

    @staticmethod
    def create_test_image(width=800, height=600, color="red"):
        """创建测试图片"""
        img = Image.new("RGB", (width, height), color=color)
        return img

    @staticmethod
    def create_test_image_bytes(width=800, height=600, color="red", format="JPEG"):
        """创建测试图片字节流"""
        img = Image.new("RGB", (width, height), color=color)
        img_io = BytesIO()
        img.save(img_io, format=format)
        img_io.seek(0)
        return img_io

    @staticmethod
    def create_colored_image(width=800, height=600):
        """创建彩色测试图片"""
        img = Image.new("RGB", (width, height))
        draw = ImageDraw.Draw(img)

        # 绘制不同颜色的方块
        colors = ["red", "green", "blue", "yellow", "purple"]
        square_size = width // 5

        for i, color in enumerate(colors):
            x1 = i * square_size
            x2 = x1 + square_size
            draw.rectangle([x1, 0, x2, height], fill=color)

        return img

    @staticmethod
    def create_test_jpeg(size=(800, 600)):
        """创建测试 JPEG 图片"""
        img = Image.new("RGB", size, color="blue")
        img_io = BytesIO()
        img.save(img_io, format="JPEG")
        img_io.seek(0)
        return img_io

    @staticmethod
    def create_test_png(size=(800, 600)):
        """创建测试 PNG 图片"""
        img = Image.new("RGB", size, color="green")
        img_io = BytesIO()
        img.save(img_io, format="PNG")
        img_io.seek(0)
        return img_io

    @staticmethod
    def create_test_gif(size=(800, 600)):
        """创建测试 GIF 图片"""
        img = Image.new("RGB", size, color="yellow")
        img_io = BytesIO()
        img.save(img_io, format="GIF")
        img_io.seek(0)
        return img_io

    @staticmethod
    def create_test_bmp(size=(800, 600)):
        """创建测试 BMP 图片"""
        img = Image.new("RGB", size, color="orange")
        img_io = BytesIO()
        img.save(img_io, format="BMP")
        img_io.seek(0)
        return img_io


# ============================================================================
# 视频生成器
# ============================================================================

class VideoGenerator:
    """测试视频生成器"""

    @staticmethod
    def create_fake_mp4(size_kb=100):
        """创建假的 MP4 文件（仅文件头）"""
        # MP4 文件头
        header = b"ftypmp42\x00\x00\x00\x00mp42isom"
        # 填充数据
        padding = b"\x00" * (size_kb * 1024 - len(header))
        return BytesIO(header + padding)

    @staticmethod
    def create_fake_avi(size_kb=100):
        """创建假的 AVI 文件"""
        # AVI 文件头
        header = b"RIFF\x00\x00\x00\x00AVI "
        padding = b"\x00" * (size_kb * 1024 - len(header))
        return BytesIO(header + padding)

    @staticmethod
    def create_fake_mov(size_kb=100):
        """创建假的 MOV 文件"""
        # MOV 文件头
        header = b"\x00\x00\x00\x20ftypqt  "
        padding = b"\x00" * (size_kb * 1024 - len(header))
        return BytesIO(header + padding)


# ============================================================================
# PPT 生成器
# ============================================================================

class PPTGenerator:
    """测试 PPT 生成器"""

    @staticmethod
    def create_fake_pptx(size_kb=100):
        """创建假的 PPTX 文件（ZIP 格式）"""
        # PPTX 是 ZIP 格式
        header = b"PK\x03\x04"
        padding = b"\x00" * (size_kb * 1024 - len(header))
        return BytesIO(header + padding)

    @staticmethod
    def create_fake_ppt(size_kb=100):
        """创建假的 PPT 文件"""
        # 旧版 PPT 文件头
        header = b"\xD0\xCF\x11\xE0\xA1\xB1\x1A\xE1"
        padding = b"\x00" * (size_kb * 1024 - len(header))
        return BytesIO(header + padding)


# ============================================================================
# 通用文件生成器
# ============================================================================

class FileGenerator:
    """通用文件生成器"""

    @staticmethod
    def create_temp_image(output_dir=None, filename="test.jpg", size=(800, 600)):
        """创建临时图片文件"""
        img = Image.new("RGB", size, color="blue")
        img_io = BytesIO()
        img.save(img_io, format="JPEG")
        img_io.seek(0)

        if output_dir:
            output_path = Path(output_dir) / filename
            with open(output_path, "wb") as f:
                f.write(img_io.getvalue())
            return output_path
        return img_io

    @staticmethod
    def create_image_with_text(text="Test Image", size=(800, 600)):
        """创建带文字的图片"""
        img = Image.new("RGB", size, color="white")
        draw = ImageDraw.Draw(img)

        # 尝试使用默认字体
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 40)
        except:
            font = ImageFont.load_default()

        # 计算文字位置（居中）
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        x = (size[0] - text_width) // 2
        y = (size[1] - text_height) // 2

        draw.text((x, y), text, fill="black", font=font)
        return img


# ============================================================================
# Pytest Fixtures
# ============================================================================

@pytest.fixture
def sample_image_bytes():
    """返回测试图片字节流"""
    img = Image.new("RGB", (100, 100), color="blue")
    img_io = BytesIO()
    img.save(img_io, format="JPEG")
    img_io.seek(0)
    return img_io


@pytest.fixture
def sample_video_bytes():
    """返回测试视频字节流"""
    return VideoGenerator.create_fake_mp4(50)


@pytest.fixture
def sample_pptx_bytes():
    """返回测试 PPTX 字节流"""
    return PPTGenerator.create_fake_pptx(50)


@pytest.fixture
def sample_image_file(tmp_path):
    """返回测试图片文件路径"""
    img = Image.new("RGB", (100, 100), color="green")
    img_io = BytesIO()
    img.save(img_io, format="JPEG")
    img_io.seek(0)

    file_path = tmp_path / "sample.jpg"
    with open(file_path, "wb") as f:
        f.write(img_io.getvalue())

    return file_path


@pytest.fixture
def colored_test_image_bytes():
    """返回彩色测试图片字节流"""
    img = ImageGenerator.create_colored_image(400, 300)
    img_io = BytesIO()
    img.save(img_io, format="JPEG")
    img_io.seek(0)
    return img_io


@pytest.fixture
def sample_files():
    """返回多种类型的测试文件"""
    return {
        "image_jpg": ImageGenerator.create_test_jpeg(),
        "image_png": ImageGenerator.create_test_png(),
        "image_gif": ImageGenerator.create_test_gif(),
        "image_bmp": ImageGenerator.create_test_bmp(),
        "video_mp4": VideoGenerator.create_fake_mp4(),
        "video_avi": VideoGenerator.create_fake_avi(),
        "ppt_pptx": PPTGenerator.create_fake_pptx(),
        "ppt_ppt": PPTGenerator.create_fake_ppt(),
    }


# ============================================================================
# 批量生成器
# ============================================================================

class BatchGenerator:
    """批量文件生成器"""

    @staticmethod
    def create_multiple_images(count=5, size=(800, 600)):
        """创建多个测试图片"""
        images = []
        for i in range(count):
            color = [
                (i * 50) % 256,
                (i * 100) % 256,
                (i * 150) % 256
            ]
            img = Image.new("RGB", size, color=tuple(color))
            img_io = BytesIO()
            img.save(img_io, format="JPEG")
            img_io.seek(0)
            images.append(img_io)
        return images

    @staticmethod
    def create_image_sequence(start=0, count=10, size=(800, 600)):
        """创建带序号的图片序列"""
        images = []
        for i in range(start, start + count):
            img = Image.new("RGB", size, color=(i * 25, i * 25, i * 25))

            # 添加序号
            draw = ImageDraw.Draw(img)
            try:
                font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 40)
            except:
                font = ImageFont.load_default()
            draw.text((50, 50), str(i), fill="white", font=font)

            img_io = BytesIO()
            img.save(img_io, format="JPEG")
            img_io.seek(0)
            images.append(img_io)
        return images
