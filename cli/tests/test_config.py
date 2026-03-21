"""
Unit tests for CLI configuration management.
"""
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import ConfigManager, CLIConfig


class TestCLIConfig:
    """Tests for CLIConfig model."""

    def test_default_values(self):
        """Test default configuration values."""
        config = CLIConfig()
        assert config.server_url == "http://localhost:8000"
        assert config.timeout == 30

    def test_custom_values(self):
        """Test custom configuration values."""
        config = CLIConfig(
            server_url="https://api.example.com",
            timeout=60
        )
        assert config.server_url == "https://api.example.com"
        assert config.timeout == 60

    def test_extra_ignore(self):
        """Test that extra fields are ignored."""
        config = CLIConfig(**{"server_url": "http://test.com", "unknown_field": "value"})
        assert config.server_url == "http://test.com"


class TestConfigManager:
    """Tests for ConfigManager class."""

    def test_default_config(self, tmp_path, monkeypatch):
        """Test default config when no file exists."""
        # Use temp directory for config
        monkeypatch.setattr(
            Path, "home",
            tmp_path
        )

        manager = ConfigManager()
        assert manager.server_url == "http://localhost:8000"
        assert manager.timeout == 30

    def test_set_server(self, tmp_path, monkeypatch):
        """Test setting server URL."""
        monkeypatch.setattr(Path, "home", tmp_path)

        manager = ConfigManager()
        manager.set_server("https://new.example.com")

        assert manager.server_url == "https://new.example.com"

    def test_set_timeout(self, tmp_path, monkeypatch):
        """Test setting timeout."""
        monkeypatch.setattr(Path, "home", tmp_path)

        manager = ConfigManager()
        manager.set_timeout(60)

        assert manager.timeout == 60

    def test_get_config_path(self, tmp_path, monkeypatch):
        """Test getting config file path."""
        monkeypatch.setattr(Path, "home", tmp_path)

        manager = ConfigManager()
        path = manager.get_config_path()

        assert path == tmp_path / ".castplay" / "config.json"

    def test_storage_info(self, tmp_path, monkeypatch):
        """Test getting storage info."""
        monkeypatch.setattr(Path, "home", tmp_path)

        manager = ConfigManager()
        info = manager.get_storage_info()

        assert "secure_storage_available" in info
        assert "storage_type" in info


class TestSecureStorage:
    """Tests for secure storage module."""

    def test_is_secure_storage_available(self):
        """Test checking if secure storage is available."""
        from secure_storage import is_secure_storage_available

        # Should return a boolean
        result = is_secure_storage_available()
        assert isinstance(result, bool)

    def test_get_storage_info(self):
        """Test getting storage info."""
        from secure_storage import get_storage_info

        info = get_storage_info()

        assert "secure_storage_available" in info
        assert "storage_type" in info
        assert "recommendation" in info

    def test_store_and_get_token_with_keyring(self, mock_keyring):
        """Test storing and retrieving token with keyring."""
        from secure_storage import store_token, get_token

        # Store token
        result = store_token("test_token_123")
        assert result is True

        # Mock the get to return our token
        mock_keyring['get'].return_value = "test_token_123"

        # Retrieve token
        token = get_token()
        assert token == "test_token_123"

    def test_delete_token(self, mock_keyring):
        """Test deleting token."""
        from secure_storage import delete_token

        result = delete_token()
        assert result is True


class TestWeekdayBitmask:
    """Tests for weekday bitmask conversion."""

    def test_weekdays_to_bitmask_weekdays(self):
        """Test converting weekdays to bitmask."""
        # Monday-Friday (0-4) = 31
        weekdays = [0, 1, 2, 3, 4]
        bitmask = 0
        for day in weekdays:
            bitmask |= (1 << day)
        assert bitmask == 31

        # Weekend (5-6) = 96
        weekdays = [5, 6]
        bitmask = 0
        for day in weekdays:
            bitmask |= (1 << day)
        assert bitmask == 96

        # All days = 127
        weekdays = [0, 1, 2, 3, 4, 5, 6]
        bitmask = 0
        for day in weekdays:
            bitmask |= (1 << day)
        assert bitmask == 127

    def test_bitmask_to_weekdays(self):
        """Test converting bitmask to weekdays."""
        # 31 = Mon-Fri
        bitmask = 31
        weekdays = []
        for i in range(7):
            if bitmask & (1 << i):
                weekdays.append(i)
        assert weekdays == [0, 1, 2, 3, 4]

        # 96 = Sat-Sun
        bitmask = 96
        weekdays = []
        for i in range(7):
            if bitmask & (1 << i):
                weekdays.append(i)
        assert weekdays == [5, 6]
