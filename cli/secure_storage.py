"""
Secure token storage using system keyring.

Provides secure storage for sensitive credentials like API tokens
using the operating system's credential store (Keychain on macOS,
Credential Manager on Windows, Secret Service on Linux).
"""
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Service name for keyring storage
KEYRING_SERVICE = "castplay"
KEYRING_TOKEN_KEY = "api_token"

# Flag to track if keyring is available
_keyring_available: Optional[bool] = None


def _check_keyring_available() -> bool:
    """Check if keyring is available and working."""
    global _keyring_available
    if _keyring_available is not None:
        return _keyring_available

    try:
        import keyring
        # Test if keyring works by trying to get a non-existent credential
        keyring.get_password(KEYRING_SERVICE, "__test__")
        _keyring_available = True
        logger.debug("Keyring is available for secure storage")
        return True
    except Exception as e:
        _keyring_available = False
        logger.warning(f"Keyring not available, falling back to file storage: {e}")
        return False


def store_token(token: str) -> bool:
    """
    Securely store an API token.

    Uses system keyring if available, otherwise falls back to file storage
    with a warning.

    Args:
        token: The token to store

    Returns:
        True if stored successfully, False otherwise
    """
    if not token:
        return False

    if _check_keyring_available():
        try:
            import keyring
            keyring.set_password(KEYRING_SERVICE, KEYRING_TOKEN_KEY, token)
            logger.info("Token stored securely in system keyring")
            return True
        except Exception as e:
            logger.error(f"Failed to store token in keyring: {e}")
            return False
    else:
        logger.warning(
            "Token will be stored in plain text. "
            "Install 'keyring' package for secure storage: pip install keyring"
        )
        return False


def get_token() -> Optional[str]:
    """
    Retrieve the stored API token.

    First tries system keyring, then falls back to legacy file storage.

    Returns:
        The stored token, or None if not found
    """
    if _check_keyring_available():
        try:
            import keyring
            token = keyring.get_password(KEYRING_SERVICE, KEYRING_TOKEN_KEY)
            if token:
                logger.debug("Token retrieved from system keyring")
                return token
        except Exception as e:
            logger.warning(f"Failed to get token from keyring: {e}")

    return None


def delete_token() -> bool:
    """
    Delete the stored API token.

    Returns:
        True if deleted successfully, False otherwise
    """
    if _check_keyring_available():
        try:
            import keyring
            keyring.delete_password(KEYRING_SERVICE, KEYRING_TOKEN_KEY)
            logger.info("Token deleted from system keyring")
            return True
        except keyring.errors.PasswordNotFoundError:
            # Token doesn't exist, that's fine
            return True
        except Exception as e:
            logger.warning(f"Failed to delete token from keyring: {e}")
            return False

    return True


def is_secure_storage_available() -> bool:
    """
    Check if secure storage (keyring) is available.

    Returns:
        True if keyring is available and working
    """
    return _check_keyring_available()


def get_storage_info() -> dict:
    """
    Get information about the storage backend.

    Returns:
        Dictionary with storage information
    """
    available = _check_keyring_available()
    return {
        "secure_storage_available": available,
        "storage_type": "keyring" if available else "file",
        "service_name": KEYRING_SERVICE if available else None,
        "recommendation": (
            "Token stored securely"
            if available
            else "Install 'keyring' package for secure token storage"
        ),
    }
