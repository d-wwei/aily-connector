"""
Auto-load credentials from ~/.aily_connector/credentials.env.

Format (no 'export', pure KEY=VALUE):
    AILY_CONNECTOR_CSRF=...
    AILY_CONNECTOR_COOKIE=...

Usage:
    import load_env
    # os.environ['AILY_CONNECTOR_CSRF'] is now available
"""

import os

CREDENTIALS_FILE = os.path.expanduser("~/.aily_connector/credentials.env")


def load():
    """Read credentials.env into os.environ (won't overwrite existing values)."""
    if not os.path.isfile(CREDENTIALS_FILE):
        return False

    with open(CREDENTIALS_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '=' not in line:
                continue
            key, _, value = line.partition('=')
            key = key.strip()
            value = value.strip()
            if key not in os.environ:
                os.environ[key] = value

    return True


# Auto-load on import
_loaded = load()
