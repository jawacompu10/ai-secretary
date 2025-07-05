from mcp.server.fastmcp import FastMCP

from models import Task
from calendar_service import CalendarProvider, create_calendar_provider

# Initialize the calendar provider
calendar_provider: CalendarProvider = create_calendar_provider()
mcp = FastMCP("Calendar")


@mcp.tool("get_all_calendar_names")
def get_all_calendars() -> list[str]:
    """Get a list of different calendars of the user.

    Returns:
        list[str]: list of calendar names available to the user
    """
    return calendar_provider.get_all_calendar_names()


@mcp.tool("create_new_calendar", description="Create a new calendar with given name")
def create_new_calendar(name: str):
    """Create a new calendar with the specified name.

    Args:
        name (str): Name for the new calendar
    """
    calendar_provider.create_new_calendar(name)


@mcp.tool("get_tasks")
def get_tasks(include_completed: bool = False) -> list[Task]:
    """Get all tasks from all calendars.

    Args:
        include_completed (bool): Whether to include completed tasks. Defaults to False.

    Returns:
        list[Task]: list of Task objects from all calendars
    """
    return calendar_provider.get_tasks(include_completed=include_completed)


if __name__ == "__main__":
    mcp.run(transport="stdio")
