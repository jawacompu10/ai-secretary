from typing import Protocol, runtime_checkable

from src.core.models import Task


@runtime_checkable
class TaskProvider(Protocol):
    """Protocol for task/todo management operations."""

    def get_tasks(
        self, include_completed: bool = False, calendar_name: str | None = None
    ) -> list[Task]:
        """Get tasks from calendars, optionally filtered by calendar name."""
        ...

    def add_task(
        self,
        summary: str,
        calendar_name: str,
        due_date: str | None = None,
        description: str | None = None,
    ) -> str:
        """Add a new task to the specified calendar."""
        ...

    def edit_due_date(
        self, summary: str, calendar_name: str, new_due_date: str | None = None
    ) -> str:
        """Update the due date of an existing task."""
        ...

    def complete_task(self, summary: str, calendar_name: str) -> str:
        """Mark an existing task as completed."""
        ...
