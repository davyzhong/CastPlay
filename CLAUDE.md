# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

CastPlay is a lightweight digital signage management system supporting Android offline playback. It provides:
- Multi-format media support (images, videos, PPT auto-conversion)
- Real-time WebSocket push for playlist updates
- Web admin panel for device and content management
- Android client with offline caching

## Common Commands

### Development Server

```bash
# Start backend (port 8000)
python scripts/server/start.py
# Or with uvicorn
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Start frontend dev server (port 3000)
cd frontend && npm run dev

# Start both (parallel)
make dev
```

### Database Management

```bash
python scripts/db/init.py      # Initialize database
python scripts/db/backup.py    # Backup database
python scripts/migration/      # Migration scripts (add columns, etc.)
```

### Testing

```bash
pytest tests/                          # All tests
pytest tests/unit/ -v                  # Unit tests only
pytest tests/integration/ -v           # Integration tests
pytest tests/ -m "not slow" --maxfail=5  # Quick tests
pytest tests/ -k "test_name" -v        # Run specific test
```

### Code Quality

```bash
make lint       # Run all linters (black, isort, mypy, pylint)
make format     # Auto-format code (black + isort)
ruff check app/  # Fast linter
```

### Frontend

```bash
cd frontend
npm run dev          # Development server
npm run build        # Production build
npm run lint         # ESLint
npm run test         # Vitest
```

### Android

```bash
./build-android.sh [serverUrl]  # Build APK with server URL
```

### CLI Tool

```bash
castplay devices list              # List all devices
castplay control pause <device_id> # Control playback
castplay status                    # System status
castplay --help                    # All commands
```

## Architecture

### Backend (FastAPI + SQLite)

```
app/
├── main.py              # FastAPI app entry, WebSocket endpoint
├── config.py            # Pydantic Settings configuration
├── database.py          # SQLAlchemy session management
├── scheduler.py         # Background task scheduler
├── bootstrap/           # Application initialization module
├── api/                 # API route handlers
│   ├── auth.py         # Authentication endpoints
│   ├── devices.py      # Device CRUD and management
│   ├── media.py        # Media file upload/conversion
│   ├── playlists.py    # Playlist management
│   ├── player.py       # Player API for devices
│   └── control.py      # Remote control commands
├── models/              # SQLAlchemy ORM models
├── schemas/             # Pydantic request/response schemas
├── services/            # Business logic services
│   ├── converter.py    # PPT to video conversion
│   └── notification.py # WebSocket notification service
├── utils/               # Utility functions
└── websocket/           # WebSocket connection manager
```

Key patterns:
- Bootstrap module handles all startup initialization (DB, directories, routes, scheduler)
- WebSocket endpoint in `main.py` handles device connections with heartbeat
- Services layer separates business logic from API routes
- SQLite database with SQLAlchemy ORM, no external dependencies

### Frontend (React + TypeScript + Vite)

```
frontend/src/
├── App.tsx              # Main app with routing
├── main.tsx             # Entry point
├── player-main.tsx      # Player page entry (multi-page app)
├── pages/               # Page components
│   ├── Dashboard.tsx    # Main dashboard
│   ├── DeviceList.tsx   # Device management
│   ├── MediaList.tsx    # Media library
│   ├── PlaylistList.tsx # Playlist management
│   └── WebPlayerSimulator.tsx  # Web-based player simulator
├── player/              # Player-related components
├── store/               # Zustand state management
└── utils/               # API client and utilities
```

Key patterns:
- Multi-page Vite build (admin index.html + player.html)
- Zustand for state management
- Ant Design for UI components
- Relative paths for Android WebView compatibility

### Android (Kotlin)

```
android/app/src/main/java/com/castplay/player/
├── MainActivity.kt      # Main activity with WebView
├── CacheManager.kt      # Offline media caching
├── JsBridge.kt          # JavaScript bridge for WebView
└── network/             # Network utilities
```

### MCP Servers

Located in `mcp/`:
- `ppt-converter/` - PPT to video/image conversion tools
- `android-tools/` - Android SDK integration (emulator, APK)

## Key Endpoints

| Endpoint | Purpose |
|----------|---------|
| `GET /` | Admin web interface |
| `GET /player.html` | Player interface |
| `WS /ws/{device_id}` | WebSocket for device communication |
| `POST /api/auth/login` | Authentication |
| `/api/devices/*` | Device management |
| `/api/media/*` | Media upload/conversion |
| `/api/playlists/*` | Playlist management |
| `/api/player/{device_id}/*` | Player-specific APIs |

## Configuration

- Environment via `.env` file (see `.env.example`)
- Critical settings: `SECRET_KEY` (production required), `ENVIRONMENT`, `DATABASE_PATH`
- Development mode: auto-generates secret key, allows CORS from any origin

## Code Standards

- Python line length: 100 characters
- Formatting: Black + isort (black profile)
- Linting: ruff, mypy, pylint
- Commit style: Conventional commits (`feat:`, `fix:`, `chore:`, etc.)
- Pre-commit hooks available: `pre-commit install`

## File Storage

```
data/
├── castplay.db          # SQLite database
├── uploads/             # Original uploaded files
├── converted/           # Converted media (PPT→video)
└── thumbnails/          # Generated thumbnails
```

## Player Configuration UI (003-player-config-ui)

### Feature Overview

The player configuration UI provides three key features for first-time setup:

1. **Server Configuration (US1)** - Configure server IP/domain on first startup
2. **Device Registration Code (US2)** - Display registration code for admin setup
3. **Playlist Selection (US3)** - Multi-select playlists for playback

### Player Startup Flow

```
1. Check Server Config → If not configured, show ServerConfigDialog
2. Connect to Server → Auto-register device via useDeviceRegistration
3. Check Registration Code → If has code and no playlists, show RegistrationCodeDisplay
4. Check Playlist Selection → If multiple playlists, show PlaylistSelectionModal
5. Start Playback → Play selected playlists
```

### Key Components

| Component | Purpose |
|-----------|---------|
| `ServerConfigDialog` | Server IP/domain input, connection test, protocol detection |
| `RegistrationCodeDisplay` | Display registration code, copy to clipboard |
| `PlaylistSelectionModal` | Multi-select playlists, select all/deselect all |
| `SettingsButton` | Floating gear icon to reopen server config |

### Key Hooks

| Hook | Purpose |
|------|---------|
| `useServerConfig` | Server configuration management, connection test |
| `useRegistrationCode` | Registration code from build env, registration state |
| `usePlaylistSelection` | Playlist multi-selection with persistence |
| `useDeviceRegistration` | Device auto-registration with server |

### Storage Keys

Configuration is persisted using these keys:

```typescript
// frontend/src/player/types/config.ts
STORAGE_KEYS = {
  SERVER_CONFIG: 'castplay_server_config',
  DEVICE_REGISTRATION: 'castplay_device_registration',
  PLAYLIST_SELECTION: 'castplay_playlist_selection',
}
```

### Environment Variables

- `REGISTRATION_CODE` - Build-time registration code (embedded in APK/web build)
- Example: `REGISTRATION_CODE=ABC123 npm run build`

### Android Integration

The `AndroidBridge` interface provides storage methods:

```typescript
interface AndroidBridge {
  getConfig(key: string): string;
  setConfig(key: string, value: string): void;
  copyToClipboard(text: string): boolean;
  // ... other methods
}
```

### Error Handling

- `ConfigErrorBoundary` - Catches configuration errors, provides retry/clear options
- `LoadingOverlay` - Loading states for configuration operations
- `ConfigLogger` - Unified logging for configuration operations

## Active Technologies
- Python 3.10+, TypeScript 5.x + FastAPI, SQLAlchemy, Pydantic, React, Zustand, Ant Design, APScheduler (001-playlist-scheduling)
- SQLite (via SQLAlchemy ORM) (001-playlist-scheduling)
- TypeScript 5.2+, Python 3.10+ + React 18, FastAPI, Ant Design 5, Zustand, SQLite (003-player-config-ui)
- localStorage (web), SharedPreferences/DataStore via JsBridge (Android) (003-player-config-ui)

## Recent Changes
- 001-playlist-scheduling: Added Python 3.10+, TypeScript 5.x + FastAPI, SQLAlchemy, Pydantic, React, Zustand, Ant Design, APScheduler
