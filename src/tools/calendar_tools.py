import sys
from pathlib import Path

# Add project root to Python path when running directly
if __name__ == "__main__":
    root_dir = Path(__file__).parent.parent.parent
    if str(root_dir) not in sys.path:
        sys.path.insert(0, str(root_dir))

from mcp.server.fastmcp import FastMCP

from src.core.models import Task
from src.providers.base import CalendarProvider
from src.providers.caldav import create_calendar_provider

# Initialize the calendar provider
calendar_provider: CalendarProvider = create_calendar_provider()
calendar_mcp = FastMCP("Calendar")


@calendar_mcp.tool("get_all_calendar_names")
def get_all_calendars() -> list[str]:
    """Get a list of different calendars of the user.

    Returns:
        list[str]: list of calendar names available to the user
    """
    return calendar_provider.get_all_calendar_names()


@calendar_mcp.tool("create_new_calendar", description="Create a new calendar with given name")
def create_new_calendar(name: str):
    """Create a new calendar with the specified name.

    Args:
        name (str): Name for the new calendar
    """
    calendar_provider.create_new_calendar(name)


@calendar_mcp.tool("get_tasks")
def get_tasks(include_completed: bool = False) -> list[Task]:
    """Get all tasks from all calendars.

    Args:
        include_completed (bool): Whether to include completed tasks. Defaults to False.

    Returns:
        list[Task]: list of Task objects from all calendars
    """
    return calendar_provider.get_tasks(include_completed=include_completed)


if __name__ == "__main__":
    calendar_mcp.run(transport="stdio")
