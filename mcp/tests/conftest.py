"""
Pytest configuration and fixtures for MCP server tests.
"""
import asyncio
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_httpx_response():
    """Create a mock httpx response."""
    def _create_response(data, status_code=200):
        response = MagicMock()
        response.status_code = status_code
        response.json.return_value = data
        response.raise_for_status = MagicMock()
        return response
    return _create_response


@pytest.fixture
def mock_api_client(mock_httpx_response):
    """Create a mock API client."""
    client = MagicMock()

    async def mock_get(path, params=None):
        return {"items": [], "success": True}

    async def mock_post(path, json_data=None):
        return {"success": True, "id": 1}

    async def mock_put(path, json_data=None):
        return {"success": True}

    async def mock_delete(path):
        return {"success": True}

    client.get = AsyncMock(side_effect=mock_get)
    client.post = AsyncMock(side_effect=mock_post)
    client.put = AsyncMock(side_effect=mock_put)
    client.delete = AsyncMock(side_effect=mock_delete)

    return client


@pytest.fixture
def sample_device():
    """Sample device data."""
    return {
        "id": 1,
        "name": "Test Device",
        "is_online": True,
        "is_enabled": True,
        "last_seen": "2024-01-15T10:30:00Z",
        "registration_code": "ABC123"
    }


@pytest.fixture
def sample_playlist():
    """Sample playlist data."""
    return {
        "id": 1,
        "name": "Test Playlist",
        "description": "A test playlist",
        "is_active": True,
        "items": [
            {"id": 1, "media_id": 1, "duration": 10, "order": 0}
        ]
    }


@pytest.fixture
def sample_schedule():
    """Sample schedule data."""
    return {
        "id": 1,
        "device_id": 1,
        "playlist_id": 1,
        "start_time": "08:00:00",
        "end_time": "18:00:00",
        "days_of_week": 31,  # Mon-Fri
        "enabled": True,
        "priority": 0
    }


@pytest.fixture
def sample_media():
    """Sample media data."""
    return {
        "id": 1,
        "filename": "test_image.jpg",
        "type": "image",
        "url": "/media/test_image.jpg",
        "duration": 10
    }
