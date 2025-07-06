"""
Calendar Management MCP Server

This server provides tools for managing calendars themselves - creating, listing,
organizing, and administering calendars across multiple roles and contexts.
Focused on calendar lifecycle and organization, not the items within calendars.
"""

import sys
from pathlib import Path

# Add project root to Python path when running directly
if __name__ == "__main__":
    root_dir = Path(__file__).parent.parent.parent
    if str(root_dir) not in sys.path:
        sys.path.insert(0, str(root_dir))

from mcp.server.fastmcp import FastMCP
from datetime import datetime, timezone

from src.providers.base import CalendarProvider
from src.providers.caldav import create_calendar_provider
from src.utils.timezone_utils import get_user_timezone

# Initialize the calendar provider
calendar_provider: CalendarProvider = create_calendar_provider()
calendar_mcp = FastMCP("Calendar Management")


@calendar_mcp.tool("get_all_calendar_names")
def get_all_calendars() -> list[str]:
    """Get a list of all available calendars.

    Returns:
        list[str]: List of calendar names available to the user
        
    Use cases:
        - See all calendars across different roles (Work, Personal, Projects)
        - Check available calendars before creating tasks or events
        - Audit calendar organization
    """
    return calendar_provider.get_all_calendar_names()


@calendar_mcp.tool("create_new_calendar")
def create_new_calendar(name: str) -> str:
    """Create a new calendar for organizing tasks and events.

    Args:
        name (str): Name for the new calendar

    Returns:
        str: Success message with calendar name
        
    Examples:
        - "Work Q1 2025" - for work-specific items
        - "Home Renovation" - for project-specific organization
        - "Personal Health" - for health and fitness tracking
        - "Kids Activities" - for family scheduling
    """
    calendar_provider.create_new_calendar(name)
    return f"Calendar '{name}' created successfully"


@calendar_mcp.tool("get_current_datetime")
def get_current_datetime() -> dict:
    """Get the current date and time in both UTC and user's local timezone.

    Returns:
        dict: Current datetime information including UTC time, local time, timezone, and formatted dates

    Use cases:
        - Calculate relative dates ("tomorrow", "next week", "in 2 hours")
        - Ensure timezone consistency across operations
        - Get current date for scheduling operations
        - Determine "today" for date range queries

    Example response:
        {
            "utc_datetime": "2025-07-06T20:30:00Z",
            "local_datetime": "2025-07-06T15:30:00-05:00", 
            "timezone": "America/New_York",
            "current_date": "2025-07-06",
            "current_time": "15:30:00",
            "weekday": "Sunday",
            "formatted": "Sunday, July 6, 2025 at 3:30 PM"
        }
    """
    # Get current UTC time (modern approach)
    utc_now = datetime.now(timezone.utc)
    
    # Get current time in user's timezone  
    user_tz = get_user_timezone()
    local_now = datetime.now(user_tz)
    
    return {
        "utc_datetime": utc_now.isoformat().replace('+00:00', 'Z'),
        "local_datetime": local_now.isoformat(),
        "timezone": str(user_tz),
        "current_date": local_now.strftime("%Y-%m-%d"),
        "current_time": local_now.strftime("%H:%M:%S"),
        "weekday": local_now.strftime("%A"),
        "formatted": local_now.strftime("%A, %B %d, %Y at %I:%M %p")
    }


# TODO: Future calendar management features:
# @calendar_mcp.tool("delete_calendar")
# @calendar_mcp.tool("rename_calendar") 
# @calendar_mcp.tool("archive_calendar")
# @calendar_mcp.tool("get_calendar_info")
# @calendar_mcp.tool("set_calendar_description")
# @calendar_mcp.tool("move_items_between_calendars")


if __name__ == "__main__":
    calendar_mcp.run(transport="stdio")