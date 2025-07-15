"""
Date parsing and validation utilities.

Provider-agnostic date handling utilities that can be used by any
calendar provider implementation (CalDAV, Google Calendar, Microsoft Graph, etc.).
"""

from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo


def parse_due_date(due_date_str: str | None) -> date | None:
    """Parse due date string to date object.

    Args:
        due_date_str (str | None): Due date in ISO format (YYYY-MM-DD) or None

    Returns:
        date | None: Parsed date object or None

    Raises:
        ValueError: If date format is invalid
    """
    if not due_date_str or not due_date_str.strip():
        return None

    try:
        return datetime.fromisoformat(due_date_str).date()
    except ValueError:
        raise ValueError(
            f"Invalid due date format: {due_date_str}. Expected YYYY-MM-DD"
        )


def parse_date_range(start_date: str, end_date: str) -> tuple[datetime, datetime]:
    """Parse start and end date strings for date range queries.

    Args:
        start_date (str): Start date in ISO format
        end_date (str): End date in ISO format

    Returns:
        tuple[datetime, datetime]: Parsed start and end datetime objects

    Raises:
        ValueError: If date formats are invalid or end date is before start date
    """
    try:
        start_dt = datetime.fromisoformat(start_date)
        end_dt = datetime.fromisoformat(end_date)

        # Validate that end date is not before start date
        if end_dt < start_dt:
            raise ValueError(
                f"End date ({end_date}) cannot be before start date ({start_date})"
            )

        return start_dt, end_dt
    except ValueError as e:
        # Re-raise ValueError with original message if it's our validation error
        if "cannot be before" in str(e):
            raise e
        # Otherwise, it's a date format error
        raise ValueError("Invalid date format. Expected YYYY-MM-DD")


def parse_instance_date(instance_date: str) -> datetime:
    """Parse instance date string for recurring event operations.

    Args:
        instance_date (str): Instance date in ISO format

    Returns:
        datetime: Parsed datetime object

    Raises:
        ValueError: If date format is invalid
    """
    try:
        return datetime.fromisoformat(instance_date)
    except ValueError:
        raise ValueError(f"Invalid date format: {instance_date}. Expected YYYY-MM-DD")


def validate_date_string(date_str: str) -> bool:
    """Validate that date string is in correct ISO format.

    Args:
        date_str (str): Date string to validate

    Returns:
        bool: True if valid date format
    """
    try:
        datetime.fromisoformat(date_str)
        return True
    except ValueError:
        return False


def calculate_past_days_range(days: int) -> tuple[date, date]:
    """Calculate date range for the past X days including today.
    
    Args:
        days (int): Number of days to go back (must be positive)
        
    Returns:
        tuple[date, date]: (start_date, end_date) where:
            - start_date: X days ago from today
            - end_date: today
            
    Raises:
        ValueError: If days is not a positive integer
        
    Examples:
        # Past 7 days (including today)
        start_date, end_date = calculate_past_days_range(7)
        # If today is 2025-07-15, returns (2025-07-09, 2025-07-15)
        
        # Past 1 day (today only)
        start_date, end_date = calculate_past_days_range(1)
        # If today is 2025-07-15, returns (2025-07-15, 2025-07-15)
    """
    if not isinstance(days, int) or days < 1:
        raise ValueError(f"Days must be a positive integer, got: {days}")
    
    # Get today's date in UTC
    today = datetime.now(ZoneInfo("UTC")).date()
    
    # Calculate start date (X days ago)
    start_date = today - timedelta(days=days - 1)  # -1 because we include today
    
    return start_date, today
