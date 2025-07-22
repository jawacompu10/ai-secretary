from src.core.models import (
    Task,
    TaskQuery,
    TaskDelete,
    TaskMove,
    TaskStatusChange,
    Event,
    EventCreate,
    EventUpdate,
    EventDelete,
    EventInstanceCancel,
    EventInstanceModify,
    Journal,
)
from src.core.models.journal import JournalDelete
from src.providers.calendar_provider import CalendarProvider
from src.providers.task_provider import TaskProvider
from src.providers.event_provider import EventProvider
from src.providers.journal_provider import JournalProvider
from config import calendar_config

from .caldav_services.base import CalDavBase
from .caldav_services.calendar_service import CalDavCalendarService
from .caldav_services.task_service import CalDavTaskService
from .caldav_services.event_service import CalDavEventService
from .caldav_services.journal_service import CalDavJournalService


class CalDavService(CalendarProvider, TaskProvider, EventProvider, JournalProvider):
    """CalDAV service implementation using composition of specialized service classes."""

    def __init__(self, url: str, username: str, password: str):
        """Initialize the CalDavService with connection details.

        Args:
            url (str): CalDAV server URL
            username (str): Username for authentication
            password (str): Password for authentication
        """
        # Create single shared CalDAV base instance
        self._caldav_base = CalDavBase(url, username, password)

        # Create specialized service instances with shared base
        self._calendar_service = CalDavCalendarService(self._caldav_base)
        self._task_service = CalDavTaskService(self._caldav_base)
        self._event_service = CalDavEventService(self._caldav_base)
        self._journal_service = CalDavJournalService(self._caldav_base)

    # Calendar Provider methods - delegate to calendar service
    def get_all_calendar_names(self) -> list[str]:
        """Get a list of all calendar names."""
        return self._calendar_service.get_all_calendar_names()

    def create_new_calendar(self, name: str) -> None:
        """Create a new calendar with the given name."""
        self._calendar_service.create_new_calendar(name)
        # Cache is automatically shared across all services via the shared base

    # Task Provider methods - delegate to task service
    def get_tasks(
        self,
        query: TaskQuery | None = None,
        *,
        include_completed: bool = False,
        calendar_name: str | None = None,
        past_days: int | None = None,
        future_days: int | None = None,
    ) -> list[Task]:
        """Get tasks from calendars, optionally filtered by query parameters.
        
        Args:
            query: TaskQuery object with filter parameters (preferred)
            include_completed: Whether to include completed tasks (legacy)
            calendar_name: Filter by calendar name (legacy)  
            past_days: Filter by past days (legacy)
            future_days: Filter by future days (legacy)
        """
        # If query is provided, use it directly
        if query is not None:
            return self._task_service.get_tasks(query)
        
        # Otherwise, create query from individual parameters (backward compatibility)
        query = TaskQuery(
            include_completed=include_completed,
            calendar_name=calendar_name,
            past_days=past_days,
            future_days=future_days,
        )
        return self._task_service.get_tasks(query)

    def add_task(
        self,
        summary: str,
        calendar_name: str,
        due_date: str | None = None,
        description: str | None = None,
    ) -> str:
        """Add a new task to the specified calendar."""
        return self._task_service.add_task(
            summary, calendar_name, due_date, description
        )

    def edit_due_date(
        self, summary: str, calendar_name: str, new_due_date: str | None = None
    ) -> str:
        """Update the due date of an existing task."""
        return self._task_service.edit_due_date(summary, calendar_name, new_due_date)

    def complete_task(self, summary: str, calendar_name: str) -> str:
        """Mark an existing task as completed."""
        return self._task_service.complete_task(summary, calendar_name)

    def delete_task(self, task_delete: TaskDelete) -> str:
        """Delete an existing task from the specified calendar."""
        return self._task_service.delete_task(task_delete)

    def move_task(self, task_move: TaskMove) -> str:
        """Move a task from one calendar to another."""
        return self._task_service.move_task(task_move)

    def change_status(self, task_status_change: TaskStatusChange) -> str:
        """Change the status of an existing task."""
        return self._task_service.change_status(task_status_change)

    # Event Provider methods - delegate to event service
    def get_events(
        self, start_date: str, end_date: str, calendar_name: str | None = None
    ) -> list[Event]:
        """Get events within a date range, optionally filtered by calendar name."""
        return self._event_service.get_events(start_date, end_date, calendar_name)

    def add_event(self, event_data: EventCreate) -> str:
        """Add a new event to the specified calendar using EventCreate model."""
        return self._event_service.add_event(event_data)

    def edit_event(self, event_update: EventUpdate) -> str:
        """Update an existing event using EventUpdate model."""
        return self._event_service.edit_event(event_update)

    def delete_event(self, event_delete: EventDelete) -> str:
        """Delete an existing event using EventDelete model."""
        return self._event_service.delete_event(event_delete)

    def cancel_event_instance(self, instance_cancel: EventInstanceCancel) -> str:
        """Cancel a single instance of a recurring event using EXDATE."""
        return self._event_service.cancel_event_instance(instance_cancel)

    def modify_event_instance(self, instance_modify: EventInstanceModify) -> str:
        """Modify a single instance of a recurring event."""
        return self._event_service.modify_event_instance(instance_modify)

    # Journal Provider methods - delegate to journal service
    def create_journal(
        self,
        calendar_name: str,
        summary: str,
        description: str,
        date: str | None = None,
    ) -> str:
        """Create a new journal entry in the specified calendar."""
        return self._journal_service.create_journal(
            calendar_name, summary, description, date
        )

    def get_journals(
        self,
        calendar_name: str | None = None,
        date: str | None = None,
        past_days: int | None = None,
    ) -> list[Journal]:
        """Get journal entries, optionally filtered by calendar name, date, or past days."""
        return self._journal_service.get_journals(calendar_name, date, past_days)

    def edit_journal(
        self,
        summary: str,
        calendar_name: str,
        new_description: str,
        append: bool = True,
    ) -> str:
        """Edit an existing journal entry's description."""
        return self._journal_service.edit_journal(
            summary, calendar_name, new_description, append
        )

    def delete_journal(self, journal_delete: JournalDelete) -> str:
        """Delete a journal entry from the specified calendar."""
        return self._journal_service.delete_journal(journal_delete)


def create_calendar_provider() -> CalDavService:
    """Factory function to create a CalDAV service with config."""
    return CalDavService(
        url=calendar_config.url,
        username=calendar_config.username,
        password=calendar_config.password,
    )
