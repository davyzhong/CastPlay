# Changelog

All notable changes to the CastPlay project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- GitHub Actions CI/CD pipeline for automated testing and security scanning
- Unit test infrastructure for MCP servers (`mcp/tests/`)
- Unit test infrastructure for CLI (`cli/tests/`)
- Secure token storage using system keyring (`cli/secure_storage.py`)
- Shared API client module with connection pooling (`mcp/castplay_shared/`)
- Context-based configuration using Python `contextvars`
- Comprehensive code review backlog (24 issues documented)
- Bilingual (English/Chinese) documentation for MCP README

### Security
- **CRITICAL**: Replace `eval()` with safe frame rate parsing in file-processor (CVE-like fix)
- **CRITICAL**: Migrate token storage from plain-text to system keyring
- Add HTTP warning for non-localhost URLs without HTTPS

### Changed
- Migrate CLI config to Pydantic v2 `ConfigDict` syntax
- Standardize all MCP server versions to 2.0.0
- Replace deprecated `datetime.utcnow()` with `datetime.now(timezone.utc)`
- **Simplify playlist assignment model**: Playlists are now either "assigned" or "not assigned" to devices (no activate/deactivate toggle)

### Fixed
- Replace hardcoded user paths with placeholder paths in MCP README
- Remove unused imports from CLI API client
- Handle paginated API responses with `items` key
- Handle 204 No Content responses properly
- Correct playlist assignment API endpoints
- Add missing `httpx` import in schedule-manager
- Add time format validation (HH:MM:SS) in schedule-manager

### Removed
- Global state mutation in MCP API client (replaced with contextvars)
- **BREAKING**: Playlist activation endpoints (`/api/playlists/{id}/devices/{device_id}/activate`)
- **BREAKING**: WebSocket message types `playlist_activated` and `playlist_deactivated`
- **BREAKING**: `is_active` field usage in `DevicePlaylist` model (field retained for backward compatibility, always `True`)

### Breaking Changes
- **Playlist Assignment Simplification**: The playlist activation feature has been removed. Playlists assigned to devices are now always considered "active". This simplifies the data model and API.
  - Removed: `/api/playlists/{playlist_id}/devices/{device_id}/activate` endpoint
  - Removed: `playlist_activated` and `playlist_deactivated` WebSocket messages
  - Changed: DevicePlaylist.is_active is always `True` for assigned playlists
  - Migration: Existing inactive assignments will be treated as active; no data migration needed

## [2.0.0] - 2026-03-18

### Added
- **MCP Servers**: Model Context Protocol servers for Claude Code integration
  - `device-control`: Device management and playback control
  - `playlist-manager`: Playlist and media management
  - `schedule-manager`: Time-based playlist scheduling
  - `ppt-converter`: PowerPoint to video/image conversion
  - `android-tools`: Android SDK integration (emulator, APK)
  - `file-processor`: Media file processing utilities
- **CLI Commands**: Typer-based command-line interface
  - `castplay devices`: Device management commands
  - `castplay playlists`: Playlist management commands
  - `castplay schedules`: Schedule management commands
  - `castplay media`: Media management commands
  - `castplay control`: Device control commands
  - `castplay status`: System status commands
  - `castplay server`: Server management commands
  - `castplay db`: Database management commands
- **Claude Code Skills**: Workflow automation skills
  - `/device-control`: Interactive device control workflow
  - `/deploy-content`: End-to-end content deployment workflow
  - `/ppt-to-signage`: One-click PPT to digital signage conversion

### Changed
- **BREAKING**: API client refactored to use shared module with connection pooling
- **BREAKING**: Configuration now uses context-based dependency injection
- Improved error handling across all MCP servers

### Fixed
- Handle paginated API responses with `items` key
- Handle 204 No Content responses properly
- Correct playlist assignment API endpoints

## [1.0.0] - 2024-12-01

### Added
- Initial release of CastPlay digital signage system
- FastAPI backend with SQLite database
- React frontend with admin panel
- Android player app with offline caching
- WebSocket real-time communication
- Multi-format media support (images, videos, PPT)
- Device registration and management
- Playlist scheduling system
