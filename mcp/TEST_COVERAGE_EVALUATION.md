# Test Coverage Evaluation: CastPlay MCP Servers, CLI, and Skills

## Executive Summary

This evaluation covers the testing strategy and coverage for:
- **MCP Servers**: 6 servers totaling ~3,665 lines
- **CLI Commands**: ~3,659 lines across 10 command modules
- **Skills**: 3 skill files for workflow guidance
- **Existing Test Suite**: 16,180 lines across 47+ test files

## Critical Finding: Zero Test Coverage for MCP and CLI

The most significant finding is that **MCP servers and CLI commands have essentially zero dedicated unit tests**. The only test file is `mcp/test_all_mcp_tools.py`, which is an integration test that requires a running server.

---

## 1. Test Coverage Analysis

### 1.1 MCP Servers - Coverage: ~0%

| Server | File | Lines | Test File |
|--------|------|-------|-----------|
| Device Control | `device_control_server.py` | 487 | None |
| Playlist Manager | `playlist_manager_server.py` | 640 | None |
| Schedule Manager | `schedule_manager_server.py` | 395 | None |
| PPT Converter | `ppt_converter_server.py` | 378 | None |
| Android Tools | `android_tools_server.py` | 687 | None |
| File Processor | `file_processor_server.py` | TBD | None |

**Total MCP Code**: ~3,665 lines
**Total MCP Tests**: 1 integration test (333 lines, requires live server)

#### Untested Critical Paths in MCP Servers:

**Severity: CRITICAL**

1. **All MCP tool functions** - Every `@mcp.tool()` decorated function has zero unit tests
2. **Error handling branches** - No tests for HTTP errors, timeouts, malformed responses
3. **Input validation** - No tests for edge cases (negative IDs, empty strings, invalid formats)
4. **Configuration persistence** - `configure_api()` writes tokens to disk untested

**Example untested function**:
```python
# device_control_server.py - lines 205-230
@mcp.tool()
async def set_volume(device_id: int, volume: int) -> dict:
    if not 0 <= volume <= 100:
        return {"success": False, "error": "Volume must be between 0 and 100"}
    # ... untested: volume = -1, volume = 101, volume = "abc"
```

### 1.2 CLI Commands - Coverage: ~0%

| Module | File | Lines | Test File |
|--------|------|-------|-----------|
| Main | `main.py` | 671 | None |
| API Client | `api_client.py` | 463 | None |
| Config | `config.py` | 108 | None |
| Devices | `devices.py` | 287 | None |
| Playlists | `playlists.py` | ~300 | None |
| Schedules | `schedules.py` | 552 | None |
| Control | `control.py` | 178 | None |
| Media | `media.py` | ~200 | None |
| Status | `status.py` | ~150 | None |
| Server | `server.py` | ~150 | None |
| DB | `db.py` | ~100 | None |

**Total CLI Code**: ~3,659 lines
**Total CLI Tests**: 0

#### Untested Critical Paths in CLI:

**Severity: CRITICAL**

1. **API Client** - No tests for authentication, error handling, retry logic
2. **Configuration** - Token storage in plain text (security issue), no tests for config persistence
3. **Command parsing** - No tests for argument validation, edge cases
4. **Output formatting** - No tests for table/JSON formatting

---

## 2. Test Quality Analysis

### 2.1 Existing Test Suite Quality (Backend)

The existing test suite for the FastAPI backend is well-structured:

**Strengths:**
- Good fixture organization (`conftest.py`)
- Security tests exist (`test_security.py`, `test_injection.py`, `test_file_upload.py`)
- Coverage for auth, devices, playlists, media APIs

**Weaknesses:**
- Token expiration test is skipped (line 148 in `test_security.py`)
- Some security tests are incomplete (pass statements instead of assertions)

### 2.2 MCP Test Script Quality - Poor

The `test_all_mcp_tools.py` script has significant issues:

**Severity: HIGH**

1. **Not a unit test** - Requires running server, tests against real API
2. **No isolation** - Creates real playlists/schedules, no cleanup verification
3. **Skips tests based on runtime state** - Lines 97-99 skip control commands if device offline
4. **No assertions** - Uses `print()` instead of `assert`
5. **No mocking** - Tests real HTTP calls, no mocked responses

**Example of poor test**:
```python
# Lines 156-161 - Skipping test based on API response, not testing behavior
if result.get("error", "").endswith("405"):
    print("  O create_playlist (API doesn't support POST)")
    results.append(("create_playlist", True))  # Expected behavior - FALSE POSITIVE
```

---

## 3. Test Pyramid Adherence

### Current State (Severely Inverted)

```
       /\
      /  \        E2E: ~5 tests (real server required)
     /----\
    /      \      Integration: ~20 tests (API tests)
   /--------\
  /          \    Unit: ~25 tests (mostly backend)
 /------------\
```

### Recommended State

```
       /\
      /  \        E2E: 5-10 tests
     /----\
    /      \      Integration: 50+ tests (MCP, CLI integration)
   /--------\
  /          \    Unit: 200+ tests (MCP tools, CLI commands)
 /------------\
```

---

## 4. Edge Cases Not Tested

### 4.1 MCP Servers - Critical Edge Cases

**Severity: CRITICAL**

| Server | Untested Edge Case | Risk |
|--------|-------------------|------|
| Device Control | Device ID = 0, -1, "abc" | Injection/crash |
| Device Control | Volume = -1, 101, "loud" | Input validation bypass |
| Schedule Manager | Time format: "25:00", "abc", "" | Schedule corruption |
| Schedule Manager | Weekdays: [7], [-1], [] | Invalid bitmask |
| Playlist Manager | Empty playlist name, SQL chars | Injection |
| PPT Converter | Non-existent file, corrupted PPT | File handling |
| Android Tools | Invalid AVD name, SDK not installed | Environment issues |

### 4.2 CLI - Critical Edge Cases

**Severity: CRITICAL**

| Command | Untested Edge Case | Risk |
|---------|-------------------|------|
| `schedules create` | Time without seconds | API mismatch |
| `control volume` | Level = "abc", -1, 1000 | Input validation |
| `devices schedule` | Invalid weekday string | Parsing error |
| Config login | Invalid credentials, network error | Error handling |

---

## 5. Security Test Gaps

### 5.1 MCP Security - Severity: CRITICAL

**No security tests exist for:**

1. **Token Storage** (`device_control_server.py` lines 452-475)
   ```python
   # Token written to disk in plain text - NO ENCRYPTION
   with open(config_path, "w", encoding="utf-8") as f:
       json.dump(config, f, indent=2)  # Token stored as plain text
   ```

2. **Input Validation Gaps** (`schedule_manager_server.py` lines 99-100)
   ```python
   # No validation for time format - accepts any string
   start_time: Start time in HH:MM:SS format (e.g., "08:00:00")
   # But no regex validation exists!
   ```

3. **Exception Swallowing** (`device_control_server.py` lines 100-123)
   ```python
   # Falls back silently without proper logging
   except Exception as e:
       logger.warning(f"Online status endpoint failed, falling back: {e}")
       # No re-raise, no structured error tracking
   ```

### 5.2 CLI Security - Severity: HIGH

**No security tests exist for:**

1. **Plain text token storage** (`config.py` lines 53-54)
   ```python
   # Token stored in ~/.castplay/config.json as plain text
   json.dump(self.config.model_dump(exclude_none=True), f, indent=2)
   ```

2. **No token expiration handling**
3. **No rate limiting in CLI client**

### 5.3 Recommended Security Tests

```python
# test_mcp_security.py - Recommended tests

class TestMCPSecurity:
    def test_token_not_logged(self):
        """Verify tokens are never logged"""

    def test_token_encrypted_at_rest(self):
        """Verify tokens are encrypted when stored"""

    def test_sql_injection_in_device_name(self):
        """Test SQL injection in device name parameter"""

    def test_time_format_validation(self):
        """Test that invalid time formats are rejected"""
        # Should reject: "25:00:00", "abc", "'; DROP TABLE--"

    def test_path_traversal_in_ppt_converter(self):
        """Test path traversal attempts in PPT conversion"""
        # Should reject: "../../../etc/passwd"
```

---

## 6. Performance Test Gaps

### 6.1 Connection Pooling - Severity: HIGH

The shared API client uses a singleton pattern for connection pooling, but there are no tests for:

1. **Concurrent access** - Multiple simultaneous requests
2. **Connection limits** - What happens with 100+ concurrent requests?
3. **Connection reuse** - Is the pool actually being reused?
4. **Timeout handling** - Network timeout scenarios

**Recommended test**:
```python
# test_mcp_performance.py

import asyncio
import pytest

class TestMCPPerformance:
    @pytest.mark.performance
    async def test_concurrent_device_requests(self):
        """Test 100 concurrent device list requests"""
        tasks = [list_devices() for _ in range(100)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        # All should succeed, no connection errors
        assert all(r.get("success", False) for r in results if isinstance(r, dict))

    @pytest.mark.performance
    async def test_connection_pool_reuse(self):
        """Verify connection pool is reused, not recreated"""
        # Implementation would track socket creation
```

### 6.2 CLI Performance - Severity: MEDIUM

No performance tests exist for:
- Large device lists (1000+ devices)
- Large playlist item batches
- File upload progress handling

---

## 7. Test Maintainability Issues

### 7.1 MCP Test Script - Severity: MEDIUM

Issues in `test_all_mcp_tools.py`:

1. **No cleanup** - Creates playlists/schedules but doesn't verify deletion
2. **Hardcoded IDs** - Uses `device_id = 1`, `playlist_id = 1`
3. **Conditional skipping** - Skips tests based on runtime conditions
4. **No parametrization** - Same test for multiple inputs not implemented

### 7.2 Test Isolation Issues

```python
# Current test - depends on server state
result = await list_devices()
device_id = devices[0]["id"] if devices else 1  # What if no devices?

# Recommended - use mocks
@pytest.fixture
def mock_httpx_client():
    with patch("httpx.AsyncClient") as mock:
        mock.return_value.get.return_value = {"items": [{"id": 1, "name": "test"}]}
        yield mock
```

---

## 8. Specific Test Recommendations

### 8.1 MCP Server Unit Tests (Priority: CRITICAL)

Create `mcp/tests/` directory with:

```
mcp/tests/
  __init__.py
  conftest.py              # Shared fixtures
  test_device_control.py  # Device Control MCP tests
  test_playlist_manager.py # Playlist Manager MCP tests
  test_schedule_manager.py # Schedule Manager MCP tests
  test_ppt_converter.py   # PPT Converter MCP tests
  test_android_tools.py   # Android Tools MCP tests
```

**Example test structure**:

```python
# mcp/tests/test_device_control.py

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx

# Import the module under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "device-control"))
from device_control_server import (
    list_devices, get_device, set_volume, configure_api
)

class TestDeviceControlMCP:
    """Unit tests for Device Control MCP"""

    @pytest.fixture
    def mock_client(self):
        """Mock the shared API client"""
        with patch("device_control_server.get_client") as mock:
            client = AsyncMock()
            mock.return_value = client
            yield client

    @pytest.mark.asyncio
    async def test_list_devices_success(self, mock_client):
        """Test successful device listing"""
        mock_client.get.return_value = {
            "items": [{"id": 1, "name": "Device 1", "is_online": True}]
        }

        result = await list_devices()

        assert result["success"] is True
        assert result["count"] == 1
        assert len(result["devices"]) == 1

    @pytest.mark.asyncio
    async def test_list_devices_online_only(self, mock_client):
        """Test filtering online devices"""
        mock_client.get.return_value = {
            "items": [
                {"id": 1, "name": "Online", "is_online": True},
                {"id": 2, "name": "Offline", "is_online": False}
            ]
        }

        result = await list_devices(online_only=True)

        assert result["count"] == 1
        assert result["devices"][0]["name"] == "Online"

    @pytest.mark.asyncio
    async def test_set_volume_validation(self, mock_client):
        """Test volume input validation"""
        # Volume too low
        result = await set_volume(1, -1)
        assert result["success"] is False
        assert "between 0 and 100" in result["error"]

        # Volume too high
        result = await set_volume(1, 101)
        assert result["success"] is False

        # Volume not integer - should be caught by type hints
        with pytest.raises(TypeError):
            await set_volume(1, "loud")

    @pytest.mark.asyncio
    async def test_set_volume_success(self, mock_client):
        """Test successful volume setting"""
        mock_client.post.return_value = {"message": "Volume set"}

        result = await set_volume(1, 50)

        assert result["success"] is True
        assert result["volume"] == 50

    @pytest.mark.asyncio
    async def test_get_device_not_found(self, mock_client):
        """Test device not found handling"""
        mock_client.get.side_effect = httpx.HTTPStatusError(
            "Not found",
            request=MagicMock(),
            response=MagicMock(status_code=404)
        )

        result = await get_device(999)

        assert result["success"] is False
        assert "not found" in result["error"].lower()

    def test_configure_api_token_storage(self, tmp_path):
        """Test that configure_api stores token securely"""
        # This test would fail currently - tokens are stored in plain text
        config_path = tmp_path / "config.json"

        result = configure_api("http://localhost:8000", "secret-token")

        assert result["success"] is True
        # SECURITY TEST: Verify token is not stored in plain text
        with open(config_path) as f:
            content = f.read()
            assert "secret-token" not in content  # Currently FAILS
```

### 8.2 CLI Unit Tests (Priority: CRITICAL)

Create `cli/tests/` directory:

```python
# cli/tests/test_api_client.py

import pytest
from unittest.mock import patch, MagicMock
import httpx

from cli.api_client import APIClient, APIError

class TestAPIClient:
    @pytest.fixture
    def client(self):
        return APIClient(server_url="http://test", token="test-token")

    def test_login_success(self, client):
        """Test successful login"""
        with patch.object(client, "_request") as mock:
            mock.return_value = {"access_token": "new-token", "user": {"username": "test"}}
            result = client.login("user", "pass")
            assert result["access_token"] == "new-token"

    def test_api_error_handling(self, client):
        """Test API error response handling"""
        with patch("httpx.Client.request") as mock:
            mock.return_value = MagicMock(
                status_code=404,
                reason_phrase="Not Found",
                json=lambda: {"detail": "Resource not found"}
            )
            with pytest.raises(APIError) as exc:
                client._request("GET", "/api/unknown")
            assert exc.value.status_code == 404

    def test_204_response_handling(self, client):
        """Test handling of 204 No Content responses"""
        with patch("httpx.Client.request") as mock:
            mock.return_value = MagicMock(status_code=204)
            result = client._request("DELETE", "/api/test/1")
            assert result == {"success": True}

# cli/tests/test_schedules.py

class TestScheduleCommands:
    def test_format_time_with_seconds(self):
        """Test time format with seconds"""
        from cli.commands.schedules import format_time
        assert format_time("08:00") == "08:00:00"
        assert format_time("08:00:30") == "08:00:30"

    def test_format_time_invalid(self):
        """Test invalid time format handling"""
        from cli.commands.schedules import format_time
        # Should return as-is (API will validate)
        assert format_time("invalid") == "invalid"

    def test_parse_weekdays_valid(self):
        """Test valid weekday parsing"""
        from cli.commands.schedules import parse_weekdays
        assert parse_weekdays("0,1,2,3,4") == [0, 1, 2, 3, 4]
        assert parse_weekdays("") == []

    def test_parse_weekdays_invalid(self):
        """Test invalid weekday handling"""
        from cli.commands.schedules import parse_weekdays
        # Currently crashes - need error handling
        with pytest.raises(ValueError):
            parse_weekdays("7,8,9")  # Invalid days
```

### 8.3 Integration Tests (Priority: HIGH)

```python
# tests/integration/test_mcp_integration.py

import pytest
import httpx
from testcontainers.core.container import DockerContainer

@pytest.fixture
def castplay_server():
    """Start CastPlay server in Docker for integration tests"""
    with DockerContainer("castplay:latest").with_exposed_ports(8000) as container:
        yield f"http://localhost:{container.get_exposed_port(8000)}"

class TestMCPIntegration:
    @pytest.mark.integration
    async def test_device_control_flow(self, castplay_server):
        """Test complete device control flow"""
        from device_control_server import (
            list_devices, pause_playback, resume_playback
        )

        # Configure API
        configure_api(castplay_server)

        # List devices
        devices = await list_devices()
        assert devices["success"]

        if devices["count"] > 0:
            device_id = devices["devices"][0]["id"]

            # Control flow
            await pause_playback(device_id)
            await resume_playback(device_id)
```

---

## 9. Skills Testing

Skills (`.claude/skills/`) are documentation/workflow guides, not executable code. They should be tested via:

1. **Documentation validation** - Verify examples match actual API
2. **Workflow execution tests** - Run through skill workflows with mock APIs

Example validation:
```python
# tests/skills/test_skill_documentation.py

class TestDeviceControlSkill:
    def test_example_commands_valid(self):
        """Verify skill examples match actual MCP tool signatures"""
        # From skill.md: "pause" should map to pause_playback(device_id)
        from device_control_server import pause_playback
        import inspect
        sig = inspect.signature(pause_playback)
        assert "device_id" in sig.parameters
```

---

## 10. Summary of Findings

### Critical Issues (Must Fix)

| Issue | Severity | Files Affected | Recommended Action |
|-------|----------|---------------|-------------------|
| Zero MCP unit tests | CRITICAL | All 6 MCP servers | Create `mcp/tests/` with unit tests |
| Zero CLI unit tests | CRITICAL | All CLI modules | Create `cli/tests/` with unit tests |
| Plain text token storage | CRITICAL | `config.py`, `device_control_server.py` | Encrypt tokens at rest |
| No time format validation | HIGH | `schedule_manager_server.py` | Add regex validation |
| Integration test only | HIGH | `test_all_mcp_tools.py` | Convert to mocked unit tests |

### High Priority Test Additions

| Test Category | Estimated Tests | Priority |
|--------------|-----------------|----------|
| MCP Tool Unit Tests | 100+ | CRITICAL |
| CLI Command Unit Tests | 50+ | CRITICAL |
| MCP Security Tests | 20+ | HIGH |
| CLI Security Tests | 15+ | HIGH |
| MCP Performance Tests | 10+ | MEDIUM |
| CLI Integration Tests | 10+ | MEDIUM |

### Recommended Test Structure

```
mcp/
  tests/
    __init__.py
    conftest.py
    test_device_control.py      # ~30 tests
    test_playlist_manager.py    # ~35 tests
    test_schedule_manager.py    # ~25 tests
    test_ppt_converter.py       # ~15 tests
    test_android_tools.py       # ~15 tests
    test_security.py            # ~20 tests
    test_performance.py         # ~10 tests

cli/
  tests/
    __init__.py
    conftest.py
    test_api_client.py          # ~25 tests
    test_config.py              # ~15 tests
    test_devices.py             # ~15 tests
    test_schedules.py           # ~20 tests
    test_control.py             # ~10 tests
    test_security.py            # ~15 tests
```

### Estimated Effort

| Task | Estimated Time |
|------|---------------|
| Create MCP test infrastructure | 4 hours |
| Write MCP unit tests (150 tests) | 16 hours |
| Create CLI test infrastructure | 2 hours |
| Write CLI unit tests (100 tests) | 12 hours |
| Fix token encryption | 2 hours |
| Add input validation | 2 hours |
| **Total** | **38 hours** |

---

## 11. Conclusion

The CastPlay MCP servers and CLI commands have a **critical testing gap**. With ~7,300 lines of production code and zero dedicated unit tests, the system is at high risk for:

1. **Regression bugs** - No safety net for refactoring
2. **Security vulnerabilities** - Unvalidated inputs, plain text secrets
3. **Production failures** - Edge cases not covered

The existing backend test suite (16,180 lines) demonstrates the team understands testing practices. This same rigor must be applied to the MCP and CLI layers immediately.
