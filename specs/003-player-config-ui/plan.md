# Implementation Plan: Player Configuration UI

**Branch**: `003-player-config-ui` | **Date**: 2026-03-16 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/003-player-config-ui/spec.md`

## Summary

Add configuration UI features to web player and Android player: 1) Server configuration dialog on startup for IP/domain input; 2) Device registration code display when not registered; 3) Multi-playlist selection interface. Implementation extends existing player infrastructure with new configuration components and local storage persistence.

## Technical Context

**Language/Version**: TypeScript 5.2+, Python 3.10+
**Primary Dependencies**: React 18, FastAPI, Ant Design 5, Zustand, SQLite
**Storage**: localStorage (web), SharedPreferences/DataStore via JsBridge (Android)
**Testing**: Vitest, pytest
**Target Platform**: Web browser, Android WebView
**Project Type**: Web application with Android WebView integration
**Performance Goals**: Dialog display <500ms, configuration save <100ms
**Constraints**: Must work offline after initial configuration, compatible with Android JsBridge
**Scale/Scope**: <50 devices per deployment

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Test-Driven Development | ✅ PASS | Will write unit tests for config components, integration tests for storage persistence |
| II. Simplicity & Zero-Dependency | ✅ PASS | Uses existing React/Zustand infrastructure, no new external dependencies |
| III. Offline-First Modular Architecture | ✅ PASS | Configuration persisted locally, works offline after initial setup |

## Project Structure

### Documentation (this feature)

```text
specs/003-player-config-ui/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (NOT created yet)
```

### Source Code (repository root)

```text
frontend/src/
├── player/
│   ├── PlayerCore.tsx           # Main player component (modify)
│   ├── components/
│   │   ├── ServerConfigDialog.tsx    # NEW: Server configuration UI
│   │   ├── RegistrationCodeDisplay.tsx # NEW: Registration code display
│   │   └── PlaylistSelectionModal.tsx # MODIFY: Add multi-select
│   ├── hooks/
│   │   ├── useServerConfig.ts        # NEW: Server config state management
│   │   ├── useRegistrationCode.ts    # NEW: Registration code management
│   │   └── usePlaylistSelection.ts   # MODIFY: Add multi-select support
│   └── services/
│       ├── ConfigStorage.ts          # NEW: Local storage abstraction
│       └── AddressValidator.ts       # NEW: Server address validation
├── store/
│   └── index.ts                 # Add config-related store slices
└── utils/
    └── apiClient.ts             # MODIFY: Use dynamic server address

app/
├── api/
│   └── player.py                # MODIFY: Add registration code endpoint
├── config.py                    # MODIFY: Add registration code env var
└── services/
    └── config_service.py        # NEW: Server-side config if needed

tests/
├── unit/
│   └── test_player_config.py    # NEW: Config component unit tests
└── integration/
    └── test_player_config_api.py # NEW: API integration tests
```

**Structure Decision**: Using existing frontend/src/player structure, extending with new components and hooks for configuration. No new top-level directories needed.

## Complexity Tracking

> No violations - all changes fit within existing architecture patterns.
