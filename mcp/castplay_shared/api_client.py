"""
Shared API Client for CastPlay MCP Servers.

This module provides a singleton HTTP client with:
- Connection pooling for better performance
- Context-based configuration (no global mutation)
- Proper error logging
- Secure token handling
"""
import os
import json
import logging
from contextvars import ContextVar
from pathlib import Path
from typing import Optional, ClassVar

import httpx

# Configure logging
logger = logging.getLogger(__name__)

# Context variable for per-request client configuration
_current_client: ContextVar[Optional['CastPlayAPIClient']] = ContextVar('current_client', default=None)


class CastPlayAPIClient:
    """
    Client for CastPlay REST API with connection pooling.

    Uses a singleton httpx.AsyncClient for connection reuse.
    Configuration is managed via context variables to avoid global state mutation.
    """

    # Class-level shared HTTP client for connection pooling
    _http_client: ClassVar[Optional[httpx.AsyncClient]] = None

    def __init__(
        self,
        base_url: Optional[str] = None,
        token: Optional[str] = None,
        timeout: float = 30.0
    ):
        self.base_url = base_url or os.environ.get("CASTPLAY_API_URL", "http://localhost:8000")
        self._token = token or self._load_token()
        self._timeout = timeout

        # Warn if using HTTP for non-localhost
        if self.base_url.startswith("http://") and "localhost" not in self.base_url:
            logger.warning(
                "Using HTTP for non-localhost URL. "
                "Credentials may be transmitted in plaintext."
            )

    def _load_token(self) -> Optional[str]:
        """
        Load token from secure storage (keyring) or fall back to config file.

        Token loading priority:
        1. System keyring (secure storage)
        2. Config file (legacy, will be migrated)
        """
        # First, try secure storage (keyring)
        try:
            import keyring
            token = keyring.get_password("castplay", "api_token")
            if token:
                logger.debug("Token loaded from secure keyring storage")
                return token
        except Exception:
            # keyring not available or no token stored
            pass

        # Fall back to config file (legacy)
        config_path = Path.home() / ".castplay" / "config.json"
        if not config_path.exists():
            return None

        try:
            with open(config_path, encoding="utf-8") as f:
                config = json.load(f)
                legacy_token = config.get("token")
                if legacy_token:
                    # Migrate to secure storage
                    self._migrate_token_to_keyring(legacy_token, config_path, config)
                    return legacy_token
        except json.JSONDecodeError as e:
            logger.warning(f"Invalid JSON in config file {config_path}: {e}")
        except IOError as e:
            logger.warning(f"Failed to read config file {config_path}: {e}")

        return None

    def _migrate_token_to_keyring(self, token: str, config_path: Path, config: dict) -> bool:
        """
        Migrate plain-text token to secure keyring storage.

        Args:
            token: The token to migrate
            config_path: Path to the config file
            config: Current config dict

        Returns:
            True if migration successful, False otherwise
        """
        try:
            import keyring
            keyring.set_password("castplay", "api_token", token)
            logger.info("Migrated token from config file to secure keyring storage")

            # Remove token from config file
            config.pop("token", None)
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2)
            logger.info("Removed plain-text token from config file")
            return True
        except Exception as e:
            logger.warning(f"Could not migrate token to keyring: {e}")
            return False

    def _get_headers(self) -> dict:
        """Get request headers with auth and security headers."""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "CastPlay-MCP/1.0",
        }
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        return headers

    @classmethod
    async def _get_http_client(cls) -> httpx.AsyncClient:
        """
        Get or create the shared HTTP client with connection pooling.

        This implements connection pooling to avoid creating a new client
        for every request, which improves performance significantly.
        """
        if cls._http_client is None:
            cls._http_client = httpx.AsyncClient(
                timeout=30.0,
                limits=httpx.Limits(
                    max_connections=100,
                    max_keepalive_connections=20,
                    keepalive_expiry=30.0
                ),
                http2=False,  # Disable HTTP/2 (requires h2 package)
                verify=True,  # Explicit TLS verification
            )
        return cls._http_client

    @classmethod
    async def close_http_client(cls):
        """Close the shared HTTP client. Call during shutdown."""
        if cls._http_client is not None:
            await cls._http_client.aclose()
            cls._http_client = None

    async def get(self, path: str, params: Optional[dict] = None) -> dict:
        """Make GET request with connection pooling."""
        client = await self._get_http_client()
        url = f"{self.base_url}{path}"

        logger.debug(f"GET {url}")
        resp = await client.get(url, params=params, headers=self._get_headers())
        resp.raise_for_status()

        if resp.status_code == 204:
            return {"success": True}
        return resp.json()

    async def post(self, path: str, json_data: Optional[dict] = None) -> dict:
        """Make POST request with connection pooling."""
        client = await self._get_http_client()
        url = f"{self.base_url}{path}"

        logger.debug(f"POST {url}")
        resp = await client.post(url, json=json_data, headers=self._get_headers())
        resp.raise_for_status()

        if resp.status_code == 204:
            return {"success": True}
        return resp.json()

    async def put(self, path: str, json_data: Optional[dict] = None) -> dict:
        """Make PUT request with connection pooling."""
        client = await self._get_http_client()
        url = f"{self.base_url}{path}"

        logger.debug(f"PUT {url}")
        resp = await client.put(url, json=json_data, headers=self._get_headers())
        resp.raise_for_status()

        if resp.status_code == 204:
            return {"success": True}
        return resp.json()

    async def delete(self, path: str) -> dict:
        """Make DELETE request with connection pooling."""
        client = await self._get_http_client()
        url = f"{self.base_url}{path}"

        logger.debug(f"DELETE {url}")
        resp = await client.delete(url, headers=self._get_headers())
        resp.raise_for_status()

        if resp.status_code == 204:
            return {"success": True}
        return resp.json()


def get_client() -> CastPlayAPIClient:
    """
    Get the current API client from context, or create a default one.

    This function provides dependency injection without global state mutation.
    Each context (request) can have its own configured client.
    """
    client = _current_client.get()
    if client is None:
        return CastPlayAPIClient()
    return client


def configure_client(base_url: str, token: Optional[str] = None) -> CastPlayAPIClient:
    """
    Configure a new API client for the current context.

    This sets the client in a context variable rather than mutating global state,
    preventing race conditions in concurrent execution.

    Args:
        base_url: Base URL of the CastPlay API server
        token: Optional authentication token

    Returns:
        The newly configured client
    """
    client = CastPlayAPIClient(base_url=base_url, token=token)
    _current_client.set(client)
    logger.info(f"API client configured for {base_url}")
    return client
