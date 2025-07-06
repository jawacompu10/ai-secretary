from typing import Protocol

from ..core.models import Task


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