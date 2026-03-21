# Data Model: Playlist Scheduling

**Feature**: 001-playlist-scheduling
**Date**: 2026-03-16

## Entity Relationship Diagram

```
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│     Device      │       │ PlaylistSchedule│       │    Playlist     │
├─────────────────┤       ├─────────────────┤       ├─────────────────┤
│ id (PK)         │◄──────│ device_id (FK)  │       │ id (PK)         │
│ name            │       │ playlist_id(FK) │──────►│ name            │
│ ...             │       │ start_time      │       │ description     │
└─────────────────┘       │ end_time        │       │ ...             │
                          │ days_of_week    │       └─────────────────┘
                          │ enabled         │
                          │ priority        │
                          │ created_at      │
                          │ updated_at      │
                          └─────────────────┘
```

## Entities

### PlaylistSchedule

Represents a time-based rule for automatically switching playlists on a device.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | Integer | PK, Auto-increment | Primary key |
| device_id | Integer | FK → devices.id, NOT NULL, Index | Target device |
| playlist_id | Integer | FK → playlists.id, NOT NULL | Playlist to activate |
| start_time | Time | NOT NULL | Schedule start time (HH:MM:SS) |
| end_time | Time | NOT NULL | Schedule end time (HH:MM:SS), must be > start_time |
| days_of_week | Integer | NOT NULL, Default: 127 | Bitmask for days (Mon=1, Tue=2, ..., Sun=64, All=127) |
| enabled | Boolean | NOT NULL, Default: True | Whether schedule is active |
| priority | Integer | NOT NULL, Default: 0 | Higher priority wins when conflicts exist |
| created_at | DateTime | NOT NULL, Auto | Record creation timestamp |
| updated_at | DateTime | NOT NULL, Auto-update | Last modification timestamp |

#### Day of Week Bitmask

| Day | Bit Value | Integer |
|-----|-----------|---------|
| Monday | 0000001 | 1 |
| Tuesday | 0000010 | 2 |
| Wednesday | 0000100 | 4 |
| Thursday | 0001000 | 8 |
| Friday | 0010000 | 16 |
| Saturday | 0100000 | 32 |
| Sunday | 1000000 | 64 |
| All Week | 1111111 | 127 |
| Weekdays | 0011111 | 31 |
| Weekends | 1100000 | 96 |

#### Validation Rules

1. **Time Range**: `end_time` MUST be greater than `start_time` (no overnight schedules)
2. **Device-Playlist Assignment**: The referenced playlist MUST be assigned to the referenced device via `device_playlists` table
3. **Deletion Cascade**: When a playlist is deleted, associated schedules are also deleted (CASCADE)
4. **Enabled Toggle**: Setting `enabled=false` preserves schedule for future reactivation

#### State Transitions

```
┌─────────┐  enable   ┌─────────┐
│ Disabled│ ────────► │ Enabled │
└─────────┘ ◄──────── └─────────┘
              disable
```

Schedules have only two states: Enabled (active) and Disabled (inactive). There is no "expired" state - schedules are recurring.

## Relationships

### Device → PlaylistSchedule (One-to-Many)

- A device can have zero or more schedules
- When a device is deleted, all its schedules are deleted (CASCADE)

### Playlist → PlaylistSchedule (One-to-Many)

- A playlist can be referenced by zero or more schedules
- When a playlist is deleted, all referencing schedules are deleted (CASCADE)

## Indexes

| Index | Columns | Purpose |
|-------|---------|---------|
| idx_schedule_device | device_id | Fast lookup of device's schedules |
| idx_schedule_enabled | enabled | Filter active schedules |
| idx_schedule_time | start_time, end_time | Time range queries |

## Sample Data

```sql
-- Weekday morning schedule (9 AM - 12 PM, Monday-Friday)
INSERT INTO playlist_schedules (device_id, playlist_id, start_time, end_time, days_of_week, enabled, priority)
VALUES (1, 5, '09:00:00', '12:00:00', 31, 1, 0);

-- Weekend all-day schedule (Saturday-Sunday)
INSERT INTO playlist_schedules (device_id, playlist_id, start_time, end_time, days_of_week, enabled, priority)
VALUES (1, 8, '00:00:00', '23:59:59', 96, 1, 0);

-- Lunch hour override (higher priority)
INSERT INTO playlist_schedules (device_id, playlist_id, start_time, end_time, days_of_week, enabled, priority)
VALUES (1, 10, '12:00:00', '13:00:00', 31, 1, 10);
```

## Migration Strategy

1. Create new `playlist_schedules` table
2. Add foreign key constraints
3. Create indexes
4. No data migration needed (new feature)
