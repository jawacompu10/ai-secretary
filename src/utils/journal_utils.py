"""
Journal-specific utility functions.

Provider-agnostic journal business logic that can be used by any
journal provider implementation (CalDAV, Google Calendar, Microsoft Graph, etc.).
"""

from datetime import datetime
from .timezone_utils import get_user_timezone


def build_updated_description(
    current_description: str, new_content: str, append: bool = True
) -> str:
    """Build updated description content with optional append mode and timestamp.

    Args:
        current_description (str): Existing description content (can be empty)
        new_content (str): New content to add or replace with
        append (bool): If True, append with timestamp. If False, replace entirely.

    Returns:
        str: Updated description content

    When appending to existing content, adds a timestamp separator in the format:
    ```
    Original content here...

    --- [2025-07-12 15:30] ---
    New content appended here...
    ```

    When replacing (append=False), simply returns the new_content.
    This preserves chronological history when appending, or allows clean
    replacement for corrections and major rewrites.
    """
    if append and current_description:
        # Add timestamp separator and append new content
        user_tz = get_user_timezone()
        timestamp = datetime.now(user_tz).strftime("%Y-%m-%d %H:%M")

        return f"{current_description}\n\n--- [{timestamp}] ---\n{new_content}"
    else:
        # Replace existing description entirely (or set initial description)
        return new_content
