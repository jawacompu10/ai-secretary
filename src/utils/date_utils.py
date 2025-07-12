"""
Date parsing and validation utilities.

Provider-agnostic date handling utilities that can be used by any
calendar provider implementation (CalDAV, Google Calendar, Microsoft Graph, etc.).
"""

from datetime import datetime, date


def parse_due_date(due_date_str: str | None) -> date | None:
    """Parse due date string to date object.
    
    Args:
        due_date_str (str | None): Due date in ISO format (YYYY-MM-DD) or None
        
    Returns:
        date | None: Parsed date object or None
        
    Raises:
        ValueError: If date format is invalid
    """
    if not due_date_str:
        return None
    
    try:
        return datetime.fromisoformat(due_date_str).date()
    except ValueError:
        raise ValueError(f"Invalid due date format: {due_date_str}. Expected YYYY-MM-DD")


def parse_date_range(start_date: str, end_date: str) -> tuple[datetime, datetime]:
    """Parse start and end date strings for date range queries.
    
    Args:
        start_date (str): Start date in ISO format
        end_date (str): End date in ISO format
        
    Returns:
        tuple[datetime, datetime]: Parsed start and end datetime objects
        
    Raises:
        ValueError: If date formats are invalid
    """
    try:
        start_dt = datetime.fromisoformat(start_date)
        end_dt = datetime.fromisoformat(end_date)
        return start_dt, end_dt
    except ValueError:
        raise ValueError(f"Invalid date format. Expected YYYY-MM-DD")


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