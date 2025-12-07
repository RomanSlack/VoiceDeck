"""Secure API key storage using system keyring."""

import logging

SERVICE_NAME = "voicedeck"
KEY_NAME = "openai_api_key"

_keyring_available = None


def is_keyring_available() -> bool:
    """Check if system keyring is available."""
    global _keyring_available
    if _keyring_available is not None:
        return _keyring_available

    try:
        import keyring
        from keyring.backends import fail

        # Check if we have a working backend (not the fail backend)
        backend = keyring.get_keyring()
        _keyring_available = not isinstance(backend, fail.Keyring)
    except ImportError:
        _keyring_available = False
    except Exception:
        _keyring_available = False

    return _keyring_available


def get_api_key() -> str | None:
    """
    Retrieve the API key from the system keyring.

    Returns:
        The API key if found, None otherwise.
    """
    if not is_keyring_available():
        return None

    try:
        import keyring
        return keyring.get_password(SERVICE_NAME, KEY_NAME)
    except Exception as e:
        logging.debug(f"Failed to get API key from keyring: {e}")
        return None


def set_api_key(api_key: str) -> bool:
    """
    Store the API key in the system keyring.

    Args:
        api_key: The API key to store.

    Returns:
        True if successful, False otherwise.
    """
    if not is_keyring_available():
        return False

    try:
        import keyring
        keyring.set_password(SERVICE_NAME, KEY_NAME, api_key)
        return True
    except Exception as e:
        logging.debug(f"Failed to store API key in keyring: {e}")
        return False


def delete_api_key() -> bool:
    """
    Delete the API key from the system keyring.

    Returns:
        True if successful, False otherwise.
    """
    if not is_keyring_available():
        return False

    try:
        import keyring
        keyring.delete_password(SERVICE_NAME, KEY_NAME)
        return True
    except keyring.errors.PasswordDeleteError:
        # Key doesn't exist, that's fine
        return True
    except Exception as e:
        logging.debug(f"Failed to delete API key from keyring: {e}")
        return False
