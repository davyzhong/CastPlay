"""
Error handling utilities for CastPlay MCP servers.

Provides consistent error handling across all MCP tools.
"""
import logging
from functools import wraps
from typing import Callable, Any

import httpx

logger = logging.getLogger(__name__)


class APIError(Exception):
    """Custom exception for API errors with user-friendly messages."""

    # Map HTTP status codes to user-friendly messages
    ERROR_MESSAGES = {
        400: "Invalid request parameters",
        401: "Authentication required",
        403: "Access denied",
        404: "Resource not found",
        405: "Operation not allowed",
        409: "Resource already exists",
        422: "Validation error",
        429: "Too many requests",
        500: "Server error",
        502: "Server unavailable",
        503: "Service temporarily unavailable",
    }

    def __init__(self, status_code: int, detail: str = None, original_error: Exception = None):
        self.status_code = status_code
        self.detail = detail
        self.original_error = original_error
        self.message = self._get_user_message()
        super().__init__(self.message)

    def _get_user_message(self) -> str:
        """Get a user-friendly error message."""
        base_message = self.ERROR_MESSAGES.get(self.status_code, "Request failed")
        if self.detail:
            return f"{base_message}: {self.detail}"
        return base_message


def handle_api_errors(func: Callable) -> Callable:
    """
    Decorator for consistent API error handling in MCP tools.

    Catches HTTP errors and exceptions, logs them appropriately,
    and returns a consistent error response format.

    Usage:
        @mcp.tool()
        @handle_api_errors
        async def my_tool(device_id: int) -> dict:
            client = get_client()
            result = await client.get(f"/api/devices/{device_id}")
            return {"success": True, "data": result}
    """
    @wraps(func)
    async def wrapper(*args, **kwargs) -> dict:
        try:
            return await func(*args, **kwargs)

        except httpx.HTTPStatusError as e:
            # Log detailed error for debugging
            logger.error(
                f"API error in {func.__name__}: "
                f"{e.response.status_code} - {e.response.text}"
            )

            # Return sanitized error to user
            status_code = e.response.status_code
            user_message = APIError.ERROR_MESSAGES.get(status_code, "Request failed")

            # Special handling for common cases
            if status_code == 404:
                return {"success": False, "error": "Resource not found"}
            if status_code == 405:
                return {"success": False, "error": "Operation not allowed by API"}

            return {"success": False, "error": f"API error: {status_code}"}

        except httpx.TimeoutException:
            logger.error(f"Timeout in {func.__name__}")
            return {"success": False, "error": "Request timed out"}

        except httpx.NetworkError as e:
            logger.error(f"Network error in {func.__name__}: {e}")
            return {"success": False, "error": "Network error - server unreachable"}

        except ValueError as e:
            logger.warning(f"Validation error in {func.__name__}: {e}")
            return {"success": False, "error": str(e)}

        except Exception as e:
            logger.exception(f"Unexpected error in {func.__name__}: {e}")
            return {"success": False, "error": f"Internal error: {type(e).__name__}"}

    return wrapper


def sanitize_error_message(error: Exception) -> str:
    """
    Sanitize error messages for external exposure.

    Removes potentially sensitive information like URLs, tokens, etc.
    """
    message = str(error)

    # Redact Bearer tokens
    import re
    message = re.sub(r'Bearer [A-Za-z0-9\-._~+/]+=*', 'Bearer [REDACTED]', message)

    # Redact tokens in JSON
    message = re.sub(r'"token":\s*"[^"]*"', '"token": "[REDACTED]"', message)

    return message
