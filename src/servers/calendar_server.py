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

from src.providers.base import CalendarProvider
from src.providers.caldav import create_calendar_provider

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


# TODO: Future calendar management features:
# @calendar_mcp.tool("delete_calendar")
# @calendar_mcp.tool("rename_calendar") 
# @calendar_mcp.tool("archive_calendar")
# @calendar_mcp.tool("get_calendar_info")
# @calendar_mcp.tool("set_calendar_description")
# @calendar_mcp.tool("move_items_between_calendars")


if __name__ == "__main__":
    calendar_mcp.run(transport="stdio")