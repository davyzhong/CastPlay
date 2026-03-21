# File Processor MCP Server

MCP server for media file processing: video info extraction, thumbnails, compression, and preview generation.

## Tools

### `get_video_info(video_path: str) -> dict`

Get video file information (duration, resolution, codec, fps, etc.).

**Parameters:**
- `video_path`: Path to the video file

**Returns:**
```json
{
  "success": true,
  "file_path": "/path/to/video.mp4",
  "file_size": 10485760,
  "file_size_mb": 10.0,
  "duration": 120.5,
  "duration_formatted": "02:00",
  "bit_rate": 696320,
  "format": "mov,mp4,m4a,3gp,3g2,mj2",
  "video": {
    "width": 1920,
    "height": 1080,
    "codec": "h264",
    "fps": 30.0,
    "aspect_ratio": "16:9"
  },
  "audio": {
    "codec": "aac",
    "sample_rate": "48000",
    "channels": 2
  }
}
```

**Error Response:**
```json
{
  "success": false,
  "error": "File not found: /path/to/video.mp4"
}
```

---

### `extract_video_thumbnail(video_path: str, output_path: str = None, time_offset: float = 0.0, width: int = 640) -> dict`

Extract a thumbnail from a video file.

**Parameters:**
- `video_path`: Path to the video file
- `output_path`: Output thumbnail path (optional, auto-generated if not provided)
- `time_offset`: Time offset in seconds (default: 0.0)
- `width`: Thumbnail width in pixels (default: 640)

**Returns:**
```json
{
  "success": true,
  "thumbnail_path": "/path/to/thumb_video.jpg",
  "file_size": 45678
}
```

---

### `compress_video(video_path: str, output_path: str = None, crf: int = 28, preset: str = "medium") -> dict`

Compress a video file using H.264 encoding.

**Parameters:**
- `video_path`: Path to the video file
- `output_path`: Output path for compressed video (optional)
- `crf`: Quality factor (0-51, higher = smaller file, lower quality, default: 28)
- `preset`: Encoding preset (`ultrafast`, `superfast`, `veryfast`, `faster`, `fast`, `medium`, `slow`, `slower`, `veryslow`)

**Returns:**
```json
{
  "success": true,
  "output_path": "/path/to/video_compressed.mp4",
  "original_size": 10485760,
  "compressed_size": 5242880,
  "reduction_percent": 50.0
}
```

---

### `generate_video_preview(video_path: str, output_path: str = None, fps: int = 1, grid_cols: int = 4, max_rows: int = 5) -> dict`

Generate a preview grid from video frames.

**Parameters:**
- `video_path`: Path to the video file
- `output_path`: Output preview image path (optional)
- `fps`: Frames per second to extract (default: 1)
- `grid_cols`: Number of columns in the grid (default: 4)
- `max_rows`: Maximum number of rows (default: 5)

**Returns:**
```json
{
  "success": true,
  "preview_path": "/path/to/preview_video.jpg",
  "file_size": 123456
}
```

---

### `check_ffmpeg_available() -> dict`

Check if ffmpeg and ffprobe are available on the system.

**Returns:**
```json
{
  "success": true,
  "ffmpeg": {
    "available": true,
    "path": "/usr/local/bin/ffmpeg"
  },
  "ffprobe": {
    "available": true,
    "path": "/usr/local/bin/ffprobe"
  }
}
```

## Requirements

- Python 3.10+
- ffmpeg and ffprobe installed on the system
- Install with: `brew install ffmpeg` (macOS) or `apt install ffmpeg` (Ubuntu)

## Installation

```bash
cd mcp/file-processor
pip install -e .
```

## Usage with Claude Desktop

Add to your Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "file-processor": {
      "command": "python",
      "args": ["/path/to/CastPlay/mcp/file-processor/file_processor_server.py"],
      "env": {}
    }
  }
}
```

## Security

This server uses `ffmpeg` and `ffprobe` for video processing. All frame rate parsing is done with explicit string parsing (not `eval()`) to prevent code injection vulnerabilities.
