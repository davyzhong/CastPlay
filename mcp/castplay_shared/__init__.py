"""
Shared modules for CastPlay MCP servers.
"""
from .api_client import CastPlayAPIClient, get_client, configure_client
from .error_handling import handle_api_errors, APIError

__all__ = [
    "CastPlayAPIClient",
    "get_client",
    "configure_client",
    "handle_api_errors",
    "APIError",
]
