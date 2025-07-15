"""
Entity finder utilities for calendar providers.

Provider-agnostic entity lookup utilities that can be used by any
calendar provider implementation (CalDAV, Google Calendar, Microsoft Graph, etc.).
"""

from typing import Any, Protocol, TypeVar
from src.core.models import Task, Event, Journal

T = TypeVar("T")


class CalendarLike(Protocol):
    """Protocol for calendar objects that support entity operations."""

    name: str

    def todos(self, **kwargs) -> list[Any]:
        """Get todos from calendar."""
        ...

    def journals(self, **kwargs) -> list[Any]:
        """Get journals from calendar."""
        ...

    def events(self, **kwargs) -> list[Any]:
        """Get events from calendar."""
        ...


def find_calendar_by_name(
    calendars: list[CalendarLike], calendar_name: str
) -> CalendarLike:
    """Find a calendar by name from a list of calendars.

    Args:
        calendars (list[CalendarLike]): List of calendar objects to search
        calendar_name (str): Name of the calendar to find

    Returns:
        CalendarLike: The found calendar object

    Raises:
        ValueError: If calendar not found
    """
    for calendar in calendars:
        if str(calendar.name) == calendar_name:
            return calendar

    available_calendars = [str(cal.name) for cal in calendars]
    raise ValueError(
        f"Calendar '{calendar_name}' not found. Available calendars: {available_calendars}"
    )


def find_task_by_summary(calendar: CalendarLike, summary: str) -> Any:
    """Find a task by summary in a calendar.

    Args:
        calendar (CalendarLike): Calendar object to search in
        summary (str): Task summary to find

    Returns:
        Any: The found todo object

    Raises:
        ValueError: If task not found
    """
    for todo in calendar.todos():
        if Task.from_todo(todo, str(calendar.name)).summary == summary:
            return todo

    raise ValueError(f"Task '{summary}' not found in calendar '{str(calendar.name)}'")


def find_journal_by_summary(calendar: CalendarLike, summary: str) -> Any:
    """Find a journal by summary in a calendar.

    Args:
        calendar (CalendarLike): Calendar object to search in
        summary (str): Journal summary to find

    Returns:
        Any: The found journal object

    Raises:
        ValueError: If journal not found
    """
    for journal in calendar.journals():
        if Journal.from_caldav_journal(journal, str(calendar.name)).summary == summary:
            return journal

    raise ValueError(
        f"Journal '{summary}' not found in calendar '{str(calendar.name)}'"
    )


def find_journal_by_summary_and_date(calendar: CalendarLike, summary: str, date: str | None = None) -> Any:
    """Find a journal by summary and optionally by date in a calendar.

    Args:
        calendar (CalendarLike): Calendar object to search in
        summary (str): Journal summary to find
        date (str | None): Optional date in ISO format (YYYY-MM-DD) to distinguish journals

    Returns:
        Any: The found journal object

    Raises:
        ValueError: If journal not found or multiple journals found without date filter
    """
    matching_journals = []
    
    for journal in calendar.journals():
        journal_obj = Journal.from_caldav_journal(journal, str(calendar.name))
        if journal_obj.summary == summary:
            if date is None:
                matching_journals.append(journal)
            else:
                # Check if journal date matches (comparing just the date part)
                if journal_obj.date_local and journal_obj.date_local.startswith(date):
                    matching_journals.append(journal)
    
    if len(matching_journals) == 0:
        date_filter = f" with date '{date}'" if date else ""
        raise ValueError(
            f"Journal '{summary}'{date_filter} not found in calendar '{str(calendar.name)}'"
        )
    elif len(matching_journals) > 1 and date is None:
        raise ValueError(
            f"Multiple journals with summary '{summary}' found in calendar '{str(calendar.name)}'. Please specify a date to distinguish between them."
        )
    
    return matching_journals[0]


def find_event_by_summary(calendar: CalendarLike, summary: str) -> Any:
    """Find an event by summary in a calendar.

    Args:
        calendar (CalendarLike): Calendar object to search in
        summary (str): Event summary to find

    Returns:
        Any: The found event object

    Raises:
        ValueError: If event not found
    """
    for event in calendar.events():
        if Event.from_caldav_event(event, str(calendar.name)).summary == summary:
            return event

    raise ValueError(f"Event '{summary}' not found in calendar '{str(calendar.name)}'")


def find_recurring_event_by_summary(calendar: CalendarLike, summary: str) -> Any:
    """Find a recurring event by summary in a calendar.

    Args:
        calendar (CalendarLike): Calendar object to search in
        summary (str): Event summary to find

    Returns:
        Any: The found recurring event object

    Raises:
        ValueError: If recurring event not found
    """
    for event in calendar.events():
        event_obj = Event.from_caldav_event(event, str(calendar.name))
        if event_obj.summary == summary and event_obj.is_recurring:
            return event

    raise ValueError(
        f"Recurring event '{summary}' not found in calendar '{str(calendar.name)}'"
    )
