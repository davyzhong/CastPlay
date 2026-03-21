"""
PPT Converter MCP Server

Provides MCP tools for PPT to PDF, images, and video conversion.
"""
import os
import sys
import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import Optional

from mcp.server import FastMCP
from loguru import logger

# Configure logging
logger.remove()
logger.add(sys.stderr, level="INFO")

mcp = FastMCP("castplay-ppt-converter")


class PPTConverter:
    """PPT conversion utilities"""

    def __init__(self):
        self.libreoffice_path = self._find_libreoffice()
        self.ffmpeg_path = self._find_ffmpeg()

    def _find_libreoffice(self) -> Optional[str]:
        """Find LibreOffice executable"""
        possible_paths = [
            "/Applications/LibreOffice.app/Contents/MacOS/soffice",  # macOS
            "/usr/bin/libreoffice",  # Linux
            "/usr/bin/soffice",  # Linux
            "C:\\Program Files\\LibreOffice\\program\\soffice.exe",  # Windows
        ]
        for path in possible_paths:
            if os.path.exists(path):
                return path
        return None

    def _find_ffmpeg(self) -> Optional[str]:
        """Find ffmpeg executable"""
        try:
            result = subprocess.run(["which", "ffmpeg"], capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip()
        except (OSError, subprocess.SubprocessError):
            pass
        return None

    def _find_pdftoppm(self) -> Optional[str]:
        """Find pdftoppm executable"""
        try:
            result = subprocess.run(["which", "pdftoppm"], capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip()
        except (OSError, subprocess.SubprocessError):
            pass
        return None


converter = PPTConverter()


@mcp.tool()
def get_ppt_info(ppt_path: str) -> dict:
    """
    Get information about a PPT file.

    Args:
        ppt_path: Path to the PPT file

    Returns:
        Dictionary with file information including page count, size, etc.
    """
    path = Path(ppt_path)
    if not path.exists():
        return {"success": False, "error": f"File not found: {ppt_path}"}

    if not path.suffix.lower() in [".ppt", ".pptx", ".odp"]:
        return {"success": False, "error": "File must be a PPT, PPTX, or ODP file"}

    file_size = path.stat().st_size

    return {
        "success": True,
        "file_name": path.name,
        "file_size_bytes": file_size,
        "file_size_mb": round(file_size / (1024 * 1024), 2),
        "extension": path.suffix.lower(),
        "path": str(path.absolute()),
    }


@mcp.tool()
def ppt_to_pdf(ppt_path: str, output_dir: Optional[str] = None) -> dict:
    """
    Convert a PPT file to PDF.

    Args:
        ppt_path: Path to the PPT file
        output_dir: Output directory (defaults to same directory as PPT file)

    Returns:
        Dictionary with conversion result including PDF path
    """
    if not converter.libreoffice_path:
        return {
            "success": False,
            "error": "LibreOffice not found. Please install LibreOffice."
        }

    path = Path(ppt_path)
    if not path.exists():
        return {"success": False, "error": f"File not found: {ppt_path}"}

    if output_dir:
        out_dir = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
    else:
        out_dir = path.parent

    try:
        cmd = [
            converter.libreoffice_path,
            "--headless",
            "--convert-to", "pdf",
            "--outdir", str(out_dir),
            str(path.absolute())
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

        if result.returncode != 0:
            return {
                "success": False,
                "error": f"LibreOffice error: {result.stderr}"
            }

        pdf_path = out_dir / f"{path.stem}.pdf"
        if pdf_path.exists():
            return {
                "success": True,
                "pdf_path": str(pdf_path.absolute()),
                "file_size_bytes": pdf_path.stat().st_size
            }
        else:
            return {"success": False, "error": "PDF file not found after conversion"}

    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Conversion timed out"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def ppt_to_images(
    ppt_path: str,
    output_dir: Optional[str] = None,
    dpi: int = 300,
    format: str = "jpg"
) -> dict:
    """
    Convert a PPT file to a sequence of images.

    Args:
        ppt_path: Path to the PPT file
        output_dir: Output directory for images
        dpi: Resolution in DPI (default: 300)
        format: Output format - jpg or png (default: jpg)

    Returns:
        Dictionary with conversion result including list of image paths
    """
    # First convert to PDF
    pdf_result = ppt_to_pdf(ppt_path, output_dir)
    if not pdf_result["success"]:
        return pdf_result

    pdf_path = Path(pdf_result["pdf_path"])

    # Determine output directory
    if output_dir:
        out_dir = Path(output_dir) / "slides"
    else:
        out_dir = pdf_path.parent / "slides"
    out_dir.mkdir(parents=True, exist_ok=True)

    # Convert PDF to images
    pdftoppm = converter._find_pdftoppm()
    if not pdftoppm:
        # Cleanup PDF
        pdf_path.unlink()
        return {
            "success": False,
            "error": "pdftoppm not found. Please install poppler-utils."
        }

    try:
        fmt_flag = "-jpeg" if format.lower() == "jpg" else "-png"
        cmd = [
            pdftoppm,
            fmt_flag,
            "-r", str(dpi),
            str(pdf_path),
            str(out_dir / "slide")
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

        if result.returncode != 0:
            return {
                "success": False,
                "error": f"pdftoppm error: {result.stderr}"
            }

        # Find generated images
        ext = ".jpg" if format.lower() == "jpg" else ".png"
        images = sorted(out_dir.glob(f"slide-*{ext}"))

        if not images:
            return {"success": False, "error": "No images generated"}

        # Cleanup PDF
        pdf_path.unlink()

        return {
            "success": True,
            "images_dir": str(out_dir.absolute()),
            "page_count": len(images),
            "image_paths": [str(img.absolute()) for img in images],
            "format": format,
            "dpi": dpi
        }

    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Conversion timed out"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def ppt_to_video(
    ppt_path: str,
    output_dir: Optional[str] = None,
    slide_duration: int = 5,
    resolution: str = "1080p"
) -> dict:
    """
    Convert a PPT file to a video with each slide shown for a specified duration.

    Args:
        ppt_path: Path to the PPT file
        output_dir: Output directory for the video
        slide_duration: Duration of each slide in seconds (default: 5)
        resolution: Output resolution - 720p, 1080p, or 4k (default: 1080p)

    Returns:
        Dictionary with conversion result including video path and duration
    """
    if not converter.ffmpeg_path:
        return {
            "success": False,
            "error": "ffmpeg not found. Please install ffmpeg."
        }

    # Convert to images first
    images_result = ppt_to_images(ppt_path, output_dir)
    if not images_result["success"]:
        return images_result

    images_dir = Path(images_result["images_dir"])

    # Determine output path
    path = Path(ppt_path)
    if output_dir:
        out_dir = Path(output_dir)
    else:
        out_dir = path.parent
    out_dir.mkdir(parents=True, exist_ok=True)

    output_path = out_dir / f"{path.stem}.mp4"

    # Resolution settings
    res_map = {
        "720p": "1280:720",
        "1080p": "1920:1080",
        "4k": "3840:2160"
    }
    res = res_map.get(resolution.lower(), "1920:1080")

    try:
        # Build ffmpeg command
        cmd = [
            converter.ffmpeg_path,
            "-y",
            "-framerate", f"1/{slide_duration}",
            "-i", f"{images_dir}/slide-%d.jpg",
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-preset", "fast",
            "-crf", "23",
            "-vf", f"scale={res}:force_original_aspect_ratio=decrease,pad={res}:(ow-iw)/2:(oh-ih)/2:black",
            str(output_path)
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

        if result.returncode != 0:
            return {
                "success": False,
                "error": f"ffmpeg error: {result.stderr}"
            }

        if not output_path.exists():
            return {"success": False, "error": "Video file not found after conversion"}

        # Calculate video duration
        page_count = images_result["page_count"]
        duration = page_count * slide_duration

        # Cleanup images
        shutil.rmtree(images_dir)

        return {
            "success": True,
            "video_path": str(output_path.absolute()),
            "duration_seconds": duration,
            "slide_duration": slide_duration,
            "page_count": page_count,
            "resolution": resolution,
            "file_size_bytes": output_path.stat().st_size
        }

    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Video conversion timed out"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def check_tools() -> dict:
    """
    Check if all required conversion tools are available.

    Returns:
        Dictionary with tool availability status
    """
    issues = []

    if not converter.libreoffice_path:
        issues.append("LibreOffice not found. Required for PPT to PDF conversion.")
    if not converter.ffmpeg_path:
        issues.append("ffmpeg not found. Required for video conversion.")
    if not converter._find_pdftoppm():
        issues.append("pdftoppm not found. Required for PDF to image conversion.")

    return {
        "success": len(issues) == 0,
        "libreoffice": converter.libreoffice_path or "not found",
        "ffmpeg": converter.ffmpeg_path or "not found",
        "pdftoppm": converter._find_pdftoppm() or "not found",
        "issues": issues if issues else None,
        "message": "All tools available" if not issues else "; ".join(issues)
    }


def main():
    """Run the MCP server"""
    mcp.run()


if __name__ == "__main__":
    main()
