# Tasks: Playlist Scheduling

**Input**: Design documents from `/specs/001-playlist-scheduling/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), data-model.md, contracts/schedule-api.yaml

**Tests**: Included per constitution (TDD mandatory)

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Backend**: `app/` at repository root
- **Frontend**: `frontend/src/`
- **Player**: `frontend/src/player/`
- **Tests**: `tests/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and database migration

- [X] T001 Create database migration for playlist_schedules table in `scripts/migration/`
- [X] T002 [P] Add PlaylistSchedule model to model exports in `app/models/__init__.py`

**Checkpoint**: Database schema ready for schedule data

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T003 [P] Create PlaylistSchedule SQLAlchemy model in `app/models/schedule.py`
- [X] T004 [P] Create Pydantic schemas (ScheduleCreate, ScheduleUpdate, ScheduleResponse) in `app/schemas/schedule.py`
- [X] T005 Create ScheduleService with conflict detection in `app/services/schedule_service.py`
- [X] T006 Register schedule API router in `app/bootstrap/application.py`

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 & 2 - Schedule CRUD + Auto Switching (Priority: P1) 🎯 MVP

**Goal**: Create, read, update, delete schedule rules AND automatically switch playlists at scheduled times

**Independent Test**: Create a schedule via API, verify it saves; wait for scheduled time, verify device switches playlist

### Tests for User Story 1 & 2 (TDD - Write FIRST, ensure FAIL)

- [X] T007 [P] [US1] Unit test for time range validation (start < end) in `tests/unit/test_schedule_service.py`
- [X] T008 [P] [US1] Unit test for days_of_week bitmask validation in `tests/unit/test_schedule_service.py`
- [X] T009 [P] [US1] Integration test for schedule CRUD endpoints in `tests/integration/test_schedule_api.py`
- [X] T010 [P] [US2] Unit test for schedule evaluation logic in `tests/unit/test_schedule_service.py`

### Backend Implementation for US1 & US2

- [X] T011 [US1] Implement POST /api/schedules endpoint in `app/api/schedules.py`
- [X] T012 [US1] Implement GET /api/schedules?device_id=X endpoint in `app/api/schedules.py`
- [X] T013 [US1] Implement PUT /api/schedules/{id} endpoint in `app/api/schedules.py`
- [X] T014 [US1] Implement DELETE /api/schedules/{id} endpoint in `app/api/schedules.py`
- [X] T015 [US2] Implement GET /api/schedules/active?device_id=X endpoint in `app/api/schedules.py`
- [X] T016 [US2] Implement GET /api/player/{device_id}/schedules endpoint in `app/api/player.py`
- [X] T017 [US2] Add schedule evaluation job to APScheduler in `app/scheduler.py`
- [X] T018 [US2] Add schedule_update WebSocket message type in `app/websocket/handler.py`

### Frontend Implementation for US1 & US2

- [X] T019 [P] [US1] Create scheduleApi service in `frontend/src/api/schedule.ts`
- [X] T020 [P] [US1] Create scheduleStore (Zustand) in `frontend/src/store/index.ts`
- [X] T021 [US1] Create ScheduleForm component in `frontend/src/pages/SchedulePage.tsx`
- [X] T022 [US1] Create SchedulePage with schedule list view in `frontend/src/pages/SchedulePage.tsx`
- [X] T023 [US1] Add SchedulePage route to App.tsx in `frontend/src/App.tsx`
- [X] T024 [P] [US2] Create ScheduleEvaluator service in `frontend/src/player/services/ScheduleEvaluator.ts`
- [X] T025 [US2] Create useSchedule hook in `frontend/src/player/hooks/useSchedule.ts`
- [X] T026 [US2] Integrate schedule switching with PlayerCore in `frontend/src/player/PlayerCore.tsx`

**Checkpoint**: MVP complete - schedules can be created and playlists switch automatically

---

## Phase 4: User Story 3 - Weekly Schedule Patterns (Priority: P2)

**Goal**: Configure schedules that repeat on specific days of the week

**Independent Test**: Create a schedule for Monday-Friday, verify it only triggers on those days

### Tests for User Story 3 (TDD - Write FIRST, ensure FAIL)

- [X] T027 [P] [US3] Unit test for day bitmask matching in `tests/unit/test_schedule_service.py`

### Implementation for US3

- [X] T028 [US3] Add days_of_week bitmask helper functions in `app/services/schedule_service.py`
- [X] T029 [US3] Add days display formatting (["Mon", "Tue"...]) in `app/schemas/schedule.py`
- [X] T030 [US3] Add day-of-week selector UI to ScheduleForm in `frontend/src/components/ScheduleForm.tsx`
- [X] T031 [US3] Update ScheduleEvaluator to check days_of_week in `frontend/src/player/services/ScheduleEvaluator.ts`

**Checkpoint**: Weekly patterns working - schedules can target specific days

---

## Phase 5: User Story 4 - Schedule Management (Priority: P2)

**Goal**: View, edit, and delete schedule rules with proper UX

**Independent Test**: View all schedules for a device sorted by time; edit a schedule; delete a schedule

### Implementation for US4

- [X] T032 [US4] Add schedule list sorted by start_time in SchedulePage in `frontend/src/pages/SchedulePage.tsx`
- [X] T033 [US4] Add edit mode to ScheduleForm in `frontend/src/components/ScheduleForm.tsx`
- [X] T034 [US4] Add delete confirmation modal in `frontend/src/components/ScheduleForm.tsx`
- [X] T035 [US4] Add schedule status indicator (enabled/disabled) in `frontend/src/pages/SchedulePage.tsx`

**Checkpoint**: Full schedule management UI complete

---

## Phase 6: User Story 5 - Schedule Conflict Handling (Priority: P3)

**Goal**: Warn users when creating overlapping schedules

**Independent Test**: Create overlapping schedule, verify warning is displayed

### Tests for User Story 5 (TDD - Write FIRST, ensure FAIL)

- [X] T036 [P] [US5] Unit test for overlap detection algorithm in `tests/unit/test_schedule_service.py`

### Implementation for US5

- [X] T037 [US5] Implement check_conflicts() method in `app/services/schedule_service.py`
- [X] T038 [US5] Return conflicts array in schedule create/update responses in `app/api/schedules.py`
- [X] T039 [US5] Add conflict warning UI to ScheduleForm in `frontend/src/components/ScheduleForm.tsx`
- [X] T040 [US5] Implement priority-based resolution in ScheduleEvaluator in `frontend/src/player/services/ScheduleEvaluator.ts`

**Checkpoint**: Conflict detection and resolution complete

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T041 [P] Add logging for schedule operations in `app/services/schedule_service.py`
- [X] T042 [P] Add error handling for playlist deletion with active schedules in `app/api/playlists.py`
- [X] T043 Run database migration and verify schema in `data/castplay.db`
- [X] T044 Validate quickstart.md scenarios end-to-end

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-6)**: All depend on Foundational phase completion
  - US1 & US2 (Phase 3): MVP - can start immediately after foundational
  - US3 (Phase 4): Depends on US1/US2 backend being complete
  - US4 (Phase 5): Depends on US1/US2 frontend being complete
  - US5 (Phase 6): Depends on US1/US2 backend being complete
- **Polish (Phase 7)**: Depends on all user stories being complete

### User Story Dependencies

- **US1 & US2 (P1)**: Core CRUD + auto-switching - No dependencies on other stories
- **US3 (P2)**: Extends US1/US2 with day-of-week support
- **US4 (P2)**: UX enhancements for US1/US2
- **US5 (P3)**: Conflict detection extends US1 create/update

### Within Each User Story

- Tests MUST be written and FAIL before implementation (TDD)
- Models before services
- Services before API endpoints
- Backend before frontend for each feature
- Core implementation before integration

### Parallel Opportunities

- T003, T004 can run in parallel (different files)
- T007, T008, T009, T010 can run in parallel (different test files)
- T019, T020 can run in parallel (different frontend files)
- T024, T025 can run in parallel (different player files)

---

## Parallel Example: User Story 1 & 2 Tests

```bash
# Launch all tests for US1 & US2 together:
Task: "Unit test for time range validation in tests/unit/test_schedule_service.py"
Task: "Unit test for days_of_week bitmask validation in tests/unit/test_schedule_service.py"
Task: "Integration test for schedule CRUD endpoints in tests/integration/test_schedule_api.py"
Task: "Unit test for schedule evaluation logic in tests/unit/test_schedule_service.py"
```

---

## Implementation Strategy

### MVP First (User Stories 1 & 2 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Stories 1 & 2
4. **STOP and VALIDATE**: Create a schedule, verify playlist switches at scheduled time
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add US1 & US2 → Test independently → Deploy/Demo (MVP!)
3. Add US3 (weekly patterns) → Test independently → Deploy/Demo
4. Add US4 (management UI) → Test independently → Deploy/Demo
5. Add US5 (conflict handling) → Test independently → Deploy/Demo
6. Each story adds value without breaking previous stories

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing (TDD per constitution)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Total tasks: 44
