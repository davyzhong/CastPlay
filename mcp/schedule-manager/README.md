# CastPlay Schedule Manager MCP Server

MCP server providing tools for managing CastPlay schedules (time-based playlist scheduling).

## Installation

```bash
cd mcp/schedule-manager
pip install -e .
```

## Available Tools

### Schedule CRUD
- `list_schedules` - Get all schedules for a device
- `get_schedule` - Get schedule details
- `create_schedule` - Create a new schedule
- `update_schedule` - Update schedule settings
- `delete_schedule` - Delete a schedule
- `enable_schedule` - Enable a schedule
- `disable_schedule` - Disable a schedule

### Active Schedule
- `get_active_schedule` - Get the currently active schedule for a device

### Helper Tools
- `weekdays_to_bitmask` - Convert weekday list to bitmask
- `bitmask_to_weekdays` - Convert bitmask to weekday list
- `configure_api` - Configure API connection settings

## Schedule Parameters

When creating or updating schedules:

- `device_id`: Target device ID
- `playlist_id`: Playlist to activate during schedule
- `start_time`: Start time in HH:MM:SS format (e.g., "08:00:00")
- `end_time`: End time in HH:MM:SS format (e.g., "18:00:00")
- `weekdays`: List of weekday numbers (0=Monday, 6=Sunday)
- `enabled`: Whether schedule is active
- `priority`: Priority for conflict resolution

## Weekday Reference

| Day | Number |
|-----|--------|
| Monday | 0 |
| Tuesday | 1 |
| Wednesday | 2 |
| Thursday | 3 |
| Friday | 4 |
| Saturday | 5 |
| Sunday | 6 |

## Example Usage

```python
# Create a work hours schedule (Mon-Fri, 9AM-6PM)
create_schedule(
    device_id=1,
    playlist_id=2,
    start_time="09:00:00",
    end_time="18:00:00",
    weekdays=[0, 1, 2, 3, 4]  # Mon-Fri
)

# Create a weekend schedule
create_schedule(
    device_id=1,
    playlist_id=3,
    start_time="10:00:00",
    end_time="22:00:00",
    weekdays=[5, 6]  # Sat-Sun
)

# Get active schedule
get_active_schedule(device_id=1)
```

## Configuration

Set the API URL and token via environment variables:
```bash
export CASTPLAY_API_URL="http://localhost:8000"
```

Or use the `configure_api` tool:
```python
configure_api(base_url="http://your-server:8000", token="your-jwt-token")
```

The server automatically loads the token from `~/.castplay/config.json` if available.
