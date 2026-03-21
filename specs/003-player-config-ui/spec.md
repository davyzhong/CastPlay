# Feature Specification: Player Configuration UI

**Feature Branch**: `003-player-config-ui`
**Created**: 2026-03-16
**Status**: Draft
**Input**: Add configuration UI features to web player and Android player: 1) on startup, display configuration dialog to set server IP/domain; 2) on startup, if no device registration code exists, display the registration code from production config; 3) after startup, if multiple playlists exist, allow selection of which playlists to include in playback sequence.

## User Scenarios & Testing

### User Story 1 - Server Configuration on Startup (Priority: P1)

When a player (web or Android) starts for the first time or when the server address is not configured, a configuration dialog appears allowing the user to enter the server IP address or domain name. The address is validated and saved locally for future use.

**Why this priority**: Without a valid server address, the player cannot connect to the server to fetch playlists or register the device. This is the foundational requirement for any player functionality.

**Independent Test**: Clear local storage, start player, verify configuration dialog appears, enter a valid IP/domain, verify connection succeeds and address is persisted.

**Acceptance Scenarios**:

1. **Given** player has no saved server address, **When** player starts, **Then** configuration dialog appears with empty address field
2. **Given** configuration dialog is displayed, **When** user enters "192.168.1.100" and clicks Save, **Then** address is saved and player attempts connection
3. **Given** configuration dialog is displayed, **When** user enters "example.com" and clicks Save, **Then** address is saved and player attempts connection
4. **Given** player has saved server address, **When** player starts, **Then** configuration dialog is skipped and player connects directly
5. **Given** configuration dialog is displayed, **When** user clicks "Cancel" or closes dialog, **Then** player shows "Server not configured" message and cannot proceed

---

### User Story 2 - Device Registration Code Display (Priority: P1)

When a player starts and the device is not yet registered (no registration code in local storage), display a screen showing the registration code that was pre-configured during production. This allows field technicians to register the device with the server.

**Why this priority**: Without registration, the device cannot receive playlists from the server. Field technicians need the registration code to complete the setup process.

**Independent Test**: Clear device registration from local storage, start player, verify registration code screen appears with the production-configured code.

**Acceptance Scenarios**:

1. **Given** device has no registration code in local storage, **When** player starts after server configuration, **Then** registration code screen displays the production-configured registration code
2. **Given** device already has a registration code, **When** player starts, **Then** registration code screen is skipped
3. **Given** registration code screen is displayed, **When** user copies the code, **Then** code is copied to clipboard with visual confirmation
4. **Given** device registers successfully with server, **When** registration completes, **Then** registration screen dismisses and player proceeds to playlist view

---

### User Story 3 - Playlist Selection (Priority: P2)

After the player connects to the server and retrieves available playlists, if multiple playlists are assigned to the device, display a playlist selection interface. Users can select one or more playlists to include in the playback sequence. Unselected playlists are excluded from playback.

**Why this priority**: This provides flexibility for users to control which content plays on the device without requiring server-side configuration changes. It is a quality-of-life feature that enhances usability.

**Independent Test**: Assign multiple playlists to a device, start player, verify selection interface shows all playlists, select subset, verify only selected playlists play.

**Acceptance Scenarios**:

1. **Given** device has one playlist assigned, **When** player connects, **Then** playlist selection interface is skipped and single playlist plays directly
2. **Given** device has multiple playlists assigned, **When** player connects, **Then** playlist selection interface displays all available playlists with their names and preview info
3. **Given** playlist selection interface is displayed, **When** user selects playlists A and C (out of A, B, C), **Then** only playlists A and C play in rotation, playlist B is excluded
4. **Given** user has previously selected playlists, **When** player restarts, **Then** previous selection is remembered and applied automatically
5. **Given** playlist selection interface, **When** user clicks "Select All", **Then** all playlists are selected
6. **Given** playlist selection interface, **When** user clicks "Deselect All", **Then** all playlists are deselected except one (minimum selection required)
7. **Given** user attempts to deselect all playlists, **When** only one playlist remains selected, **Then** system prevents deselection and shows "At least one playlist must be selected" message

---

### Edge Cases

- **Invalid server address format**: User enters malformed address (e.g., "192.168.1", "htp://invalid") - display validation error "Please enter a valid IP address or domain name"
- **Server unreachable**: After configuration, server cannot be reached - display connection error with "Retry" and "Change Server" options
- **Registration code not found**: Production build missing registration code - display error "Registration code not configured. Please contact support."
- **Registration fails on server**: Server rejects registration code - display error message with code to retry
- **No playlists assigned**: Device is registered but has no playlists assigned - display "No playlists available. Please contact administrator."
- **Network loss after playlist selection**: Connection is lost after selection - continue playing selected playlists from offline cache
- **All playlists deleted**: All selected playlists are deleted from server - display "No playlists available" and prompt to refresh
- **Single playlist deleted**: One of multiple selected playlists is deleted - automatically remove from selection and continue with remaining playlists
- **Address with custom port**: User enters "192.168.1.100:8080" - accept and use specified port

## Requirements

### Functional Requirements

**Server Configuration:**
- **FR-001**: Player MUST display a server configuration dialog on first startup or when no server address is saved
- **FR-002**: Server configuration dialog MUST accept IP addresses (e.g., "192.168.1.100") and domain names (e.g., "example.com")
- **FR-003**: Server configuration dialog MUST accept addresses with custom ports (e.g., "192.168.1.100:8080")
- **FR-004**: Player MUST validate the entered address format before attempting connection
- **FR-005**: Player MUST persist the server address in local storage for subsequent startups
- **FR-006**: Player MUST provide a way to re-open server configuration from settings after initial setup

**Device Registration:**
- **FR-007**: Player MUST display the production-configured registration code when device is not registered
- **FR-008**: Registration code display MUST show the code in a clear, large, readable format
- **FR-009**: Registration code display MUST provide a "Copy" button to copy code to clipboard
- **FR-010**: Player MUST detect if device is already registered and skip registration code display
- **FR-011**: Player MUST automatically proceed to playlist view after successful registration

**Playlist Selection:**
- **FR-012**: Player MUST fetch and display all playlists assigned to the device after registration
- **FR-013**: Playlist selection interface MUST show playlist name for each available playlist
- **FR-014**: Playlist selection interface MUST allow multi-select (checkbox or toggle) for each playlist
- **FR-015**: Player MUST only play playlists that are selected in the selection interface
- **FR-016**: Player MUST persist playlist selection in local storage for subsequent startups
- **FR-017**: Player MUST provide "Select All" action in playlist selection interface
- **FR-018**: Player MUST provide "Deselect All" action in playlist selection interface
- **FR-019**: Player MUST enforce minimum selection of one playlist (cannot deselect all)
- **FR-020**: Playlist selection interface MUST be skipped when only one playlist is assigned

### Key Entities

- **ServerConfig**: Server address (IP or domain), optional port, last connection status, configuration timestamp
- **DeviceRegistration**: Registration code (from production config), registration status, device UUID, registered timestamp
- **PlaylistSelection**: List of selected playlist IDs, selection timestamp, user-modified flag

## Success Criteria

### Measurable Outcomes

- **SC-001**: Users can configure server address in under 30 seconds on first startup
- **SC-002**: Registration code is visible and copyable within 5 seconds of display
- **SC-003**: Playlist selection interface loads within 3 seconds after server connection
- **SC-004**: Players remember all configuration across restarts without requiring re-entry
- **SC-005**: Playlist selection changes take effect immediately without requiring player restart
- **SC-006**: Configuration dialogs display correctly on both web browser and Android WebView
- **SC-007**: Touch interactions work correctly on Android devices

## Clarifications

### Session 2026-03-16

- Q: How is the registration code configured and embedded during production? → A: Build-time environment variable (e.g., `REGISTRATION_CODE=ABC123 npm run build`) - Code is embedded at build time, different APKs/web builds for different deployment batches
- Q: How does the user access the settings menu to modify server configuration after initial setup? → A: Dedicated gear/settings icon in the top-right corner of the player screen - visible but unobtrusive, common pattern, always accessible
- Q: What protocol should the player use when connecting to the server? → A: HTTPS preferred with HTTP fallback - Production uses HTTPS for security, development/testing can use HTTP, automatic protocol detection

## Assumptions
- Server address validation uses standard IP/domain format rules (no protocol prefix needed)
- Local storage is available and persistent on both web (localStorage) and Android (SharedPreferences/DataStore) platforms
- This feature applies to both web player (player.html) and Android WebView player
- Android platform provides JsBridge for accessing native storage and clipboard
- Default server port is 8000 if not specified in the address
