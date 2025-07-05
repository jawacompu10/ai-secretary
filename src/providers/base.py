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

    def get_tasks(self, include_completed: bool = False) -> list[Task]:
        """Get all tasks from all calendars."""
        ...