# Quickstart: Player Configuration UI

**Feature**: 003-player-config-ui
**Date**: 2026-03-16

## Prerequisites

- Backend server running on `http://localhost:8000`
- Frontend dev server: `cd frontend && npm run dev`
- At least one device registered in the system
- At least two playlists assigned to test device

## Test Scenarios

### Scenario 1: First-Time Server Configuration

**Goal**: Verify server configuration dialog appears and saves correctly

**Steps**:
1. Clear localStorage: `localStorage.clear()` in browser console
2. Open player page: `http://localhost:3000/player.html`
3. **Expected**: Server configuration dialog appears
4. Enter server address: `localhost:8000`
5. Click "Save"
6. **Expected**: Dialog closes, player attempts connection
7. Verify in console: `localStorage.getItem('castplay_server_config')` shows saved config

**Success Criteria**:
- ✅ Dialog appears when no config exists
- ✅ Address validated before save
- ✅ Config persisted to localStorage
- ✅ Player proceeds to next step (registration)

---

### Scenario 2: Invalid Server Address Handling

**Goal**: Verify validation error messages

**Steps**:
1. Clear localStorage
2. Open player page
3. Enter invalid address: `htp://invalid`
4. Click "Save"
5. **Expected**: Error message "请输入有效的 IP 地址或域名"
6. Enter valid address: `192.168.1.100:8000`
7. **Expected**: Form accepts input

**Success Criteria**:
- ✅ Malformed addresses rejected with clear message
- ✅ Valid addresses accepted

---

### Scenario 3: Registration Code Display

**Goal**: Verify registration code is shown for unregistered devices

**Steps**:
1. Set build env: `VITE_REGISTRATION_CODE=TESTCODE123`
2. Clear device registration from localStorage
3. Start player (after server config)
4. **Expected**: Registration code screen shows "TESTCODE123"
5. Click "Copy" button
6. **Expected**: Code copied to clipboard (check with paste)

**Success Criteria**:
- ✅ Registration code displayed clearly
- ✅ Copy button works
- ✅ Visual confirmation of copy action

---

### Scenario 4: Skip Registration for Already Registered Device

**Goal**: Verify registration screen is skipped when device is registered

**Steps**:
1. Complete registration for a device
2. Reload player page
3. **Expected**: Registration screen skipped
4. Verify `isRegistered: true` in localStorage

**Success Criteria**:
- ✅ Registered devices skip registration screen
- ✅ Player proceeds directly to playlist view

---

### Scenario 5: Multi-Playlist Selection

**Goal**: Verify playlist selection interface with multiple playlists

**Steps**:
1. Ensure test device has 3+ playlists assigned
2. Clear playlist selection: `localStorage.removeItem('castplay_playlist_selection')`
3. Start player (complete server config and registration first)
4. **Expected**: Playlist selection interface appears with all 3 playlists
5. Verify checkboxes for each playlist
6. Uncheck playlist 2, keep playlists 1 and 3 checked
7. Click "Confirm"
8. **Expected**: Only playlists 1 and 3 play in rotation
9. Verify selection saved in localStorage

**Success Criteria**:
- ✅ All assigned playlists displayed
- ✅ Checkboxes for each playlist
- ✅ Selection persisted
- ✅ Only selected playlists play

---

### Scenario 6: Select All / Deselect All

**Goal**: Verify bulk selection actions

**Steps**:
1. Open playlist selection interface
2. Click "Deselect All"
3. **Expected**: One playlist remains checked (minimum enforcement)
4. Click "Select All"
5. **Expected**: All playlists checked
6. Click "Deselect All" repeatedly
7. **Expected**: Cannot deselect last playlist, shows message

**Success Criteria**:
- ✅ Select All checks all playlists
- ✅ Deselect All unchecks all but one
- ✅ Minimum one selection enforced
- ✅ User-friendly message shown

---

### Scenario 7: Remember Selection on Restart

**Goal**: Verify selection persists across app restarts

**Steps**:
1. Select playlists 1 and 3
2. Click "Confirm"
3. Reload player page
4. **Expected**: Player starts with playlists 1 and 3 (no selection dialog)
5. Verify localStorage has correct `selectedIds`

**Success Criteria**:
- ✅ Previous selection remembered
- ✅ Selection dialog not shown on restart

---

### Scenario 8: Single Playlist Auto-Skip

**Goal**: Verify selection interface is skipped for single playlist

**Steps**:
1. Ensure device has exactly 1 playlist assigned
2. Start player
3. **Expected**: Playlist selection interface NOT shown
4. **Expected**: Single playlist plays directly

**Success Criteria**:
- ✅ No selection dialog for single playlist
- ✅ Direct playback starts

---

### Scenario 9: Settings Access After Configuration

**Goal**: Verify settings icon provides access to modify config

**Steps**:
1. Complete initial setup
2. Look for gear icon in top-right corner
3. Click gear icon
4. **Expected**: Server configuration dialog opens (edit mode)
5. Change server address
6. Click "Save"
7. **Expected**: New config saved and applied

**Success Criteria**:
- ✅ Settings icon visible and accessible
- ✅ Configuration can be modified after initial setup
- ✅ Changes persisted

---

### Scenario 10: Server Unreachable Error Handling

**Goal**: Verify error handling for unreachable server

**Steps**:
1. Clear localStorage
2. Start player
3. Enter unreachable address: `192.168.99.99:9999`
4. Click "Save"
5. **Expected**: Error dialog with "Retry" and "Change Server" options
6. Click "Change Server"
7. **Expected**: Back to configuration dialog
8. Enter correct address
9. **Expected**: Connection succeeds

**Success Criteria**:
- ✅ Connection failure detected
- ✅ Clear error message with options
- ✅ Retry and change server work

---

## Android-Specific Tests

### Scenario A1: Android JsBridge Storage

**Goal**: Verify config persists via Android SharedPreferences

**Steps**:
1. Build APK with `REGISTRATION_CODE=ANDROIDTEST`
2. Install on Android device/emulator
3. Complete server configuration
4. Close app completely
5. Reopen app
6. **Expected**: Server config remembered (no config dialog)

**Success Criteria**:
- ✅ Config persists via JsBridge
- ✅ No reconfiguration needed on restart

### Scenario A2: Touch Interactions

**Goal**: Verify UI works correctly on touch devices

**Steps**:
1. Open player on Android device
2. Test scrolling in playlist selection
3. Test checkbox toggle with finger tap
4. Test button clicks

**Success Criteria**:
- ✅ Touch scrolling smooth
- ✅ Checkboxes respond to tap
- ✅ Buttons respond to tap
- ✅ No touch-related UI glitches

---

## Quick Validation Commands

```bash
# Start backend
python scripts/server/start.py

# Start frontend
cd frontend && npm run dev

# Build with registration code
REGISTRATION_CODE=TEST123 npm run build

# Clear localStorage (in browser console)
localStorage.clear()

# Check stored config (in browser console)
console.log(JSON.parse(localStorage.getItem('castplay_server_config')));
console.log(JSON.parse(localStorage.getItem('castplay_playlist_selection')));
```
