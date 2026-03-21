# Data Model: Player Configuration UI

**Feature**: 003-player-config-ui
**Date**: 2026-03-16

## Entities

### 1. ServerConfig

Configuration for server connection, stored locally on the player device.

| Field | Type | Required | Default | Validation | Description |
|-------|------|----------|---------|------------|-------------|
| address | string | Yes | - | Valid IP/domain format | Server address without protocol |
| port | number | No | 8000 | 1-65535 | Server port (extracted from address if present) |
| protocol | 'http' \| 'https' | No | 'https' | - | Connection protocol |
| configuredAt | ISO datetime | Yes | now | - | When configuration was saved |
| lastConnectionStatus | 'success' \| 'failed' \| 'pending' | No | 'pending' | - | Last connection attempt result |
| lastConnectionAt | ISO datetime | No | null | - | Last connection attempt timestamp |

**State Transitions**:
- `pending` → `success`: Successful connection test
- `pending` → `failed`: Connection test failed
- `success` → `failed`: Subsequent connection fails
- `failed` → `success`: Connection restored

**Storage Key**: `castplay_server_config`

---

### 2. DeviceRegistration

Device registration status and code management.

| Field | Type | Required | Default | Validation | Description |
|-------|------|----------|---------|------------|-------------|
| code | string | Yes | - | Non-empty | Registration code from build config |
| isRegistered | boolean | Yes | false | - | Whether device is registered with server |
| deviceId | string | No | null | UUID format | Assigned device ID after registration |
| registeredAt | ISO datetime | No | null | - | When registration completed |
| registeredBy | string | No | null | - | User/system that completed registration |

**State Transitions**:
- `isRegistered: false` → `isRegistered: true`: Successful registration
- Code is immutable (set at build time)

**Storage Key**: `castplay_device_registration`

**Note**: The registration `code` is read from build-time environment variable `VITE_REGISTRATION_CODE`, not stored in local storage.

---

### 3. PlaylistSelection

User's playlist selection preferences.

| Field | Type | Required | Default | Validation | Description |
|-------|------|----------|---------|------------|-------------|
| selectedIds | number[] | Yes | [] | Min length 1 after user action | IDs of selected playlists |
| updatedAt | ISO datetime | Yes | now | - | When selection was last modified |
| userModified | boolean | Yes | false | - | Whether user explicitly changed selection |

**State Transitions**:
- Initial: `selectedIds` empty, `userModified: false`
- After auto-select (first time): `selectedIds` = all available, `userModified: false`
- After user action: `selectedIds` = user choice, `userModified: true`

**Business Rules**:
- Minimum one playlist must be selected (enforced at UI level)
- If `userModified: false`, auto-select all available playlists
- Selection persists across app restarts

**Storage Key**: `castplay_playlist_selection`

---

## Entity Relationships

```
┌─────────────────┐
│  ServerConfig   │
│  (local storage)│
└────────┬────────┘
         │ enables connection to
         ▼
┌─────────────────┐     registers with     ┌─────────────────┐
│    Server       │◄───────────────────────│ DeviceRegistration│
│  (remote)       │                        │ (local + build)  │
└────────┬────────┘                        └──────────────────┘
         │ provides
         ▼
┌─────────────────┐     user selects from    ┌─────────────────┐
│  Playlists[]    │─────────────────────────►│PlaylistSelection│
│  (from server)  │                         │ (local storage) │
└─────────────────┘                         └──────────────────┘
```

---

## TypeScript Interfaces

```typescript
// Stored in localStorage with key 'castplay_server_config'
interface ServerConfig {
  address: string;
  port: number;
  protocol: 'http' | 'https';
  configuredAt: string;
  lastConnectionStatus: 'success' | 'failed' | 'pending';
  lastConnectionAt: string | null;
}

// Stored in localStorage with key 'castplay_device_registration'
interface DeviceRegistration {
  isRegistered: boolean;
  deviceId: string | null;
  registeredAt: string | null;
  registeredBy: string | null;
  // Note: 'code' comes from import.meta.env.VITE_REGISTRATION_CODE
}

// Stored in localStorage with key 'castplay_playlist_selection'
interface PlaylistSelection {
  selectedIds: number[];
  updatedAt: string;
  userModified: boolean;
}

// Combined config state (for Zustand store)
interface PlayerConfigState {
  server: ServerConfig | null;
  registration: DeviceRegistration;
  playlistSelection: PlaylistSelection;

  // Actions
  setServerConfig: (config: Omit<ServerConfig, 'configuredAt' | 'lastConnectionStatus'>) => void;
  updateConnectionStatus: (status: ServerConfig['lastConnectionStatus']) => void;
  setRegistrationComplete: (deviceId: string) => void;
  setPlaylistSelection: (ids: number[], userModified: boolean) => void;
  clearAllConfig: () => void;
}
```

---

## Storage Implementation

### Web Platform (localStorage)

```typescript
// Keys
const STORAGE_KEYS = {
  SERVER_CONFIG: 'castplay_server_config',
  DEVICE_REGISTRATION: 'castplay_device_registration',
  PLAYLIST_SELECTION: 'castplay_playlist_selection',
} as const;

// Read
const config = JSON.parse(localStorage.getItem(STORAGE_KEYS.SERVER_CONFIG) || 'null');

// Write
localStorage.setItem(STORAGE_KEYS.SERVER_CONFIG, JSON.stringify(config));
```

### Android Platform (via JsBridge)

```typescript
// Read
const config = JSON.parse(window.AndroidBridge?.getConfig('castplay_server_config') || 'null');

// Write
window.AndroidBridge?.setConfig('castplay_server_config', JSON.stringify(config));
```

### Abstraction Layer

```typescript
class ConfigStorage {
  private isAndroid = !!window.AndroidBridge;

  get<T>(key: string): T | null {
    const raw = this.isAndroid
      ? window.AndroidBridge?.getConfig(key) || ''
      : localStorage.getItem(key);
    return raw ? JSON.parse(raw) : null;
  }

  set<T>(key: string, value: T): void {
    const raw = JSON.stringify(value);
    if (this.isAndroid) {
      window.AndroidBridge?.setConfig(key, raw);
    } else {
      localStorage.setItem(key, raw);
    }
  }

  remove(key: string): void {
    if (this.isAndroid) {
      window.AndroidBridge?.setConfig(key, '');
    } else {
      localStorage.removeItem(key);
    }
  }
}
```

---

## Validation Rules

### Server Address Validation

```typescript
// Valid formats:
// - 192.168.1.100
// - 192.168.1.100:8080
// - example.com
// - example.com:443
// - https://example.com (protocol stripped)

const ADDRESS_REGEX = /^(https?:\/\/)?([\w.-]+)(:\d+)?$/;

function validateAddress(input: string): { valid: boolean; error?: string } {
  if (!input || input.trim().length === 0) {
    return { valid: false, error: '请输入服务器地址' };
  }

  const match = input.trim().match(ADDRESS_REGEX);
  if (!match) {
    return { valid: false, error: '请输入有效的 IP 地址或域名' };
  }

  const [, , host, port] = match;
  if (port) {
    const portNum = parseInt(port.slice(1), 10);
    if (portNum < 1 || portNum > 65535) {
      return { valid: false, error: '端口号必须在 1-65535 之间' };
    }
  }

  return { valid: true };
}
```

---

## Migration Considerations

No database migration needed - all data stored in local storage on player devices.

For existing deployments:
- Players without config will show setup dialogs on first run
- No backwards compatibility concerns as this is new functionality
