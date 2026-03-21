"""
Unit tests for the shared API client module.
"""
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from castplay_shared.api_client import (
    CastPlayAPIClient,
    get_client,
    configure_client,
    _current_client
)


class TestCastPlayAPIClient:
    """Tests for CastPlayAPIClient class."""

    def test_init_default_values(self):
        """Test client initialization with default values."""
        client = CastPlayAPIClient()
        assert client.base_url == "http://localhost:8000"
        assert client._timeout == 30.0

    def test_init_custom_values(self):
        """Test client initialization with custom values."""
        client = CastPlayAPIClient(
            base_url="https://api.example.com",
            token="test_token",
            timeout=60.0
        )
        assert client.base_url == "https://api.example.com"
        assert client._token == "test_token"
        assert client._timeout == 60.0

    def test_init_from_env(self, monkeypatch):
        """Test client initialization from environment variable."""
        monkeypatch.setenv("CASTPLAY_API_URL", "https://env.example.com")
        client = CastPlayAPIClient()
        assert client.base_url == "https://env.example.com"

    def test_get_headers_with_token(self):
        """Test headers generation with token."""
        client = CastPlayAPIClient(token="secret_token")
        headers = client._get_headers()
        assert headers["Authorization"] == "Bearer secret_token"
        assert headers["Content-Type"] == "application/json"

    def test_get_headers_without_token(self):
        """Test headers generation without token."""
        with patch('keyring.get_password', return_value=None):
            with patch('castplay_shared.api_client.Path.exists', return_value=False):
                client = CastPlayAPIClient()
                headers = client._get_headers()
                assert "Authorization" not in headers
                assert headers["Content-Type"] == "application/json"

    def test_http_warning_for_non_localhost(self, caplog):
        """Test warning is logged for HTTP with non-localhost URL."""
        with caplog.at_level("WARNING"):
            client = CastPlayAPIClient(base_url="http://api.example.com")
        assert "HTTP for non-localhost" in caplog.text

    def test_no_warning_for_https(self, caplog):
        """Test no warning for HTTPS URL."""
        with caplog.at_level("WARNING"):
            client = CastPlayAPIClient(base_url="https://api.example.com")
        assert "HTTP for non-localhost" not in caplog.text

    def test_no_warning_for_localhost(self, caplog):
        """Test no warning for localhost HTTP URL."""
        with caplog.at_level("WARNING"):
            client = CastPlayAPIClient(base_url="http://localhost:8000")
        assert "HTTP for non-localhost" not in caplog.text

    @pytest.mark.asyncio
    async def test_get_request(self, mock_httpx_response):
        """Test GET request."""
        client = CastPlayAPIClient()

        with patch.object(client, '_get_http_client') as mock_get_client:
            mock_http = AsyncMock()
            mock_http.get.return_value = mock_httpx_response({"data": "test"})
            mock_get_client.return_value = mock_http

            result = await client.get("/api/test")
            assert result["data"] == "test"

    @pytest.mark.asyncio
    async def test_post_request(self, mock_httpx_response):
        """Test POST request."""
        client = CastPlayAPIClient()

        with patch.object(client, '_get_http_client') as mock_get_client:
            mock_http = AsyncMock()
            mock_http.post.return_value = mock_httpx_response({"id": 1})
            mock_get_client.return_value = mock_http

            result = await client.post("/api/test", json_data={"name": "test"})
            assert result["id"] == 1

    @pytest.mark.asyncio
    async def test_204_response(self, mock_httpx_response):
        """Test handling of 204 No Content response."""
        client = CastPlayAPIClient()

        with patch.object(client, '_get_http_client') as mock_get_client:
            mock_response = MagicMock()
            mock_response.status_code = 204
            mock_response.raise_for_status = MagicMock()

            mock_http = AsyncMock()
            mock_http.delete.return_value = mock_response
            mock_get_client.return_value = mock_http

            result = await client.delete("/api/test/1")
            assert result == {"success": True}


class TestParseFrameRate:
    """Tests for frame rate parsing (from file_processor)."""

    @pytest.fixture(autouse=True)
    def setup_path(self):
        """Add file-processor to path for imports."""
        file_processor_path = Path(__file__).parent.parent / "file-processor"
        if str(file_processor_path) not in sys.path:
            sys.path.insert(0, str(file_processor_path))
        yield
        # Cleanup is optional - leave path for other tests

    def test_parse_simple_fraction(self):
        """Test parsing simple fraction like 30/1."""
        from file_processor_server import _parse_frame_rate
        assert _parse_frame_rate("30/1") == 30.0

    def test_parse_complex_fraction(self):
        """Test parsing complex fraction like 30000/1001."""
        from file_processor_server import _parse_frame_rate
        result = _parse_frame_rate("30000/1001")
        assert abs(result - 29.97) < 0.01

    def test_parse_decimal(self):
        """Test parsing decimal like 29.97."""
        from file_processor_server import _parse_frame_rate
        assert _parse_frame_rate("29.97") == 29.97

    def test_parse_empty_string(self):
        """Test parsing empty string returns 0.0."""
        from file_processor_server import _parse_frame_rate
        assert _parse_frame_rate("") == 0.0

    def test_parse_invalid(self):
        """Test parsing invalid string returns 0.0."""
        from file_processor_server import _parse_frame_rate
        assert _parse_frame_rate("invalid") == 0.0

    def test_parse_division_by_zero(self):
        """Test parsing with division by zero returns 0.0."""
        from file_processor_server import _parse_frame_rate
        assert _parse_frame_rate("10/0") == 0.0


class TestContextFunctions:
    """Tests for context-based client functions."""

    def test_get_client_default(self):
        """Test get_client returns a default client."""
        _current_client.set(None)
        client = get_client()
        assert isinstance(client, CastPlayAPIClient)

    def test_configure_client(self):
        """Test configure_client sets context client."""
        client = configure_client("https://test.example.com", "test_token")
        assert client.base_url == "https://test.example.com"
        assert client._token == "test_token"

        # Verify it's in context
        context_client = get_client()
        assert context_client.base_url == "https://test.example.com"
