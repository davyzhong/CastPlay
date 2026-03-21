# Research: Player Configuration UI

**Feature**: 003-player-config-ui
**Date**: 2026-03-16

## Research Topics

### 1. Server Address Validation

**Decision**: Use URL constructor for validation with fallback regex

**Rationale**:
- Native URL API handles most cases but requires protocol prefix
- Custom regex needed for bare IP/domain input (e.g., "192.168.1.100")
- Support formats: IP (192.168.1.100), IP:port (192.168.1.100:8080), domain (example.com)

**Implementation**:
```typescript
function validateServerAddress(input: string): { valid: boolean; normalized: string; error?: string } {
  // Add protocol if missing
  const normalized = input.match(/^https?:\/\//) ? input : `http://${input}`;

  try {
    const url = new URL(normalized);
    return { valid: true, normalized: url.origin };
  } catch {
    return { valid: false, normalized: '', error: '请输入有效的 IP 地址或域名' };
  }
}
```

**Alternatives Considered**:
- validator.js library - rejected to avoid new dependency
- Pure regex - rejected as URL constructor handles edge cases better

---

### 2. Local Storage Strategy

**Decision**: Create ConfigStorage abstraction layer with platform detection

**Rationale**:
- Web uses localStorage directly
- Android uses JsBridge to access SharedPreferences
- Abstraction allows same code to work on both platforms
- Single source of truth for configuration data

**Data Schema**:
```typescript
interface StoredConfig {
  serverAddress: string;           // e.g., "http://192.168.1.100:8000"
  serverAddressConfiguredAt: string; // ISO timestamp
  registrationCode: string;        // From build-time env var
  isDeviceRegistered: boolean;
  selectedPlaylistIds: number[];   // For multi-playlist selection
  selectionUpdatedAt?: string;
}
```

**Platform Detection**:
```typescript
const isAndroid = !!window.AndroidBridge;
const storage = isAndroid ? new AndroidStorage() : new WebStorage();
```

**Alternatives Considered**:
- IndexedDB - rejected as overkill for simple config data
- Zustand persist middleware alone - rejected as doesn't handle Android bridge

---

### 3. Registration Code Management

**Decision**: Build-time environment variable embedded at compile

**Rationale**:
- Spec clarifies: `REGISTRATION_CODE=ABC123 npm run build`
- Vite exposes env vars via `import.meta.env.VITE_REGISTRATION_CODE`
- Different builds for different deployment batches
- Code is immutable at runtime (security consideration)

**Implementation**:
```typescript
// vite.config.ts
define: {
  'import.meta.env.VITE_REGISTRATION_CODE': JSON.stringify(process.env.REGISTRATION_CODE || '')
}

// Usage
const registrationCode = import.meta.env.VITE_REGISTRATION_CODE;
```

**Alternatives Considered**:
- Runtime fetch from server - rejected per spec clarification
- Config file - rejected as less secure and harder to manage per-deployment

---

### 4. Multi-Playlist Selection UI Pattern

**Decision**: Checkbox list with Select All / Deselect All, minimum one selection enforced

**Rationale**:
- Checkbox pattern is familiar and touch-friendly
- Select All/Deselect All provides quick actions
- Minimum one selection prevents empty state
- Existing PlaylistSelectionModal provides foundation to extend

**UI Flow**:
1. Display all available playlists with checkboxes
2. Pre-select previously selected playlists (or all if first time)
3. "Select All" / "Deselect All" buttons
4. Disable deselect for last selected playlist
5. Save selection on confirm, remember for next startup

**Alternatives Considered**:
- Drag to reorder - rejected as additional complexity not in spec
- Radio button (single selection) - rejected as spec requires multi-select

---

### 5. Android JsBridge Integration

**Decision**: Extend existing AndroidBridge interface with storage methods

**Rationale**:
- Project already uses AndroidBridge for server URL
- Add get/set methods for config values
- Consistent with existing architecture

**Interface Extension**:
```typescript
interface AndroidBridge {
  // Existing
  getServerUrl(): string;

  // New
  getConfig(key: string): string;
  setConfig(key: string, value: string): void;
  copyToClipboard(text: string): boolean;
}
```

**Android Side (Kotlin)**:
```kotlin
@JavascriptInterface
fun getConfig(key: String): String {
    return sharedPreferences.getString(key, "") ?: ""
}

@JavascriptInterface
fun setConfig(key: String, value: String) {
    sharedPreferences.edit().putString(key, value).apply()
}
```

---

### 6. Protocol Handling (HTTPS with HTTP Fallback)

**Decision**: Try HTTPS first, fallback to HTTP on connection failure

**Rationale**:
- Production prefers HTTPS for security
- Development/testing may use HTTP
- Automatic protocol detection reduces user error

**Implementation**:
```typescript
async function testConnection(baseUrl: string): Promise<{ success: boolean; protocol: 'https' | 'http' }> {
  // Try HTTPS first
  try {
    await fetch(`https://${baseUrl}/api/health`, { method: 'HEAD', signal: AbortSignal.timeout(5000) });
    return { success: true, protocol: 'https' };
  } catch {
    // Fallback to HTTP
    try {
      await fetch(`http://${baseUrl}/api/health`, { method: 'HEAD', signal: AbortSignal.timeout(5000) });
      return { success: true, protocol: 'http' };
    } catch {
      return { success: false, protocol: 'http' };
    }
  }
}
```

---

### 7. Settings Access Pattern

**Decision**: Gear icon in top-right corner, always visible

**Rationale**:
- Spec clarification: Dedicated gear/settings icon
- Common UI pattern understood by users
- Top-right corner is conventional placement
- Always accessible without blocking playback

**Implementation**:
- Floating button positioned fixed top-right
- Opens ServerConfigDialog in edit mode
- Icon from @ant-design/icons (SettingOutlined)

---

## Summary of Decisions

| Topic | Decision | Key Benefit |
|-------|----------|-------------|
| Address Validation | URL constructor + fallback regex | No new dependencies |
| Local Storage | ConfigStorage abstraction | Platform-agnostic code |
| Registration Code | Build-time env var (VITE_*) | Per-deployment customization |
| Multi-Select UI | Checkbox list with min-1 enforcement | Familiar, touch-friendly |
| Android Integration | Extend AndroidBridge | Consistent architecture |
| Protocol Handling | HTTPS first, HTTP fallback | Security + dev flexibility |
| Settings Access | Top-right gear icon | Conventional, always accessible |

## No NEEDS CLARIFICATION Items

All technical decisions resolved based on spec clarifications and existing project patterns.
