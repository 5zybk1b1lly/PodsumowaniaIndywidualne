"""Utilities for storing/loading saved SMTP/IMAP login credentials."""

import json
import os
from pathlib import Path

_CREDENTIALS_FILE_NAME = ".salesup_credentials.json"


def _get_credentials_path() -> str:
    """Return the path where credentials are stored."""
    home = Path.home()
    return str(home / _CREDENTIALS_FILE_NAME)


def load_credentials() -> dict:
    """Load saved credentials from disk.

    Returns:
        dict: Saved credentials, or empty dict if none or file is invalid.
    """
    path = _get_credentials_path()
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if not isinstance(data, dict):
                return {}
            return data
    except Exception:
        return {}


def save_credentials(credentials: dict) -> None:
    """Save credentials to disk.

    Args:
        credentials: Dict containing login information.
    """
    path = _get_credentials_path()
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(credentials, f, indent=2, ensure_ascii=False)
    except Exception:
        # Ignore write errors; do not break app.
        pass


def delete_credentials() -> None:
    """Delete stored credentials file."""
    path = _get_credentials_path()
    try:
        os.remove(path)
    except Exception:
        pass
