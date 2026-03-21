# Quickstart: Playlist Scheduling

**Feature**: 001-playlist-scheduling
**Date**: 2026-03-16

## Prerequisites

- CastPlay server running (port 8000)
- At least one device registered
- At least two playlists created and assigned to the device

## Quick Setup (5 minutes)

### 1. Create a Schedule via API

```bash
# Create a weekday morning schedule
curl -X POST http://localhost:8000/api/schedules \
  -H "Content-Type: application/json" \
  -H "Cookie: $(curl -s -c - http://localhost:8000/api/auth/login \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=admin&password=admin123" | grep session | awk '{print $NF}')" \
  -d '{
    "device_id": 1,
    "playlist_id": 2,
    "start_time": "09:00:00",
    "end_time": "17:00:00",
    "days_of_week": 31,
    "enabled": true,
    "priority": 0
  }'
```

### 2. Verify Schedule Created

```bash
# List schedules for device
curl http://localhost:8000/api/schedules?device_id=1
```

Expected response:
```json
{
  "schedules": [
    {
      "id": 1,
      "device_id": 1,
      "playlist_id": 2,
      "playlist_name": "Business Hours",
      "start_time": "09:00:00",
      "end_time": "17:00:00",
      "days_of_week": 31,
      "days_display": ["Mon", "Tue", "Wed", "Thu", "Fri"],
      "enabled": true,
      "priority": 0
    }
  ],
  "total": 1
}
```

### 3. Test Schedule Activation

```bash
# Check active schedule for device
curl http://localhost:8000/api/schedules/active?device_id=1
```

### 4. View in Admin UI

1. Open http://localhost:8000/
2. Navigate to Devices page
3. Click on a device
4. See "Schedules" tab showing all configured schedules
5. Click "Add Schedule" to create new schedule via UI

## Day of Week Reference

| Pattern | Value | Days |
|---------|-------|------|
| Weekdays | 31 | Mon-Fri |
| Weekends | 96 | Sat-Sun |
| All Week | 127 | Mon-Sun |
| Monday only | 1 | Mon |
| Monday + Wednesday + Friday | 21 | Mon, Wed, Fri |

## Testing Schedule Switching

### Method 1: Create Near-Future Schedule

```bash
# Get current time and add 2 minutes
CURRENT_TIME=$(date +%H:%M)
# Create schedule starting in 2 minutes
curl -X POST http://localhost:8000/api/schedules \
  -H "Content-Type: application/json" \
  -d "{
    \"device_id\": 1,
    \"playlist_id\": 3,
    \"start_time\": \"$(date -v+2M +%H:%M):00\",
    \"end_time\": \"23:59:59\",
    \"days_of_week\": 127,
    \"enabled\": true
  }"

# Watch the device - it should switch playlists at the scheduled time
```

### Method 2: Use Web Player Simulator

1. Open http://localhost:8000/player.html
2. Open browser console (F12)
3. Create a schedule starting soon
4. Observe schedule evaluation logs in console

## Troubleshooting

### Schedule Not Triggering

1. **Check device is online**: Device must have WebSocket connection
2. **Check current time**: Server uses Asia/Shanghai timezone
3. **Check schedule enabled**: `enabled` must be `true`
4. **Check day match**: Today's day must be in `days_of_week` bitmask

### Conflict Warning Appearing

- Conflicts are warnings, not errors
- If intentional, save anyway
- When multiple schedules match, highest `priority` wins
- If same priority, most recently created wins

### Playlist Not Switching

1. Check current media finishes first (graceful transition)
2. Check schedule is still within active time window
3. Check device received schedule update via WebSocket
