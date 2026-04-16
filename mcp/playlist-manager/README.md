# CastPlay Playlist Manager MCP Server

MCP server providing tools for managing CastPlay playlists and media.

## Installation

```bash
cd mcp/playlist-manager
pip install -e .
```

## Available Tools

### Playlist CRUD
- `list_playlists` - Get all playlists
- `get_playlist` - Get playlist details
- `create_playlist` - Create new playlist
- `update_playlist` - Update playlist info
- `delete_playlist` - Delete playlist

### Playlist Items
- `get_playlist_items` - Get items in playlist
- `add_media_to_playlist` - Add single media item
- `add_media_batch` - Add multiple media items
- `remove_media_from_playlist` - Remove item
- `update_item_duration` - Change item duration
- `reorder_playlist_items` - Reorder items

### Device Assignment
- `assign_to_device` - Assign playlist to device (always active)
- `unassign_from_device` - Remove from device
- `get_assigned_devices` - Get devices with this playlist

### Media Management
- `list_media` - List all media
- `get_media_info` - Get media details
- `delete_media` - Delete media file
- `retry_conversion` - Retry PPT conversion
