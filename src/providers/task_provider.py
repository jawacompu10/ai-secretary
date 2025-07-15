from typing import Protocol, runtime_checkable

from src.core.models import Task, TaskDelete, TaskMove


@runtime_checkable
class TaskProvider(Protocol):
    """Protocol for task/todo management operations."""

    def get_tasks(
        self, include_completed: bool = False, calendar_name: str | None = None, past_days: int | None = None
    ) -> list[Task]:
        """Get tasks from calendars, optionally filtered by calendar name and/or past days.
        
        Args:
            include_completed: Whether to include completed tasks
            calendar_name: Filter by specific calendar name, or None for all calendars
            past_days: Filter by tasks due in past X days including today, or None for all tasks
            
        Note:
            Tasks without due dates are always included when past_days filter is used,
            as they are considered "timeless" and still relevant.
        """
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

    def delete_task(self, task_delete: TaskDelete) -> str:
        """Delete an existing task."""
        ...

    def move_task(self, task_move: TaskMove) -> str:
        """Move a task from one calendar to another."""
        ...
