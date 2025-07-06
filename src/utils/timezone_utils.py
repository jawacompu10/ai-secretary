"""
Timezone utility functions for handling datetime conversions.

This module provides utilities for:
- Parsing timezone-aware datetime strings
- Converting to UTC for storage
- Converting from UTC to user timezone for display
"""

from datetime import datetime
from zoneinfo import ZoneInfo
import os


def get_user_timezone() -> ZoneInfo:
    """Get the user's local timezone.
    
    Returns:
        ZoneInfo: User's local timezone, defaults to UTC if not determinable
    """
    try:
        # Try to get system timezone
        return ZoneInfo(str(datetime.now().astimezone().tzinfo))
    except:
        try:
            # Fallback to TZ environment variable
            tz_name = os.environ.get('TZ', 'UTC')
            return ZoneInfo(tz_name)
        except:
            # Final fallback to UTC
            return ZoneInfo('UTC')


def parse_datetime_to_utc(datetime_str: str) -> datetime:
    """Parse timezone-aware datetime string and convert to UTC.
    
    Args:
        datetime_str (str): Datetime string in ISO format with timezone
                           Examples: "2025-07-08T14:00:00+00:00", "2025-07-08T09:00:00-05:00", "2025-07-08T14:00:00Z"
    
    Returns:
        datetime: UTC datetime object
        
    Raises:
        ValueError: If datetime format is invalid or timezone is missing
    """
    try:
        # Handle Z suffix (UTC)
        if datetime_str.endswith('Z'):
            datetime_str = datetime_str[:-1] + '+00:00'
        
        # Parse timezone-aware datetime
        dt = datetime.fromisoformat(datetime_str)
        
        # Ensure it's timezone-aware
        if dt.tzinfo is None:
            raise ValueError("Datetime must include timezone information")
        
        # Convert to UTC
        return dt.astimezone(ZoneInfo('UTC'))
        
    except ValueError as e:
        if "timezone" in str(e).lower():
            raise e
        raise ValueError(f"Invalid datetime format: {datetime_str}. Expected format: YYYY-MM-DDTHH:MM:SS+TZ (e.g., '2025-07-08T14:00:00+00:00' or '2025-07-08T14:00:00Z')")


def utc_to_user_timezone(utc_dt: datetime) -> datetime:
    """Convert UTC datetime to user's local timezone.
    
    Args:
        utc_dt (datetime): UTC datetime object
        
    Returns:
        datetime: Datetime in user's local timezone
    """
    if utc_dt.tzinfo is None:
        # Assume it's UTC if no timezone info
        utc_dt = utc_dt.replace(tzinfo=ZoneInfo('UTC'))
    
    user_tz = get_user_timezone()
    return utc_dt.astimezone(user_tz)


def format_datetime_for_user(utc_dt: datetime | None) -> str | None:
    """Format UTC datetime for display to user in their timezone.
    
    Args:
        utc_dt (datetime | None): UTC datetime object or None
        
    Returns:
        str | None: Formatted datetime string in user timezone, or None
    """
    if utc_dt is None:
        return None
    
    user_dt = utc_to_user_timezone(utc_dt)
    return user_dt.isoformat()


def validate_datetime_string(datetime_str: str) -> bool:
    """Validate that datetime string is timezone-aware and parseable.
    
    Args:
        datetime_str (str): Datetime string to validate
        
    Returns:
        bool: True if valid timezone-aware datetime
    """
    try:
        parse_datetime_to_utc(datetime_str)
        return True
    except ValueError:
        return False