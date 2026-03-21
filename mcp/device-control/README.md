# CastPlay Device Control MCP Server

MCP server providing tools for controlling CastPlay devices.

## Installation

```bash
cd mcp/device-control
pip install -e .
```

## Usage with Claude Desktop

Add to Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "castplay-device-control": {
      "command": "python",
      "args": ["/path/to/CastPlay/mcp/device-control/device_control_server.py"]
    }
  }
}
```

## Available Tools

### Device Query
- `list_devices` - Get all registered devices
- `get_device` - Get device details by ID
- `get_online_devices` - Get all online devices
- `check_device_online` - Check if specific device is online

### Playback Control
- `pause_playback` - Pause playback on device
- `resume_playback` - Resume playback on device
- `set_volume` - Set device volume (0-100)
- `next_media` - Skip to next media
- `prev_media` - Go to previous media
- `switch_playlist` - Switch device to different playlist
- `reload_playlist` - Force device to reload playlist

### Device Management
- `enable_device` - Enable device for playback
- `disable_device` - Disable device from playback
- `get_device_playlists` - Get playlists assigned to device
- `set_device_name` - Update device name

### Configuration
- `configure_api` - Set API URL and authentication token

## Configuration

The server reads configuration from `~/.castplay/config.json`:

```json
{
  "api_url": "http://localhost:8000",
  "token": "your-jwt-token"
}
```

Or set environment variable:
```bash
export CASTPLAY_API_URL=http://localhost:8000
```
