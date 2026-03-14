# CastPlay PPT Converter MCP Server

MCP server providing PPT conversion tools for CastPlay.

## Features

- **ppt_to_pdf**: Convert PPT/PPTX/ODP to PDF
- **ppt_to_images**: Convert PPT to image sequence (JPG/PNG)
- **ppt_to_video**: Convert PPT to video with configurable slide duration
- **get_ppt_info**: Get information about a PPT file
- **check_tools**: Check if required tools are available

## Requirements

- LibreOffice (for PPT to PDF conversion)
- poppler-utils (pdftoppm for PDF to image conversion)
- ffmpeg (for video generation)

## Installation

```bash
cd mcp/ppt-converter
pip install -e .
```

## Usage

### As MCP Server

Add to your Claude Code configuration:

```json
{
  "mcpServers": {
    "ppt-converter": {
      "command": "python",
      "args": ["/path/to/CastPlay/mcp/ppt-converter/ppt_converter_server.py"]
    }
  }
}
```

### Standalone

```bash
python ppt_converter_server.py
```

## Tools

### ppt_to_pdf

Convert a PPT file to PDF.

```
ppt_to_pdf(ppt_path: str, output_dir: Optional[str] = None) -> dict
```

### ppt_to_images

Convert a PPT file to images.

```
ppt_to_images(
    ppt_path: str,
    output_dir: Optional[str] = None,
    dpi: int = 300,
    format: str = "jpg"
) -> dict
```

### ppt_to_video

Convert a PPT file to video.

```
ppt_to_video(
    ppt_path: str,
    output_dir: Optional[str] = None,
    slide_duration: int = 5,
    resolution: str = "1080p"
) -> dict
```

### get_ppt_info

Get information about a PPT file.

```
get_ppt_info(ppt_path: str) -> dict
```

### check_tools

Check if all required tools are available.

```
check_tools() -> dict
```
