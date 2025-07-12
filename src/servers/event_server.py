"""
Event Management MCP Server

This server provides tools for managing calendar events - meetings, appointments,
and scheduled activities. Focused on event lifecycle: scheduling, rescheduling,
and managing time-based calendar entries with support for recurring events.
"""

import sys
from pathlib import Path

# Add project root to Python path when running directly
if __name__ == "__main__":
    root_dir = Path(__file__).parent.parent.parent
    if str(root_dir) not in sys.path:
        sys.path.insert(0, str(root_dir))

from mcp.server.fastmcp import FastMCP

from src.core.models import Event, EventCreate, EventUpdate, EventDelete, EventInstanceCancel, EventInstanceModify
from src.providers.event_provider import EventProvider
from src.providers.caldav_provider import create_calendar_provider

# Initialize the event provider
event_provider: EventProvider = create_calendar_provider()
event_mcp = FastMCP("Event Management")


@event_mcp.tool("get_events")
def get_events(start_date: str, end_date: str, calendar_name: str | None = None) -> list[Event]:
    """Get events within a date range, optionally filtered by calendar name.

    Args:
        start_date (str): Start date in ISO format (YYYY-MM-DD)
        end_date (str): End date in ISO format (YYYY-MM-DD)
        calendar_name (str | None): Filter events by specific calendar name, or None for all calendars

    Returns:
        list[Event]: List of Event objects within the specified date range

    Examples:
        get_events("2025-07-01", "2025-07-31")  # All events in July
        get_events("2025-07-06", "2025-07-12", "Work")  # Work events this week
    """
    return event_provider.get_events(start_date, end_date, calendar_name)


@event_mcp.tool("add_event")
def add_event(event_data: EventCreate) -> str:
    """Schedule a new event/meeting/appointment with optional recurring pattern.

    Args:
        event_data (EventCreate): Event creation data including times, location, and recurrence

    Returns:
        str: Success message with event details

    Examples:
        # One-time meeting (UTC)
        {
            "summary": "Team Standup",
            "calendar_name": "Work",
            "start_datetime": "2025-07-08T14:00:00Z",
            "end_datetime": "2025-07-08T14:30:00Z",
            "description": "Daily team sync",
            "location": "Conference Room A"
        }

        # One-time meeting (with timezone)
        {
            "summary": "Client Call",
            "calendar_name": "Work",
            "start_datetime": "2025-07-08T09:00:00-05:00",
            "end_datetime": "2025-07-08T10:00:00-05:00",
            "description": "Eastern time client meeting"
        }

        # Weekly recurring meeting
        {
            "summary": "Weekly Review",
            "calendar_name": "Work", 
            "start_datetime": "2025-07-08T14:00:00Z",
            "end_datetime": "2025-07-08T15:00:00Z",
            "rrule": "FREQ=WEEKLY;BYDAY=TU"
        }

        # Weekday recurring (Monday to Friday)
        {
            "summary": "Daily Standup",
            "calendar_name": "Work",
            "start_datetime": "2025-07-08T14:00:00Z", 
            "end_datetime": "2025-07-08T14:15:00Z",
            "rrule": "FREQ=WEEKLY;BYDAY=MO,TU,WE,TH,FR"
        }

        # Monthly recurring (first Monday of each month)
        {
            "summary": "Monthly Planning",
            "calendar_name": "Work",
            "start_datetime": "2025-07-07T15:00:00Z",
            "end_datetime": "2025-07-07T17:00:00Z", 
            "rrule": "FREQ=MONTHLY;BYDAY=1MO"
        }

        # Limited occurrences (10 times only)
        {
            "summary": "Project Checkpoint",
            "calendar_name": "Work",
            "start_datetime": "2025-07-08T21:00:00Z",
            "end_datetime": "2025-07-08T22:00:00Z",
            "rrule": "FREQ=WEEKLY;COUNT=10"
        }

        # Until specific date
        {
            "summary": "Training Sessions", 
            "calendar_name": "Personal",
            "start_datetime": "2025-07-08T23:00:00Z",
            "end_datetime": "2025-07-09T00:00:00Z",
            "rrule": "FREQ=WEEKLY;UNTIL=20251201T000000Z"
        }
    """
    return event_provider.add_event(event_data)


@event_mcp.tool("edit_event")
def edit_event(event_update: EventUpdate) -> str:
    """Reschedule or modify an existing event.

    Args:
        event_update (EventUpdate): Event update data with new times, location, or recurrence

    Returns:
        str: Success message with updated event details

    Examples:
        # Reschedule meeting
        {
            "summary": "Team Standup",
            "calendar_name": "Work",
            "new_start_datetime": "2025-07-08T15:00:00Z",
            "new_end_datetime": "2025-07-08T15:30:00Z"
        }

        # Change location only
        {
            "summary": "Weekly Review",
            "calendar_name": "Work",
            "new_location": "Zoom Meeting Room"
        }

        # Modify recurring pattern
        {
            "summary": "Daily Standup",
            "calendar_name": "Work", 
            "new_rrule": "FREQ=WEEKLY;BYDAY=MO,WE,FR"
        }

        # Remove recurrence (make one-time)
        {
            "summary": "Project Checkpoint",
            "calendar_name": "Work",
            "new_rrule": null
        }
    """
    return event_provider.edit_event(event_update)


@event_mcp.tool("delete_event")
def delete_event(event_delete: EventDelete) -> str:
    """Cancel/delete an existing event.

    Args:
        event_delete (EventDelete): Event deletion data with summary and calendar

    Returns:
        str: Success message confirming event deletion

    Examples:
        {
            "summary": "Team Standup",
            "calendar_name": "Work"
        }

        {
            "summary": "Personal Appointment", 
            "calendar_name": "Personal"
        }
    """
    return event_provider.delete_event(event_delete)


@event_mcp.tool("cancel_event_instance")
def cancel_event_instance(instance_cancel: EventInstanceCancel) -> str:
    """Cancel a single instance of a recurring event while keeping the series.

    Args:
        instance_cancel (EventInstanceCancel): Instance cancellation data with event and date

    Returns:
        str: Success message confirming instance cancellation

    Examples:
        # Cancel next Tuesday's standup
        {
            "summary": "Daily Standup",
            "calendar_name": "Work",
            "instance_date": "2025-07-15"
        }

        # Cancel specific training session
        {
            "summary": "Weekly Training",
            "calendar_name": "Personal", 
            "instance_date": "2025-07-22"
        }

    Use cases:
        - Skip one occurrence due to holiday/vacation
        - Cancel meeting when key attendees unavailable
        - Temporary schedule conflicts
        - Keep recurring pattern but exclude specific dates
    """
    return event_provider.cancel_event_instance(instance_cancel)


@event_mcp.tool("modify_event_instance")
def modify_event_instance(instance_modify: EventInstanceModify) -> str:
    """Modify a single instance of a recurring event (time, location, etc.).

    Args:
        instance_modify (EventInstanceModify): Instance modification data

    Returns:
        str: Success message with modified instance details

    Examples:
        # Move Tuesday's standup to different time
        {
            "summary": "Daily Standup",
            "calendar_name": "Work",
            "instance_date": "2025-07-15",
            "new_start_datetime": "2025-07-15T10:00:00Z",
            "new_end_datetime": "2025-07-15T10:15:00Z"
        }

        # Change location for one session
        {
            "summary": "Weekly Review",
            "calendar_name": "Work",
            "instance_date": "2025-07-22",
            "new_location": "Conference Room B"
        }

        # Extend one meeting duration
        {
            "summary": "Project Sync",
            "calendar_name": "Work",
            "instance_date": "2025-07-18",
            "new_end_datetime": "2025-07-18T16:00:00Z",
            "new_description": "Extended session for Q3 planning"
        }

    Use cases:
        - One-time schedule adjustments
        - Room changes for specific dates
        - Extended sessions for special topics
        - Guest attendees requiring different arrangements
    """
    return event_provider.modify_event_instance(instance_modify)


if __name__ == "__main__":
    event_mcp.run(transport="stdio")