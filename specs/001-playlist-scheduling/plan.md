# Implementation Plan: Playlist Scheduling

**Branch**: `001-playlist-scheduling` | **Date**: 2026-03-16 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-playlist-scheduling/spec.md`

## Summary

Implement a scheduling feature that allows devices to automatically switch playlists based on time of day and day of week. The system will persist schedule rules in SQLite, evaluate them via an extended APScheduler, push schedule data to devices via WebSocket for offline evaluation, and provide a management UI in the React admin panel.

## Technical Context

**Language/Version**: Python 3.10+, TypeScript 5.x
**Primary Dependencies**: FastAPI, SQLAlchemy, Pydantic, React, Zustand, Ant Design, APScheduler
**Storage**: SQLite (via SQLAlchemy ORM)
**Testing**: pytest (backend), Vitest (frontend)
**Target Platform**: Linux server (backend), Modern browsers + Android WebView (frontend)
**Project Type**: Web application with mobile client
**Performance Goals**: Playlist switch within 5 seconds of scheduled time
**Constraints**: Offline-capable schedule evaluation on device side, no external dependencies
**Scale/Scope**: <50 devices, <100 schedules per device (user-managed)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence |
|-----------|--------|----------|
| I. Test-Driven Development | ✅ PASS | Plan includes test-first approach; contract tests defined |
| II. Simplicity & Zero-Dependency | ✅ PASS | Uses existing SQLite, APScheduler, WebSocket - no new external deps |
| III. Offline-First Modular Architecture | ✅ PASS | Schedule data synced to device for offline evaluation; WebSocket push for updates |

**Constitution Check**: ✅ ALL GATES PASSED

## Project Structure

### Documentation (this feature)

```text
specs/001-playlist-scheduling/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (API contracts)
│   └── schedule-api.yaml
└── tasks.md             # Phase 2 output (via /speckit.tasks)
```

### Source Code (repository root)

```text
app/
├── models/
│   └── schedule.py           # NEW: PlaylistSchedule model
├── schemas/
│   └── schedule.py           # NEW: Pydantic schemas for schedule CRUD
├── api/
│   └── schedules.py          # NEW: REST API endpoints for schedule management
├── services/
│   └── schedule_service.py   # NEW: Schedule evaluation and conflict detection
├── scheduler.py              # EXTEND: Add schedule evaluation job
└── websocket/
    └── handler.py            # EXTEND: Push schedule updates to devices

frontend/src/
├── pages/
│   └── SchedulePage.tsx      # NEW: Schedule management UI
├── components/
│   └── ScheduleForm.tsx      # NEW: Schedule create/edit form
├── store/
│   └── scheduleStore.ts      # NEW: Zustand store for schedule state
└── services/
    └── scheduleApi.ts        # NEW: API client for schedule endpoints

frontend/src/player/
├── services/
│   └── ScheduleEvaluator.ts  # NEW: Client-side schedule evaluation for offline
└── hooks/
    └── useSchedule.ts        # NEW: Hook for schedule data and switching

tests/
├── unit/
│   └── test_schedule_service.py    # NEW: Unit tests for schedule logic
├── integration/
│   └── test_schedule_api.py        # NEW: Integration tests for schedule endpoints
└── contract/
    └── test_schedule_contract.py   # NEW: Contract tests for schedule API
```

**Structure Decision**: Extends existing web application structure with new modules following established patterns (models in `app/models/`, schemas in `app/schemas/`, API routes in `app/api/`, services in `app/services/`).

## Complexity Tracking

> No violations - design follows existing patterns and constitution principles.

| Aspect | Approach | Justification |
|--------|----------|---------------|
| Schedule evaluation | Extend existing APScheduler | Reuses infrastructure, no new dependencies |
| Offline support | Sync schedules to device, evaluate locally | Follows offline-first principle |
| Conflict detection | Service layer validation | Simple, no external rules engine |
