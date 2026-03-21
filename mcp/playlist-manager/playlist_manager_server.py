"""
Playlist Manager MCP Server

Provides MCP tools for managing CastPlay playlists and media.

Uses the shared API client with connection pooling for better performance.
"""
import json
import logging
import sys
from pathlib import Path
from typing import Optional, List

import httpx

# Add parent directory to path for shared module
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp.server import FastMCP

# Import shared components
from castplay_shared import get_client, configure_client

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

mcp = FastMCP("castplay-playlist-manager")


# ============== Playlist CRUD Tools ==============

@mcp.tool()
async def list_playlists(
    skip: int = 0,
    limit: int = 100,
    include_inactive: bool = True
) -> dict:
    """
    Get list of all playlists.

    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        include_inactive: Include inactive playlists

    Returns:
        Dictionary with playlist list
    """
    try:
        params = {"skip": skip, "limit": limit}
        result = await get_client().get("/api/playlists/", params=params)
        playlists = result.get("items", []) if isinstance(result, dict) else result

        if not include_inactive:
            playlists = [p for p in playlists if p.get("is_active", True)]

        return {
            "success": True,
            "playlists": playlists,
            "count": len(playlists)
        }
    except httpx.HTTPStatusError as e:
        return {"success": False, "error": f"API error: {e.response.status_code}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def get_playlist(playlist_id: int) -> dict:
    """
    Get detailed information about a playlist.

    Args:
        playlist_id: The playlist ID

    Returns:
        Dictionary with playlist details including media items
    """
    try:
        playlist = await get_client().get(f"/api/playlists/{playlist_id}")
        return {"success": True, "playlist": playlist}
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return {"success": False, "error": f"Playlist {playlist_id} not found"}
        return {"success": False, "error": f"API error: {e.response.status_code}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def create_playlist(
    name: str,
    description: Optional[str] = None,
    device_ids: Optional[List[int]] = None
) -> dict:
    """
    Create a new playlist.

    Args:
        name: Playlist name
        description: Optional description
        device_ids: Optional list of device IDs to assign to

    Returns:
        Dictionary with created playlist
    """
    try:
        data = {"name": name}
        if description:
            data["description"] = description

        playlist = await get_client().post("/api/playlists", json_data=data)

        # Assign to devices if specified
        if device_ids:
            for device_id in device_ids:
                await get_client().post(f"/api/playlists/{playlist['id']}/assign/{device_id}")

        return {
            "success": True,
            "playlist": playlist,
            "message": f"Playlist '{name}' created with ID {playlist['id']}"
        }
    except httpx.HTTPStatusError as e:
        return {"success": False, "error": f"Failed to create playlist: {e.response.status_code}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def update_playlist(
    playlist_id: int,
    name: Optional[str] = None,
    description: Optional[str] = None
) -> dict:
    """
    Update playlist information.

    Args:
        playlist_id: The playlist ID
        name: New name (optional)
        description: New description (optional)

    Returns:
        Dictionary with updated playlist
    """
    try:
        data = {}
        if name:
            data["name"] = name
        if description is not None:
            data["description"] = description

        playlist = await get_client().put(f"/api/playlists/{playlist_id}", json_data=data)
        return {
            "success": True,
            "playlist": playlist,
            "message": f"Playlist {playlist_id} updated"
        }
    except httpx.HTTPStatusError as e:
        return {"success": False, "error": f"Failed to update playlist: {e.response.status_code}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def delete_playlist(playlist_id: int) -> dict:
    """
    Delete a playlist.

    Args:
        playlist_id: The playlist ID to delete

    Returns:
        Dictionary with deletion result
    """
    try:
        await get_client().delete(f"/api/playlists/{playlist_id}")
        return {
            "success": True,
            "playlist_id": playlist_id,
            "message": f"Playlist {playlist_id} deleted"
        }
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return {"success": False, "error": f"Playlist {playlist_id} not found"}
        return {"success": False, "error": f"Failed to delete playlist: {e.response.status_code}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def activate_playlist(playlist_id: int) -> dict:
    """
    Activate a playlist for playback.

    Args:
        playlist_id: The playlist ID to activate

    Returns:
        Dictionary with activation result
    """
    try:
        playlist = await get_client().put(f"/api/playlists/{playlist_id}", json_data={"is_active": True})
        return {
            "success": True,
            "playlist_id": playlist_id,
            "message": f"Playlist {playlist_id} activated"
        }
    except httpx.HTTPStatusError as e:
        return {"success": False, "error": f"Failed to activate playlist: {e.response.status_code}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def deactivate_playlist(playlist_id: int) -> dict:
    """
    Deactivate a playlist from playback.

    Args:
        playlist_id: The playlist ID to deactivate

    Returns:
        Dictionary with deactivation result
    """
    try:
        playlist = await get_client().put(f"/api/playlists/{playlist_id}", json_data={"is_active": False})
        return {
            "success": True,
            "playlist_id": playlist_id,
            "message": f"Playlist {playlist_id} deactivated"
        }
    except httpx.HTTPStatusError as e:
        return {"success": False, "error": f"Failed to deactivate playlist: {e.response.status_code}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ============== Playlist Items Tools ==============

@mcp.tool()
async def get_playlist_items(playlist_id: int) -> dict:
    """
    Get all media items in a playlist.

    Args:
        playlist_id: The playlist ID

    Returns:
        Dictionary with playlist items
    """
    try:
        playlist = await get_client().get(f"/api/playlists/{playlist_id}")
        items = playlist.get("items", [])
        return {
            "success": True,
            "playlist_id": playlist_id,
            "items": items,
            "count": len(items)
        }
    except httpx.HTTPStatusError as e:
        return {"success": False, "error": f"Failed to get items: {e.response.status_code}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def add_media_to_playlist(
    playlist_id: int,
    media_id: int,
    duration: int = 10
) -> dict:
    """
    Add a media item to a playlist.

    Args:
        playlist_id: The playlist ID
        media_id: The media ID to add
        duration: Duration in seconds (default: 10)

    Returns:
        Dictionary with added item
    """
    try:
        result = await get_client().post(
            f"/api/playlists/{playlist_id}/items",
            json_data={"media_id": media_id, "duration": duration}
        )
        return {
            "success": True,
            "playlist_id": playlist_id,
            "media_id": media_id,
            "duration": duration,
            "message": f"Media {media_id} added to playlist {playlist_id}"
        }
    except httpx.HTTPStatusError as e:
        return {"success": False, "error": f"Failed to add media: {e.response.status_code}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def add_media_batch(
    playlist_id: int,
    media_ids: List[int],
    duration: int = 10
) -> dict:
    """
    Add multiple media items to a playlist.

    Args:
        playlist_id: The playlist ID
        media_ids: List of media IDs to add
        duration: Duration in seconds for all items (default: 10)

    Returns:
        Dictionary with batch add result
    """
    try:
        result = await get_client().post(
            f"/api/playlists/{playlist_id}/items/batch",
            json_data={"media_ids": media_ids, "duration": duration}
        )
        return {
            "success": True,
            "playlist_id": playlist_id,
            "added_count": len(media_ids),
            "media_ids": media_ids,
            "message": f"Added {len(media_ids)} items to playlist {playlist_id}"
        }
    except httpx.HTTPStatusError as e:
        return {"success": False, "error": f"Failed to add media batch: {e.response.status_code}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def remove_media_from_playlist(
    playlist_id: int,
    item_id: int
) -> dict:
    """
    Remove a media item from a playlist.

    Args:
        playlist_id: The playlist ID
        item_id: The playlist item ID (not media ID)

    Returns:
        Dictionary with removal result
    """
    try:
        await get_client().delete(f"/api/playlists/{playlist_id}/items/{item_id}")
        return {
            "success": True,
            "playlist_id": playlist_id,
            "item_id": item_id,
            "message": f"Item {item_id} removed from playlist {playlist_id}"
        }
    except httpx.HTTPStatusError as e:
        return {"success": False, "error": f"Failed to remove item: {e.response.status_code}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def update_item_duration(
    playlist_id: int,
    item_id: int,
    duration: int
) -> dict:
    """
    Update duration of a playlist item.

    Args:
        playlist_id: The playlist ID
        item_id: The playlist item ID
        duration: New duration in seconds

    Returns:
        Dictionary with update result
    """
    try:
        result = await get_client().put(
            f"/api/playlists/{playlist_id}/items/{item_id}",
            json_data={"duration": duration}
        )
        return {
            "success": True,
            "playlist_id": playlist_id,
            "item_id": item_id,
            "duration": duration,
            "message": f"Item {item_id} duration updated to {duration}s"
        }
    except httpx.HTTPStatusError as e:
        return {"success": False, "error": f"Failed to update duration: {e.response.status_code}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def reorder_playlist_items(
    playlist_id: int,
    item_order: List[dict]
) -> dict:
    """
    Reorder items in a playlist.

    Args:
        playlist_id: The playlist ID
        item_order: List of {id, order} objects specifying new order

    Returns:
        Dictionary with reorder result

    Example:
        reorder_playlist_items(1, [{"id": 3, "order": 0}, {"id": 1, "order": 1}])
    """
    try:
        result = await get_client().put(
            f"/api/playlists/{playlist_id}/items/reorder",
            json_data={"items": item_order}
        )
        return {
            "success": True,
            "playlist_id": playlist_id,
            "message": f"Playlist {playlist_id} items reordered"
        }
    except httpx.HTTPStatusError as e:
        return {"success": False, "error": f"Failed to reorder items: {e.response.status_code}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ============== Device Assignment Tools ==============

@mcp.tool()
async def assign_to_device(
    playlist_id: int,
    device_id: int
) -> dict:
    """
    Assign a playlist to a device.

    Args:
        playlist_id: The playlist ID
        device_id: The device ID

    Returns:
        Dictionary with assignment result
    """
    try:
        result = await get_client().post(f"/api/playlists/{playlist_id}/devices/{device_id}")
        return {
            "success": True,
            "playlist_id": playlist_id,
            "device_id": device_id,
            "message": f"Playlist {playlist_id} assigned to device {device_id}"
        }
    except httpx.HTTPStatusError as e:
        return {"success": False, "error": f"Failed to assign playlist: {e.response.status_code}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def unassign_from_device(
    playlist_id: int,
    device_id: int
) -> dict:
    """
    Remove a playlist from a device.

    Args:
        playlist_id: The playlist ID
        device_id: The device ID

    Returns:
        Dictionary with unassignment result
    """
    try:
        await get_client().delete(f"/api/playlists/{playlist_id}/devices/{device_id}")
        return {
            "success": True,
            "playlist_id": playlist_id,
            "device_id": device_id,
            "message": f"Playlist {playlist_id} removed from device {device_id}"
        }
    except httpx.HTTPStatusError as e:
        return {"success": False, "error": f"Failed to unassign playlist: {e.response.status_code}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def get_assigned_devices(playlist_id: int) -> dict:
    """
    Get devices that have this playlist assigned.

    Args:
        playlist_id: The playlist ID

    Returns:
        Dictionary with assigned devices
    """
    try:
        playlist = await get_client().get(f"/api/playlists/{playlist_id}")
        devices = playlist.get("devices", [])
        return {
            "success": True,
            "playlist_id": playlist_id,
            "devices": devices,
            "count": len(devices)
        }
    except httpx.HTTPStatusError as e:
        return {"success": False, "error": f"Failed to get devices: {e.response.status_code}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ============== Media Management Tools ==============

@mcp.tool()
async def list_media(
    media_type: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
) -> dict:
    """
    Get list of all media files.

    Args:
        media_type: Filter by type ('image', 'video', 'ppt')
        skip: Number of records to skip
        limit: Maximum number of records to return

    Returns:
        Dictionary with media list
    """
    try:
        params = {"skip": skip, "limit": limit}
        if media_type:
            params["type"] = media_type

        result = await get_client().get("/api/media/", params=params)
        # Handle paginated response with 'items' key
        media = result.get("items", result) if isinstance(result, dict) else result
        return {
            "success": True,
            "media": media,
            "count": len(media) if isinstance(media, list) else 0
        }
    except httpx.HTTPStatusError as e:
        return {"success": False, "error": f"Failed to list media: {e.response.status_code}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def get_media_info(media_id: int) -> dict:
    """
    Get detailed information about a media file.

    Args:
        media_id: The media ID

    Returns:
        Dictionary with media details
    """
    try:
        media = await get_client().get(f"/api/media/{media_id}")
        return {"success": True, "media": media}
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return {"success": False, "error": f"Media {media_id} not found"}
        return {"success": False, "error": f"Failed to get media: {e.response.status_code}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def delete_media(media_id: int) -> dict:
    """
    Delete a media file.

    Args:
        media_id: The media ID to delete

    Returns:
        Dictionary with deletion result
    """
    try:
        await get_client().delete(f"/api/media/{media_id}")
        return {
            "success": True,
            "media_id": media_id,
            "message": f"Media {media_id} deleted"
        }
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return {"success": False, "error": f"Media {media_id} not found"}
        return {"success": False, "error": f"Failed to delete media: {e.response.status_code}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def retry_conversion(media_id: int) -> dict:
    """
    Retry PPT conversion for a media file.

    Args:
        media_id: The media ID to retry conversion

    Returns:
        Dictionary with retry result
    """
    try:
        result = await get_client().post(f"/api/media/{media_id}/retry")
        return {
            "success": True,
            "media_id": media_id,
            "message": f"Conversion retry started for media {media_id}"
        }
    except httpx.HTTPStatusError as e:
        return {"success": False, "error": f"Failed to retry conversion: {e.response.status_code}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def main():
    """Run the MCP server"""
    mcp.run()


if __name__ == "__main__":
    main()
