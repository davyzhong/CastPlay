# Feature Specification: Playlist Scheduling

**Feature Branch**: `001-playlist-scheduling`
**Created**: 2026-03-16
**Status**: Draft
**Input**: User description: "Create a scheduling feature that allows devices to automatically switch playlists based on time of day"

## Clarifications

### Session 2026-03-16

- Q: Who is allowed to create, edit, and delete schedule rules? → A: Any authenticated user can manage schedules.
- Q: Is there a maximum number of schedules per device? → A: No hard limit, users manage their own schedule complexity.
- Q: When no schedule matches the current time, what should the device play? → A: Play the first assigned playlist for that device.
- Q: Should schedules support overnight time ranges (end time earlier than start time)? → A: No, schedules must be within the same calendar day (max 24 hours).
- Q: How should playlist switching behave at scheduled times? → A: Finish current media item, then switch to new playlist.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Create Time-Based Schedule (Priority: P1)

As a display manager, I want to configure a device to automatically switch to a specific playlist at a designated time so that the correct content displays during business hours without manual intervention.

**Why this priority**: This is the core value proposition - automating playlist switching based on time. Without this, there's no scheduling feature.

**Independent Test**: Create a schedule rule for a device, verify the rule is saved and displays correctly in the schedule list.

**Acceptance Scenarios**:

1. **Given** a device with multiple assigned playlists, **When** I create a schedule rule specifying Playlist A should activate at 09:00, **Then** the schedule rule is saved and visible in the device's schedule list.
2. **Given** a device with an existing schedule, **When** I create another schedule for a different time slot, **Then** both schedules coexist without conflict.
3. **Given** I'm creating a schedule, **When** I specify invalid time (e.g., end time before start time), **Then** the system rejects the input with a clear error message.

---

### User Story 2 - Automatic Playlist Switching (Priority: P1)

As a display device, I want to automatically switch to the scheduled playlist when the scheduled time arrives so that content changes happen reliably without network dependency.

**Why this priority**: This is the functional core - schedules must actually trigger playlist changes. Without this, schedules are just records with no effect.

**Independent Test**: Set a schedule to activate in 1 minute, wait for the trigger, verify the device displays the correct playlist.

**Acceptance Scenarios**:

1. **Given** a device has a schedule for Playlist B at 14:00, **When** the time reaches 14:00, **Then** the device automatically switches to Playlist B.
2. **Given** a device is offline at the scheduled switch time, **When** the device comes back online, **Then** it switches to the currently active scheduled playlist.
3. **Given** no schedule applies to the current time, **When** the device checks for active playlist, **Then** it continues playing the current or default playlist.

---

### User Story 3 - Weekly Schedule Patterns (Priority: P2)

As a display manager, I want to configure schedules that repeat on specific days of the week so that I can have different content on weekdays versus weekends without creating seven separate schedules.

**Why this priority**: Reduces management overhead for common patterns (weekdays vs weekends), but the system is functional without it.

**Independent Test**: Create a schedule for Monday-Friday at 09:00, verify it only triggers on those days.

**Acceptance Scenarios**:

1. **Given** I create a schedule for Monday-Friday at 09:00 with Playlist A, **When** it's Monday at 09:00, **Then** Playlist A activates.
2. **Given** I create a schedule for Monday-Friday at 09:00 with Playlist A, **When** it's Saturday at 09:00, **Then** the schedule does not trigger.
3. **Given** a schedule for all seven days, **When** I view the schedule, **Then** I see it repeats daily.

---

### User Story 4 - Schedule Management (Priority: P2)

As a display manager, I want to view, edit, and delete schedule rules so that I can maintain accurate scheduling over time.

**Why this priority**: Essential for ongoing operations, but basic create/delete is covered by Story 1.

**Independent Test**: Create a schedule, modify its time, verify the update persists; delete a schedule, verify it's removed.

**Acceptance Scenarios**:

1. **Given** a device has existing schedules, **When** I view the device details, **Then** I see all schedules sorted by time.
2. **Given** a schedule exists, **When** I edit the time or playlist, **Then** the changes take effect immediately for future triggers.
3. **Given** a schedule exists, **When** I delete it, **Then** it no longer appears in the list and no longer triggers.

---

### User Story 5 - Schedule Conflict Handling (Priority: P3)

As a display manager, I want the system to warn me when creating overlapping schedules so that I can resolve conflicts before they cause display issues.

**Why this priority**: Improves user experience but system can function with manual conflict resolution.

**Independent Test**: Create overlapping schedules for the same time, verify a warning is displayed.

**Acceptance Scenarios**:

1. **Given** a schedule exists for 09:00-12:00 on Monday, **When** I create another schedule for 10:00-11:00 on Monday, **Then** the system warns about the overlap.
2. **Given** an overlap warning, **When** I confirm the overlap is intentional, **Then** the system allows saving both schedules.
3. **Given** multiple schedules match the current time, **When** the device evaluates which to play, **Then** it uses the schedule with highest `priority` value (ties broken by most recently created).

---

### Edge Cases

- What happens when daylight saving time changes? Schedule times should respect the device's timezone.
- What happens when a playlist assigned to a schedule is deleted? The schedule becomes invalid and should be flagged or disabled.
- What happens when a device has no active schedule? It plays the "default" playlist, defined as the playlist with the lowest `device_playlists.id` (oldest assignment to that device).
- What happens when schedules span midnight (e.g., 22:00-02:00)? Not supported. Users must create two separate schedules (e.g., 22:00-23:59 and 00:00-02:00) for overnight coverage.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST allow authenticated users to create schedule rules linking a device, a playlist, and a time range (within a single calendar day, max 24 hours).
- **FR-002**: System MUST support specifying which days of the week a schedule applies to.
- **FR-003**: System MUST automatically activate the scheduled playlist when the scheduled time begins.
- **FR-004**: System MUST support multiple schedules per device with different time slots (no hard limit enforced).
- **FR-005**: System MUST persist schedule rules so they survive server restarts.
- **FR-006**: System MUST allow authenticated users to edit and delete existing schedule rules.
- **FR-007**: System MUST display all schedules for a device in a list view sorted by time.
- **FR-008**: Devices MUST be able to evaluate schedules locally when offline (schedule data synced to device).
- **FR-009**: System MUST finish the currently playing media item before switching to a newly scheduled playlist (no mid-playback interruption).
- **FR-010**: System MUST warn users when creating overlapping schedules for the same device.

### Key Entities

- **PlaylistSchedule**: Represents a schedule rule. Contains: device reference, playlist reference, start time, end time, days of week, enabled status, priority.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can create a schedule rule in under 30 seconds through the management interface.
- **SC-002**: Playlist switches occur within 5 seconds of the scheduled time.
- **SC-003**: Devices with offline schedules switch correctly when the scheduled time arrives, even without network connectivity.
- **SC-004**: 100% of schedule rules persist correctly across server restarts.
- **SC-005**: Users report 90% satisfaction with schedule management ease-of-use.
- **SC-006**: Schedule conflicts are detected and warned about before saving.

## Assumptions

- Schedules use a single timezone configured at the system level (Asia/Shanghai as per existing scheduler).
- Time ranges are specified in 24-hour format.
- A device can have multiple playlists assigned, but only one plays at a time (existing behavior).
- Schedule changes are pushed to devices via the existing WebSocket notification system.
- The existing APScheduler infrastructure can be extended for schedule evaluation.
