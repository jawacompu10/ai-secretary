from typing import Protocol

from src.core.models import Task, Event, EventCreate, EventUpdate, EventDelete, EventInstanceCancel, EventInstanceModify, Journal


class CalendarProvider(Protocol):
    """Protocol for calendar provider implementations."""

    def get_all_calendar_names(self) -> list[str]:
        """Get a list of all calendar names."""
        ...

    def create_new_calendar(self, name: str) -> None:
        """Create a new calendar with the given name."""
        ...

    def get_tasks(self, include_completed: bool = False, calendar_name: str | None = None) -> list[Task]:
        """Get tasks from calendars, optionally filtered by calendar name."""
        ...

    def add_task(self, summary: str, calendar_name: str, due_date: str | None = None, description: str | None = None) -> str:
        """Add a new task to the specified calendar."""
        ...

    def edit_due_date(self, summary: str, calendar_name: str, new_due_date: str | None = None) -> str:
        """Update the due date of an existing task."""
        ...

    def complete_task(self, summary: str, calendar_name: str) -> str:
        """Mark an existing task as completed."""
        ...

    # Event methods
    def get_events(self, start_date: str, end_date: str, calendar_name: str | None = None) -> list[Event]:
        """Get events within a date range, optionally filtered by calendar name."""
        ...

    def add_event(self, event_data: EventCreate) -> str:
        """Add a new event to the specified calendar."""
        ...

    def edit_event(self, event_update: EventUpdate) -> str:
        """Update an existing event."""
        ...

    def delete_event(self, event_delete: EventDelete) -> str:
        """Delete an existing event."""
        ...

    def cancel_event_instance(self, instance_cancel: EventInstanceCancel) -> str:
        """Cancel a single instance of a recurring event."""
        ...

    def modify_event_instance(self, instance_modify: EventInstanceModify) -> str:
        """Modify a single instance of a recurring event."""
        ...

    # Journal methods
    def create_journal(self, calendar_name: str, summary: str, description: str, date: str | None = None) -> str:
        """Create a new journal entry in the specified calendar."""
        ...

    def get_journals(self, calendar_name: str | None = None, date: str | None = None) -> list[Journal]:
        """Get journal entries, optionally filtered by calendar name and/or date."""
        ...