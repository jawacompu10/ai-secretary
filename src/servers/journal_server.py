"""
Journal Management MCP Server

This server provides tools for managing journal entries - daily notes, reflections,
and personal records. Focused on journaling lifecycle: creating, retrieving,
and organizing personal journal entries across different calendars.
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

from src.core.models import Journal
from src.providers.journal_provider import JournalProvider
from src.providers.caldav_provider import create_calendar_provider
from src.utils.timezone_utils import get_user_timezone

# Initialize the journal provider
journal_provider: JournalProvider = create_calendar_provider()

# Verify the provider supports journal operations
if not isinstance(journal_provider, JournalProvider):
    raise RuntimeError("Calendar provider doesn't support journal operations. Please use a provider that implements JournalProvider.")

journal_mcp = FastMCP("Journal Management")


@journal_mcp.tool("create_journal")
def create_journal(calendar_name: str, summary: str, description: str, date: str | None = None) -> str:
    """Create a new journal entry in the specified calendar.

    Args:
        calendar_name (str): Name of the calendar to add the journal to
        summary (str): Journal title/summary
        description (str): Journal content/description
        date (str | None): Journal date in ISO format (YYYY-MM-DD) or None for today

    Returns:
        str: Success message with journal details

    Examples:
        # Today's journal entry
        {
            "calendar_name": "Personal",
            "summary": "Daily Reflection",
            "description": "Had a productive day working on the secretary project. Made good progress on the journal functionality."
        }

        # Journal entry for specific date
        {
            "calendar_name": "Personal",
            "summary": "Weekend Thoughts",
            "description": "Spent time with family and reflected on work-life balance. Need to prioritize more personal time.",
            "date": "2025-07-12"
        }

        # Work journal entry
        {
            "calendar_name": "Work",
            "summary": "Project Retrospective",
            "description": "Completed the MCP server implementation. Key learnings: better planning reduces debugging time.",
            "date": "2025-07-11"
        }

    Use cases:
        - Daily personal reflections and thoughts
        - Work project notes and retrospectives
        - Learning insights and key takeaways
        - Gratitude journaling and mindfulness notes
        - Meeting or event reflections
    """
    return journal_provider.create_journal(calendar_name, summary, description, date)


@journal_mcp.tool("get_current_datetime")
def get_current_datetime() -> str:
    """Get the current date and time in the user's timezone.
    
    Returns:
        str: Current datetime in ISO format with timezone info
        
    This utility helps with creating journal entries for the current moment
    or understanding what 'today' means in the user's context.
    """
    user_tz = get_user_timezone()
    current_time = datetime.now(timezone.utc).astimezone(user_tz)
    return current_time.isoformat()


@journal_mcp.tool("get_journals")
def get_journals(calendar_name: str | None = None, date: str | None = None) -> list[Journal]:
    """Get journal entries, optionally filtered by calendar name and/or date.

    Args:
        calendar_name (str | None): Filter by specific calendar name, or None for all calendars
        date (str | None): Filter by specific date in ISO format (YYYY-MM-DD), or None for all dates

    Returns:
        list[Journal]: List of Journal objects matching the criteria

    Examples:
        # Get all journal entries from all calendars
        {}

        # Get journal entries from specific calendar
        {
            "calendar_name": "Personal"
        }

        # Get journal entries from specific date
        {
            "date": "2025-07-11"
        }

        # Get journal entries from specific calendar and date
        {
            "calendar_name": "Work",
            "date": "2025-07-11"
        }

        # Get entries from last week
        {
            "date": "2025-07-05"
        }

    Use cases:
        - Review recent journal entries and reflections
        - Find specific journal entries by date
        - Browse journals from a particular calendar (Work, Personal, etc.)
        - Analyze patterns in journaling habits
        - Search for past thoughts and insights
        - Prepare for meetings by reviewing related journal entries
    """
    return journal_provider.get_journals(calendar_name, date)


if __name__ == "__main__":
    journal_mcp.run(transport="stdio")