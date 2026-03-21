# Research: Playlist Scheduling

**Feature**: 001-playlist-scheduling
**Date**: 2026-03-16

## Research Questions

### Q1: How should schedule evaluation be triggered?

**Decision**: Use APScheduler with a cron-style job running every minute to evaluate active schedules.

**Rationale**:
- APScheduler is already integrated in the project for PPT conversion tasks
- Minute-level granularity meets the 5-second success criteria (devices evaluate locally)
- Server-side evaluation is primarily for pushing notifications to devices
- Simple to implement and maintain

**Alternatives Considered**:
- **Second-by-second polling**: Overkill for digital signage use case, adds unnecessary load
- **Event-driven (time-based triggers)**: More complex, requires additional infrastructure
- **Database triggers**: Not portable, ties logic to SQLite specifics

### Q2: How to represent days of week for schedule patterns?

**Decision**: Use a bitmask integer (0-127) where each bit represents a day (Monday=1, Sunday=64, all week=127).

**Rationale**:
- Compact storage in SQLite (single integer column)
- Fast bitwise operations for matching
- Familiar pattern (similar to Unix cron)
- Easy to serialize to/from frontend (array of day numbers)

**Alternatives Considered**:
- **JSON array of day names**: More readable but slower queries, larger storage
- **Separate table with day rows**: Over-normalized for simple day matching
- **String format like "1,2,3,5"**: Requires string parsing, error-prone

### Q3: How to handle schedule conflict detection?

**Decision**: Service-layer validation that checks for time range overlaps on the same days before save.

**Rationale**:
- Conflicts are warnings, not errors (user can override)
- Simple time range overlap algorithm: `start1 < end2 AND start2 < end1`
- Plus day bitmask overlap check: `(days1 & days2) != 0`
- Returns list of conflicting schedules for user confirmation

**Alternatives Considered**:
- **Database constraint**: Too rigid, conflicts are warnings not hard errors
- **External rules engine**: Overkill for simple overlap detection
- **No detection**: Poor UX, would cause unpredictable behavior

### Q4: How to sync schedules to devices for offline evaluation?

**Decision**: Include schedule data in the device's playlist sync response; push updates via WebSocket when schedules change.

**Rationale**:
- Existing WebSocket infrastructure already handles playlist updates
- Devices already fetch playlist data on connect/reconnect
- Schedule data is small (typically <100 records)
- Player can evaluate schedules locally using same algorithm as server

**Alternatives Considered**:
- **Polling from device**: More network traffic, less real-time
- **Separate schedule sync endpoint**: Adds complexity, schedules are tightly coupled to playlists
- **Full offline database sync**: Overkill, only schedule data needed

### Q5: How to handle timezone for schedule evaluation?

**Decision**: Use the server's configured timezone (Asia/Shanghai from existing scheduler) for all schedule evaluation. Devices receive UTC timestamps and convert locally if needed.

**Rationale**:
- Single timezone simplifies implementation and debugging
- Consistent with existing scheduler configuration
- Digital signage typically serves single geographic location
- Devices can display times in local timezone while evaluating against server time

**Alternatives Considered**:
- **Per-device timezone**: Adds complexity, most deployments are single-location
- **Per-schedule timezone**: Confusing for users, error-prone
- **UTC everywhere**: Harder for users to reason about business hours

## Dependencies Analysis

### Existing Dependencies (No changes needed)

| Dependency | Usage | Compatibility |
|------------|-------|---------------|
| APScheduler | Schedule evaluation job | ✅ Extend existing |
| SQLAlchemy | PlaylistSchedule model | ✅ Add new model |
| FastAPI | REST endpoints | ✅ Add new routes |
| Pydantic | Request/response schemas | ✅ Add new schemas |
| WebSocket | Push schedule updates | ✅ Extend handler |
| React/Zustand | Frontend state management | ✅ Add new store |

### No New Dependencies Required

All functionality can be implemented using existing project dependencies. This aligns with Constitution Principle II (Simplicity & Zero-Dependency).

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Schedule evaluation performance with many devices | Low | Medium | Evaluate per-device in parallel; cache active schedules |
| Clock drift between server and devices | Medium | Low | Devices sync time on WebSocket connect; 5-second tolerance |
| Playlist deleted while schedule active | Medium | Medium | Add cascade delete or soft-delete with warning |
| Daylight saving transition | Low | Low | Use timezone-aware datetime; test transition scenarios |

## Implementation Notes

1. **Schedule Model**: Add `PlaylistSchedule` model with fields: device_id, playlist_id, start_time, end_time, days_of_week (bitmask), enabled, priority, created_at, updated_at

2. **Conflict Detection**: Implement in `ScheduleService.check_conflicts()` - returns list of overlapping schedules

3. **Evaluation Job**: Add `evaluate_schedules()` job to APScheduler running every minute

4. **WebSocket Message**: Add `schedule_update` message type with full schedule list for device

5. **Frontend Evaluation**: `ScheduleEvaluator` class in player uses same algorithm as server for offline evaluation
