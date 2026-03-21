# CastPlay CLI

Command-line interface for managing CastPlay digital signage system.

## Installation

```bash
cd cli
pip install -e .
```

Or install from the root project:

```bash
pip install -e ".[cli]"
```

## Commands

### Devices

```bash
# List all devices
castplay devices list

# List only online devices
castplay devices list --online

# Get device details
castplay devices get 1

# Enable/disable device
castplay devices enable 1
castplay devices disable 1

# Get device playlists
castplay devices playlists 1
```

### Playlists

```bash
# List all playlists
castplay playlists list

# Get playlist details
castplay playlists get 1

# Create playlist
castplay playlists create "My Playlist" --description "Description"

# Delete playlist
castplay playlists delete 1

# List playlist items
castplay playlists items 1

# Add media to playlist
castplay playlists add-item 1 --media-id 5 --duration 10
```

### Schedules

```bash
# List schedules for a device
castplay schedules list --device-id 1

# Create schedule (weekdays: 0=Mon, 6=Sun)
castplay schedules create \
    --device-id 1 \
    --playlist-id 2 \
    --start-time 08:00:00 \
    --end-time 18:00:00 \
    --weekdays 0,1,2,3,4

# Update schedule
castplay schedules update 1 --start-time 09:00:00

# Delete schedule
castplay schedules delete 1

# Get active schedule
castplay schedules active --device-id 1
```

### Control

```bash
# Pause playback
castplay control pause 1

# Resume playback
castplay control resume 1

# Set volume (0-100)
castplay control volume 1 50

# Next/previous media
castplay control next 1
castplay control prev 1

# Switch playlist
castplay control switch 1 --playlist-id 2

# Reload playlist
castplay control reload 1
```

### Media

```bash
# List all media
castplay media list

# List by type
castplay media list --type video

# Get media info
castplay media get 1

# Delete media
castplay media delete 1

# Retry PPT conversion
castplay media retry 1
```

### Status

```bash
# System status
castplay status

# Online devices count
castplay status --online
```

### Server

```bash
# Start backend server
castplay server start

# Start with options
castplay server start --host 0.0.0.0 --port 8000 --reload
```

### Configuration

```bash
# Set server URL
castplay config server https://api.example.com

# Login (stores token securely)
castplay config login

# Logout
castplay config logout

# Show current config
castplay config show
```

## Configuration

Configuration is stored in `~/.castplay/config.json`. Authentication tokens are stored securely in the system keyring (Keychain on macOS, Credential Manager on Windows, Secret Service on Linux).

### Environment Variables

- `CASTPLAY_API_URL`: Override API URL
- `CASTPLAY_TOKEN`: Override authentication token

## Output Formats

Most commands support `--json` for JSON output:

```bash
castplay devices list --json
```

## Exit Codes

- `0`: Success
- `1`: Error (API error, not found, validation error)
- `2`: Invalid arguments

## Security

- Tokens are stored in system keyring, not plain text files
- HTTP connections to non-localhost URLs trigger a warning
- Use HTTPS for production deployments
