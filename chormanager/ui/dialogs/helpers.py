"""Helper functions for dialogs."""

import re


def sanitize_filename(name: str, max_length: int = 100) -> str:
    """Sanitize a string for use in filenames.

    Args:
        name: Input string to sanitize.
        max_length: Maximum length of output.

    Returns:
        Safe filename string.
    """
    safe = re.sub(r'[^\w\-]', '_', name)
    return safe[:max_length]
