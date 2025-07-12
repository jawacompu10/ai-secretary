"""
Entity finder utilities for calendar providers.

Provider-agnostic entity lookup utilities that can be used by any
calendar provider implementation (CalDAV, Google Calendar, Microsoft Graph, etc.).
"""

from typing import Any, Protocol, TypeVar
from src.core.models import Task, Event, Journal

T = TypeVar('T')


class CalendarLike(Protocol):
    """Protocol for calendar objects that have a name attribute."""
    name: Any
    
    def todos(self, **kwargs) -> list[Any]:
        """Get todos from calendar."""
        ...
        
    def journals(self, **kwargs) -> list[Any]:
        """Get journals from calendar."""
        ...
        
    def events(self, **kwargs) -> list[Any]:
        """Get events from calendar."""
        ...


def find_calendar_by_name(calendars: list[CalendarLike], calendar_name: str) -> CalendarLike:
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
    raise ValueError(f"Calendar '{calendar_name}' not found. Available calendars: {available_calendars}")


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
        if Task.from_todo(todo, calendar.name).summary == summary:
            return todo
    
    raise ValueError(f"Task '{summary}' not found in calendar '{calendar.name}'")


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
        if Journal.from_caldav_journal(journal, calendar.name).summary == summary:
            return journal
    
    raise ValueError(f"Journal '{summary}' not found in calendar '{calendar.name}'")


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
        if Event.from_caldav_event(event, calendar.name).summary == summary:
            return event
    
    raise ValueError(f"Event '{summary}' not found in calendar '{calendar.name}'")


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
        event_obj = Event.from_caldav_event(event, calendar.name)
        if event_obj.summary == summary and event_obj.is_recurring:
            return event
    
    raise ValueError(f"Recurring event '{summary}' not found in calendar '{calendar.name}'")