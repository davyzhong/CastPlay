"""
Pytest configuration and fixtures for CLI tests.
"""
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def mock_config_manager():
    """Create a mock ConfigManager."""
    manager = MagicMock()
    manager.server_url = "http://localhost:8000"
    manager.token = "test_token"
    manager.timeout = 30
    manager.config_file = Path.home() / ".castplay" / "config.json"
    return manager


@pytest.fixture
def mock_api_client():
    """Create a mock API client."""
    client = MagicMock()
    client.get.return_value = {"items": [], "success": True}
    client.post.return_value = {"success": True, "id": 1}
    client.put.return_value = {"success": True}
    client.delete.return_value = {"success": True}
    client.login.return_value = {"access_token": "test_token", "user": {"username": "test"}}
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
        "items": []
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
        "days_of_week": 31,
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


@pytest.fixture
def mock_keyring():
    """Mock keyring for secure storage tests."""
    with patch('keyring.get_password') as mock_get, \
         patch('keyring.set_password') as mock_set, \
         patch('keyring.delete_password') as mock_delete:
        mock_get.return_value = None
        yield {
            'get': mock_get,
            'set': mock_set,
            'delete': mock_delete
        }
