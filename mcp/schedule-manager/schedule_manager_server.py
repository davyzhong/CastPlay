"""
Schedule Manager MCP Server

Provides MCP tools for managing CastPlay schedules (playlist time-based scheduling).

Uses the shared API client with connection pooling for better performance.
"""
import httpx
import json
import logging
import re
import sys
from pathlib import Path
from typing import Optional, List

# Add parent directory to path for shared module
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp.server import FastMCP

# Import shared components
from castplay_shared import get_client, configure_client

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

mcp = FastMCP("castplay-schedule-manager")


# ============== Validation Helpers ==============

def validate_time_format(time_str: str) -> tuple[bool, str]:
    """
    Validate time string format (HH:MM:SS).

    Args:
        time_str: Time string to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not time_str:
        return False, "Time string cannot be empty"

    # Match HH:MM:SS format
    pattern = r'^([0-1]?[0-9]|2[0-3]):([0-5][0-9]):([0-5][0-9])$'
    if not re.match(pattern, time_str):
        return False, f"Invalid time format '{time_str}'. Expected HH:MM:SS (e.g., '08:00:00', '18:30:00')"

    return True, ""


def validate_weekdays(weekdays: Optional[List[int]]) -> tuple[bool, str]:
    """
    Validate weekdays list.

    Args:
        weekdays: List of weekday numbers (0=Monday, 6=Sunday)

    Returns:
        Tuple of (is_valid, error_message)
    """
    if weekdays is None:
        return True, ""  # None means all days, which is valid

    if not isinstance(weekdays, list):
        return False, "weekdays must be a list"

    for day in weekdays:
        if not isinstance(day, int) or day < 0 or day > 6:
            return False, f"Invalid weekday {day}. Must be integer 0-6 (0=Monday, 6=Sunday)"

    return True, ""


# ============== Schedule CRUD Tools ==============

@mcp.tool()
async def list_schedules(
    device_id: int
) -> dict:
    """
    Get all schedules for a specific device.

    Args:
        device_id: The device ID to get schedules for

    Returns:
        List of schedules with their configurations
    """
    try:
        result = await get_client().get("/api/schedules/", params={"device_id": device_id})
        schedules = result.get("schedules", [])
        return {
            "success": True,
            "schedules": schedules,
            "total": len(schedules)
        }
    except httpx.HTTPStatusError as e:
        return {"success": False, "error": f"API error: {e.response.status_code}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def get_schedule(
    schedule_id: int
) -> dict:
    """
    Get detailed information about a specific schedule.

    Args:
        schedule_id: The schedule ID

    Returns:
        Schedule details including device, playlist, time range, and weekdays
    """
    try:
        schedule = await get_client().get(f"/api/schedules/{schedule_id}")
        return {
            "success": True,
            "schedule": schedule
        }
    except httpx.HTTPStatusError as e:
        return {"success": False, "error": f"Schedule not found: {e.response.status_code}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def create_schedule(
    device_id: int,
    playlist_id: int,
    start_time: str,
    end_time: str,
    weekdays: Optional[List[int]] = None,
    enabled: bool = True,
    priority: int = 0
) -> dict:
    """
    Create a new schedule for a device.

    Args:
        device_id: Target device ID
        playlist_id: Playlist to activate during this schedule
        start_time: Start time in HH:MM:SS format (e.g., "08:00:00")
        end_time: End time in HH:MM:SS format (e.g., "18:00:00")
        weekdays: List of weekdays (0=Monday, 6=Sunday). None means every day.
        enabled: Whether the schedule is enabled (default: True)
        priority: Schedule priority for conflict resolution (default: 0)

    Returns:
        Created schedule details
    """
    # Validate time formats
    valid, error = validate_time_format(start_time)
    if not valid:
        return {"success": False, "error": f"Invalid start_time: {error}"}

    valid, error = validate_time_format(end_time)
    if not valid:
        return {"success": False, "error": f"Invalid end_time: {error}"}

    # Validate weekdays
    valid, error = validate_weekdays(weekdays)
    if not valid:
        return {"success": False, "error": error}

    try:
        # Convert weekdays list to bitmask
        days_of_week = 127  # Default: all days
        if weekdays is not None:
            bitmask = 0
            for day in weekdays:
                bitmask |= (1 << day)
            days_of_week = bitmask

        data = {
            "device_id": device_id,
            "playlist_id": playlist_id,
            "start_time": start_time,
            "end_time": end_time,
            "days_of_week": days_of_week,
            "enabled": enabled,
            "priority": priority
        }

        result = await get_client().post("/api/schedules/", json_data=data)
        return {
            "success": True,
            "schedule": result,
            "message": f"Schedule created for device {device_id}"
        }
    except httpx.HTTPStatusError as e:
        error_detail = ""
        try:
            error_detail = e.response.json().get("detail", str(e.response.text))
        except Exception:
            error_detail = str(e.response.text)
        return {"success": False, "error": f"Failed to create schedule: {error_detail}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def update_schedule(
    schedule_id: int,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    weekdays: Optional[List[int]] = None,
    playlist_id: Optional[int] = None,
    enabled: Optional[bool] = None,
    priority: Optional[int] = None
) -> dict:
    """
    Update an existing schedule.

    Args:
        schedule_id: The schedule ID to update
        start_time: New start time (HH:MM:SS)
        end_time: New end time (HH:MM:SS)
        weekdays: New weekdays list (0-6)
        playlist_id: New playlist ID
        enabled: Enable/disable the schedule
        priority: New priority value

    Returns:
        Updated schedule details
    """
    # Validate time formats if provided
    if start_time is not None:
        valid, error = validate_time_format(start_time)
        if not valid:
            return {"success": False, "error": f"Invalid start_time: {error}"}

    if end_time is not None:
        valid, error = validate_time_format(end_time)
        if not valid:
            return {"success": False, "error": f"Invalid end_time: {error}"}

    # Validate weekdays if provided
    if weekdays is not None:
        valid, error = validate_weekdays(weekdays)
        if not valid:
            return {"success": False, "error": error}

    try:
        data = {}
        if start_time is not None:
            data["start_time"] = start_time
        if end_time is not None:
            data["end_time"] = end_time
        if weekdays is not None:
            bitmask = 0
            for day in weekdays:
                bitmask |= (1 << day)
            data["days_of_week"] = bitmask
        if playlist_id is not None:
            data["playlist_id"] = playlist_id
        if enabled is not None:
            data["enabled"] = enabled
        if priority is not None:
            data["priority"] = priority

        if not data:
            return {"success": False, "error": "No fields to update"}

        result = await get_client().put(f"/api/schedules/{schedule_id}", json_data=data)
        return {
            "success": True,
            "schedule": result,
            "message": f"Schedule {schedule_id} updated"
        }
    except httpx.HTTPStatusError as e:
        return {"success": False, "error": f"Failed to update schedule: {e.response.status_code}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def delete_schedule(
    schedule_id: int
) -> dict:
    """
    Delete a schedule.

    Args:
        schedule_id: The schedule ID to delete

    Returns:
        Success confirmation
    """
    try:
        await get_client().delete(f"/api/schedules/{schedule_id}")
        return {
            "success": True,
            "message": f"Schedule {schedule_id} deleted"
        }
    except httpx.HTTPStatusError as e:
        return {"success": False, "error": f"Failed to delete schedule: {e.response.status_code}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def get_active_schedule(
    device_id: int
) -> dict:
    """
    Get the currently active schedule for a device.

    This checks the current time and weekday to determine which schedule
    should be active for the device.

    Args:
        device_id: The device ID to check

    Returns:
        Active schedule details, or indication that no schedule is active
    """
    try:
        result = await get_client().get("/api/schedules/active", params={"device_id": device_id})
        if result:
            return {
                "success": True,
                "active_schedule": result,
                "device_id": device_id
            }
        else:
            return {
                "success": True,
                "active_schedule": None,
                "message": f"No active schedule for device {device_id} at this time"
            }
    except httpx.HTTPStatusError as e:
        return {"success": False, "error": f"Failed to get active schedule: {e.response.status_code}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def enable_schedule(
    schedule_id: int
) -> dict:
    """
    Enable a schedule.

    Args:
        schedule_id: The schedule ID to enable

    Returns:
        Updated schedule status
    """
    return await update_schedule(schedule_id, enabled=True)


@mcp.tool()
async def disable_schedule(
    schedule_id: int
) -> dict:
    """
    Disable a schedule.

    Args:
        schedule_id: The schedule ID to disable

    Returns:
        Updated schedule status
    """
    return await update_schedule(schedule_id, enabled=False)


# ============== Helper Tools ==============

@mcp.tool()
def weekdays_to_bitmask(
    weekdays: List[int]
) -> dict:
    """
    Convert a list of weekday numbers to a bitmask.

    Args:
        weekdays: List of weekday numbers (0=Monday, 6=Sunday)

    Returns:
        The bitmask value and explanation

    Example:
        weekdays_to_bitmask([0, 1, 2, 3, 4])  # Monday-Friday -> 31
        weekdays_to_bitmask([5, 6])           # Weekend -> 96
    """
    bitmask = 0
    for day in weekdays:
        if 0 <= day <= 6:
            bitmask |= (1 << day)

    weekday_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    selected_days = [weekday_names[d] for d in weekdays if 0 <= d <= 6]

    return {
        "success": True,
        "bitmask": bitmask,
        "weekdays": weekdays,
        "selected_days": selected_days
    }


@mcp.tool()
def bitmask_to_weekdays(
    bitmask: int
) -> dict:
    """
    Convert a bitmask to a list of weekday numbers.

    Args:
        bitmask: The bitmask value (1-127)

    Returns:
        List of weekday numbers and names

    Example:
        bitmask_to_weekdays(31)   # -> [0, 1, 2, 3, 4] (Mon-Fri)
        bitmask_to_weekdays(127)  # -> [0, 1, 2, 3, 4, 5, 6] (Every day)
    """
    weekdays = []
    for i in range(7):
        if bitmask & (1 << i):
            weekdays.append(i)

    weekday_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    selected_days = [weekday_names[d] for d in weekdays]

    return {
        "success": True,
        "bitmask": bitmask,
        "weekdays": weekdays,
        "selected_days": selected_days
    }


@mcp.tool()
def configure_api(base_url: str, token: Optional[str] = None) -> dict:
    """
    Configure API connection settings.

    Uses context-based configuration to avoid global state mutation.

    Args:
        base_url: Base URL of the CastPlay API server
        token: Optional authentication token

    Returns:
        Dictionary with configuration result
    """
    try:
        configure_client(base_url=base_url, token=token)
        return {
            "success": True,
            "base_url": base_url,
            "message": f"API configured to use {base_url}"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def main():
    """Run the MCP server"""
    mcp.run()


if __name__ == "__main__":
    main()
