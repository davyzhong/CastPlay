"""
File Processor MCP Server

Provides MCP tools for media file processing: thumbnails, video info, etc.
"""
import os
import sys
import subprocess
import json
import re
from pathlib import Path
from typing import Optional, Dict, Any

from mcp.server import FastMCP
from loguru import logger

# Configure logging
logger.remove()
logger.add(sys.stderr, level="INFO")

mcp = FastMCP("castplay-file-processor")


class FileProcessor:
    """Media file processing utilities"""

    def __init__(self):
        self.ffmpeg_path = self._find_ffmpeg()
        self.ffprobe_path = self._find_ffprobe()

    def _find_ffmpeg(self) -> Optional[str]:
        """Find ffmpeg executable"""
        try:
            result = subprocess.run(["which", "ffmpeg"], capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip()
        except (OSError, subprocess.SubprocessError):
            pass
        return None

    def _find_ffprobe(self) -> Optional[str]:
        """Find ffprobe executable"""
        try:
            result = subprocess.run(["which", "ffprobe"], capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip()
        except (OSError, subprocess.SubprocessError):
            pass
        return None

    def run_command(self, cmd: list, timeout: int = 60) -> dict:
        """Run a shell command and return result"""
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return {
                "success": result.returncode == 0,
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Command timed out"}
        except Exception as e:
            return {"success": False, "error": str(e)}


file_processor = FileProcessor()


@mcp.tool()
def get_video_info(video_path: str) -> dict:
    """
    Get video file information (duration, resolution, codec, etc.)

    Args:
        video_path: Path to the video file

    Returns:
        Video information including duration, width, height, codec, fps, etc.
    """
    if not os.path.exists(video_path):
        return {"success": False, "error": f"File not found: {video_path}"}

    if not file_processor.ffprobe_path:
        return {"success": False, "error": "ffprobe not found. Please install ffmpeg."}

    try:
        cmd = [
            file_processor.ffprobe_path,
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            video_path
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

        if result.returncode != 0:
            return {"success": False, "error": f"ffprobe error: {result.stderr}"}

        data = json.loads(result.stdout)

        # Extract video stream info
        video_stream = None
        audio_stream = None
        for stream in data.get("streams", []):
            if stream.get("codec_type") == "video" and video_stream is None:
                video_stream = stream
            elif stream.get("codec_type") == "audio" and audio_stream is None:
                audio_stream = stream

        format_info = data.get("format", {})

        info = {
            "success": True,
            "file_path": video_path,
            "file_size": int(format_info.get("size", 0)),
            "file_size_mb": round(int(format_info.get("size", 0)) / (1024 * 1024), 2),
            "duration": float(format_info.get("duration", 0)),
            "duration_formatted": _format_duration(float(format_info.get("duration", 0))),
            "bit_rate": int(format_info.get("bit_rate", 0)),
            "format": format_info.get("format_name", "unknown"),
        }

        if video_stream:
            info["video"] = {
                "width": video_stream.get("width"),
                "height": video_stream.get("height"),
                "codec": video_stream.get("codec_name"),
                "fps": _parse_frame_rate(video_stream.get("r_frame_rate", "0/1")),
                "aspect_ratio": video_stream.get("display_aspect_ratio"),
            }

        if audio_stream:
            info["audio"] = {
                "codec": audio_stream.get("codec_name"),
                "sample_rate": audio_stream.get("sample_rate"),
                "channels": audio_stream.get("channels"),
            }

        return info

    except json.JSONDecodeError as e:
        return {"success": False, "error": f"Failed to parse ffprobe output: {e}"}
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "ffprobe timed out"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def extract_video_thumbnail(
    video_path: str,
    output_path: Optional[str] = None,
    time_offset: float = 0.0,
    width: int = 640
) -> dict:
    """
    Extract a thumbnail from a video file

    Args:
        video_path: Path to the video file
        output_path: Output thumbnail path (optional, auto-generated if not provided)
        time_offset: Time offset in seconds (default: 0.0)
        width: Thumbnail width in pixels (default: 640)

    Returns:
        Path to the generated thumbnail
    """
    if not os.path.exists(video_path):
        return {"success": False, "error": f"File not found: {video_path}"}

    if not file_processor.ffmpeg_path:
        return {"success": False, "error": "ffmpeg not found. Please install ffmpeg."}

    try:
        # Generate output path if not provided
        if not output_path:
            video_name = Path(video_path).stem
            output_dir = Path(video_path).parent
            output_path = str(output_dir / f"thumb_{video_name}.jpg")

        # Ensure output directory exists
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        cmd = [
            file_processor.ffmpeg_path,
            "-i", video_path,
            "-ss", str(time_offset),
            "-vframes", "1",
            "-vf", f"scale={width}:-1",
            "-y",
            output_path
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

        if result.returncode != 0:
            return {"success": False, "error": f"ffmpeg error: {result.stderr}"}

        if os.path.exists(output_path):
            return {
                "success": True,
                "thumbnail_path": output_path,
                "file_size": os.path.getsize(output_path)
            }
        else:
            return {"success": False, "error": "Thumbnail file not created"}

    except subprocess.TimeoutExpired:
        return {"success": False, "error": "ffmpeg timed out"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def compress_video(
    video_path: str,
    output_path: Optional[str] = None,
    crf: int = 28,
    preset: str = "medium"
) -> dict:
    """
    Compress a video file

    Args:
        video_path: Path to the video file
        output_path: Output path for compressed video (optional)
        crf: Quality factor (0-51, higher = smaller file, lower quality, default: 28)
        preset: Encoding preset (ultrafast, superfast, veryfast, faster, fast, medium, slow, slower, veryslow)

    Returns:
        Path to the compressed video and size reduction info
    """
    if not os.path.exists(video_path):
        return {"success": False, "error": f"File not found: {video_path}"}

    if not file_processor.ffmpeg_path:
        return {"success": False, "error": "ffmpeg not found. Please install ffmpeg."}

    try:
        # Generate output path if not provided
        if not output_path:
            video_name = Path(video_path).stem
            output_dir = Path(video_path).parent
            output_path = str(output_dir / f"{video_name}_compressed.mp4")

        original_size = os.path.getsize(video_path)

        cmd = [
            file_processor.ffmpeg_path,
            "-i", video_path,
            "-c:v", "libx264",
            "-crf", str(crf),
            "-preset", preset,
            "-c:a", "aac",
            "-b:a", "128k",
            "-y",
            output_path
        ]

        logger.info(f"Compressing video: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

        if result.returncode != 0:
            return {"success": False, "error": f"ffmpeg error: {result.stderr}"}

        if os.path.exists(output_path):
            compressed_size = os.path.getsize(output_path)
            reduction = (1 - compressed_size / original_size) * 100

            return {
                "success": True,
                "output_path": output_path,
                "original_size": original_size,
                "compressed_size": compressed_size,
                "reduction_percent": round(reduction, 2)
            }
        else:
            return {"success": False, "error": "Compressed file not created"}

    except subprocess.TimeoutExpired:
        return {"success": False, "error": "ffmpeg timed out (video may be too long)"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def generate_video_preview(
    video_path: str,
    output_path: Optional[str] = None,
    fps: int = 1,
    grid_cols: int = 4,
    max_rows: int = 5
) -> dict:
    """
    Generate a preview grid from video frames

    Args:
        video_path: Path to the video file
        output_path: Output preview image path (optional)
        fps: Frames per second to extract (default: 1)
        grid_cols: Number of columns in the grid (default: 4)
        max_rows: Maximum number of rows (default: 5)

    Returns:
        Path to the generated preview image
    """
    if not os.path.exists(video_path):
        return {"success": False, "error": f"File not found: {video_path}"}

    if not file_processor.ffmpeg_path:
        return {"success": False, "error": "ffmpeg not found. Please install ffmpeg."}

    try:
        # Generate output path if not provided
        if not output_path:
            video_name = Path(video_path).stem
            output_dir = Path(video_path).parent
            output_path = str(output_dir / f"preview_{video_name}.jpg")

        # Get video info first to calculate intervals
        info = get_video_info(video_path)
        if not info.get("success"):
            return {"success": False, "error": "Failed to get video info"}

        duration = info.get("duration", 0)
        if duration <= 0:
            return {"success": False, "error": "Invalid video duration"}

        # Calculate total frames and tile settings
        total_frames = grid_cols * max_rows
        interval = duration / (total_frames + 1)

        # Use ffmpeg tile filter
        cmd = [
            file_processor.ffmpeg_path,
            "-i", video_path,
            "-vf", f"select='not(mod(n\\,{int(interval*30)}))',scale=320:-1,tile={grid_cols}x{max_rows}",
            "-frames:v", "1",
            "-y",
            output_path
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

        if result.returncode != 0:
            # Fallback: simpler approach
            cmd = [
                file_processor.ffmpeg_path,
                "-i", video_path,
                "-vf", f"fps=1/{interval},scale=320:-1,tile={grid_cols}x{max_rows}",
                "-frames:v", "1",
                "-y",
                output_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

            if result.returncode != 0:
                return {"success": False, "error": f"ffmpeg error: {result.stderr}"}

        if os.path.exists(output_path):
            return {
                "success": True,
                "preview_path": output_path,
                "file_size": os.path.getsize(output_path)
            }
        else:
            return {"success": False, "error": "Preview file not created"}

    except subprocess.TimeoutExpired:
        return {"success": False, "error": "ffmpeg timed out"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def check_ffmpeg_available() -> dict:
    """
    Check if ffmpeg and ffprobe are available

    Returns:
        Status of ffmpeg and ffprobe availability
    """
    return {
        "success": True,
        "ffmpeg": {
            "available": file_processor.ffmpeg_path is not None,
            "path": file_processor.ffmpeg_path
        },
        "ffprobe": {
            "available": file_processor.ffprobe_path is not None,
            "path": file_processor.ffprobe_path
        }
    }


def _format_duration(seconds: float) -> str:
    """Format duration in HH:MM:SS format"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)

    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes:02d}:{secs:02d}"


def _parse_frame_rate(rate_str: str) -> float:
    """
    Safely parse frame rate string from ffprobe output.

    Frame rates come in formats like "30/1", "30000/1001", "60/1".
    This function parses them without using eval() for security.

    Args:
        rate_str: Frame rate string (e.g., "30/1", "29.97", "30000/1001")

    Returns:
        Frame rate as float, or 0.0 if parsing fails
    """
    if not rate_str:
        return 0.0

    try:
        if "/" in rate_str:
            parts = rate_str.split("/")
            if len(parts) == 2:
                num = float(parts[0])
                den = float(parts[1])
                return num / den if den != 0 else 0.0
        return float(rate_str)
    except (ValueError, ZeroDivisionError):
        return 0.0


if __name__ == "__main__":
    mcp.run()
