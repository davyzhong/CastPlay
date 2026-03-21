"""
Device Control MCP Server

Provides MCP tools for controlling CastPlay devices remotely.

Uses the shared API client with connection pooling for better performance.
"""
import json
import logging
import sys
from pathlib import Path
from typing import Optional

# Add parent directory to path for shared module
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp.server import FastMCP

# Import shared components
from castplay_shared import get_client, configure_client, handle_api_errors

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

mcp = FastMCP("castplay-device-control")


# ============== Device Query Tools ==============

@mcp.tool()
async def list_devices(
    online_only: bool = False,
    skip: int = 0,
    limit: int = 100
) -> dict:
    """
    Get list of all registered devices.

    Args:
        online_only: If True, only return online devices
        skip: Number of records to skip
        limit: Maximum number of records to return

    Returns:
        Dictionary with device list and metadata
    """
    try:
        client = get_client()
        params = {"skip": skip, "limit": limit}
        result = await client.get("/api/devices/", params=params)
        # Handle paginated response with 'items' key
        devices = result.get("items", result) if isinstance(result, dict) else result

        if online_only:
            devices = [d for d in devices if d.get("is_online", False)]

        return {
            "success": True,
            "devices": devices,
            "count": len(devices),
            "online_only": online_only
        }
    except Exception as e:
        logger.error(f"Failed to list devices: {e}")
        return {"success": False, "error": str(e)}


@mcp.tool()
async def get_device(device_id: int) -> dict:
    """
    Get detailed information about a specific device.

    Args:
        device_id: The device ID

    Returns:
        Dictionary with device details
    """
    try:
        client = get_client()
        device = await client.get(f"/api/devices/{device_id}")
        return {"success": True, "device": device}
    except Exception as e:
        error_msg = str(e)
        if "404" in error_msg:
            return {"success": False, "error": f"Device {device_id} not found"}
        logger.error(f"Failed to get device {device_id}: {e}")
        return {"success": False, "error": error_msg}


@mcp.tool()
async def get_online_devices() -> dict:
    """
    Get list of all currently online devices.

    Returns:
        Dictionary with online device list
    """
    client = get_client()
    try:
        # Use status endpoint for online devices
        result = await client.get("/api/devices/status/online")
        return {
            "success": True,
            "online_devices": result,
            "count": len(result) if isinstance(result, list) else result.get("count", 0)
        }
    except Exception as e:
        logger.warning(f"Online status endpoint failed, falling back: {e}")
        # Fallback to filtering from device list
        try:
            result = await client.get("/api/devices/")
            devices = result.get("items", result) if isinstance(result, dict) else result
            online = [d for d in devices if d.get("is_online", False)]
            return {
                "success": True,
                "online_devices": online,
                "count": len(online)
            }
        except Exception as e2:
            logger.error(f"Fallback also failed: {e2}")
            return {"success": False, "error": str(e2)}


@mcp.tool()
async def check_device_online(device_id: int) -> dict:
    """
    Check if a specific device is online.

    Args:
        device_id: The device ID to check

    Returns:
        Dictionary with online status
    """
    try:
        client = get_client()
        device = await client.get(f"/api/devices/{device_id}")
        return {
            "success": True,
            "device_id": device_id,
            "device_name": device.get("name", "Unknown"),
            "is_online": device.get("is_online", False),
            "last_seen": device.get("last_seen")
        }
    except Exception as e:
        error_msg = str(e)
        if "404" in error_msg:
            return {"success": False, "error": f"Device {device_id} not found"}
        return {"success": False, "error": error_msg}


# ============== Playback Control Tools ==============

@mcp.tool()
async def pause_playback(device_id: int) -> dict:
    """
    Pause playback on a device.

    Args:
        device_id: The device ID to control

    Returns:
        Dictionary with operation result
    """
    try:
        client = get_client()
        result = await client.post(f"/api/control/{device_id}/pause")
        return {
            "success": True,
            "device_id": device_id,
            "action": "pause",
            "message": result.get("message", "Playback paused")
        }
    except Exception as e:
        return {"success": False, "error": f"Failed to pause: {e}"}


@mcp.tool()
async def resume_playback(device_id: int) -> dict:
    """
    Resume playback on a device.

    Args:
        device_id: The device ID to control

    Returns:
        Dictionary with operation result
    """
    try:
        client = get_client()
        result = await client.post(f"/api/control/{device_id}/resume")
        return {
            "success": True,
            "device_id": device_id,
            "action": "resume",
            "message": result.get("message", "Playback resumed")
        }
    except Exception as e:
        return {"success": False, "error": f"Failed to resume: {e}"}


@mcp.tool()
async def set_volume(device_id: int, volume: int) -> dict:
    """
    Set playback volume on a device.

    Args:
        device_id: The device ID to control
        volume: Volume level (0-100)

    Returns:
        Dictionary with operation result
    """
    if not 0 <= volume <= 100:
        return {"success": False, "error": "Volume must be between 0 and 100"}

    try:
        client = get_client()
        result = await client.post(f"/api/control/{device_id}/volume", json_data={"volume": volume})
        return {
            "success": True,
            "device_id": device_id,
            "action": "set_volume",
            "volume": volume,
            "message": result.get("message", f"Volume set to {volume}")
        }
    except Exception as e:
        return {"success": False, "error": f"Failed to set volume: {e}"}


@mcp.tool()
async def next_media(device_id: int) -> dict:
    """
    Skip to next media item on a device.

    Args:
        device_id: The device ID to control

    Returns:
        Dictionary with operation result
    """
    try:
        client = get_client()
        result = await client.post(f"/api/control/{device_id}/next")
        return {
            "success": True,
            "device_id": device_id,
            "action": "next",
            "message": result.get("message", "Skipped to next media")
        }
    except Exception as e:
        return {"success": False, "error": f"Failed to skip: {e}"}


@mcp.tool()
async def prev_media(device_id: int) -> dict:
    """
    Go to previous media item on a device.

    Args:
        device_id: The device ID to control

    Returns:
        Dictionary with operation result
    """
    try:
        client = get_client()
        result = await client.post(f"/api/control/{device_id}/prev")
        return {
            "success": True,
            "device_id": device_id,
            "action": "prev",
            "message": result.get("message", "Went to previous media")
        }
    except Exception as e:
        return {"success": False, "error": f"Failed to go back: {e}"}


@mcp.tool()
async def switch_playlist(device_id: int, playlist_id: int) -> dict:
    """
    Switch a device to a different playlist.

    Args:
        device_id: The device ID to control
        playlist_id: The playlist ID to switch to

    Returns:
        Dictionary with operation result
    """
    try:
        client = get_client()
        result = await client.post(f"/api/control/{device_id}/switch", json_data={"playlist_id": playlist_id})
        return {
            "success": True,
            "device_id": device_id,
            "action": "switch_playlist",
            "playlist_id": playlist_id,
            "message": result.get("message", f"Switched to playlist {playlist_id}")
        }
    except Exception as e:
        return {"success": False, "error": f"Failed to switch playlist: {e}"}


@mcp.tool()
async def reload_playlist(device_id: int) -> dict:
    """
    Force device to reload its playlist.

    Args:
        device_id: The device ID to control

    Returns:
        Dictionary with operation result
    """
    try:
        client = get_client()
        result = await client.post(f"/api/control/{device_id}/reload")
        return {
            "success": True,
            "device_id": device_id,
            "action": "reload",
            "message": result.get("message", "Playlist reloaded")
        }
    except Exception as e:
        return {"success": False, "error": f"Failed to reload: {e}"}


# ============== Device Management Tools ==============

@mcp.tool()
async def enable_device(device_id: int) -> dict:
    """
    Enable a device for playback.

    Args:
        device_id: The device ID to enable

    Returns:
        Dictionary with operation result
    """
    try:
        client = get_client()
        await client.put(f"/api/devices/{device_id}", json_data={"is_enabled": True})
        return {
            "success": True,
            "device_id": device_id,
            "action": "enable",
            "message": f"Device {device_id} enabled"
        }
    except Exception as e:
        return {"success": False, "error": f"Failed to enable device: {e}"}


@mcp.tool()
async def disable_device(device_id: int) -> dict:
    """
    Disable a device from playback.

    Args:
        device_id: The device ID to disable

    Returns:
        Dictionary with operation result
    """
    try:
        client = get_client()
        await client.put(f"/api/devices/{device_id}", json_data={"is_enabled": False})
        return {
            "success": True,
            "device_id": device_id,
            "action": "disable",
            "message": f"Device {device_id} disabled"
        }
    except Exception as e:
        return {"success": False, "error": f"Failed to disable device: {e}"}


@mcp.tool()
async def get_device_playlists(device_id: int) -> dict:
    """
    Get playlists assigned to a device.

    Args:
        device_id: The device ID

    Returns:
        Dictionary with assigned playlists
    """
    try:
        client = get_client()
        playlists = await client.get(f"/api/devices/{device_id}/playlists")
        return {
            "success": True,
            "device_id": device_id,
            "playlists": playlists,
            "count": len(playlists) if isinstance(playlists, list) else 0
        }
    except Exception as e:
        return {"success": False, "error": f"Failed to get playlists: {e}"}


@mcp.tool()
async def set_device_name(device_id: int, name: str) -> dict:
    """
    Update device name.

    Args:
        device_id: The device ID
        name: New name for the device

    Returns:
        Dictionary with operation result
    """
    try:
        client = get_client()
        await client.put(f"/api/devices/{device_id}", json_data={"name": name})
        return {
            "success": True,
            "device_id": device_id,
            "action": "rename",
            "new_name": name,
            "message": f"Device renamed to '{name}'"
        }
    except Exception as e:
        return {"success": False, "error": f"Failed to rename device: {e}"}


@mcp.tool()
def configure_api(base_url: str, token: Optional[str] = None) -> dict:
    """
    Configure API connection settings.

    Uses context-based configuration to avoid global state mutation.
    Configuration is persisted securely - tokens use system keyring.

    Args:
        base_url: Base URL of the CastPlay API server
        token: Optional authentication token (stored securely in keyring)

    Returns:
        Dictionary with configuration result
    """
    try:
        # Configure client in context (no global mutation)
        configure_client(base_url=base_url, token=token)
        logger.info(f"API client configured for {base_url}")

        # Persist configuration to file (non-sensitive data only)
        config_dir = Path.home() / ".castplay"
        config_dir.mkdir(exist_ok=True)
        config_path = config_dir / "config.json"

        config = {}
        if config_path.exists():
            try:
                with open(config_path, encoding="utf-8") as f:
                    config = json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Could not read existing config: {e}")

        config["api_url"] = base_url
        # Remove any legacy plain-text token from config
        config.pop("token", None)

        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)

        # Store token securely in keyring
        secure_storage_used = False
        if token:
            try:
                import keyring
                keyring.set_password("castplay", "api_token", token)
                secure_storage_used = True
                logger.info("Token stored securely in system keyring")
            except Exception as e:
                logger.warning(f"Could not store token in keyring: {e}")

        return {
            "success": True,
            "message": f"API configured: {base_url}",
            "config_path": str(config_path),
            "secure_storage": secure_storage_used,
            "security_note": "Token stored in system keyring" if secure_storage_used else "Install 'keyring' package for secure token storage"
        }
    except Exception as e:
        logger.error(f"Failed to configure API: {e}")
        return {"success": False, "error": str(e)}


def main():
    """Run the MCP server"""
    mcp.run()


if __name__ == "__main__":
    main()
