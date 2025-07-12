"""
Task Management MCP Server

This server provides tools for managing tasks/todos across calendars.
Focused on task lifecycle: create, update, complete, and list tasks.
"""

import sys
from pathlib import Path

# Add project root to Python path when running directly
if __name__ == "__main__":
    root_dir = Path(__file__).parent.parent.parent
    if str(root_dir) not in sys.path:
        sys.path.insert(0, str(root_dir))

from mcp.server.fastmcp import FastMCP

from src.core.models import Task, TaskCreate, TaskUpdate, TaskComplete
from src.providers.task_provider import TaskProvider
from src.providers.caldav_provider import create_calendar_provider

# Initialize the task provider
task_provider: TaskProvider = create_calendar_provider()
task_mcp = FastMCP("Tasks")


@task_mcp.tool("get_tasks")
def get_tasks(include_completed: bool = False, calendar_name: str | None = None) -> list[Task]:
    """Get tasks from calendars, optionally filtered by calendar name.

    Args:
        include_completed (bool): Whether to include completed tasks. Defaults to False.
        calendar_name (str | None): Filter tasks by specific calendar name, or None for all calendars

    Returns:
        list[Task]: List of Task objects from specified calendar(s)

    Examples:
        get_tasks()  # All tasks from all calendars
        get_tasks(calendar_name="Work")  # Only work tasks
        get_tasks(include_completed=True, calendar_name="Personal")  # All personal tasks including completed
    """
    return task_provider.get_tasks(
        include_completed=include_completed,
        calendar_name=calendar_name
    )


@task_mcp.tool("add_task")
def add_task(task_data: TaskCreate) -> str:
    """Add a new task/todo to a specific calendar.

    Args:
        task_data (TaskCreate): Task creation data including summary, calendar name, due date, and description

    Returns:
        str: Success message with task details

    Examples:
        {"summary": "Buy Eggs", "calendar_name": "Personal"}
        {"summary": "Automate Auth Test", "calendar_name": "Work", "due_date": "2025-07-10", "description": "Add unit tests for the new feature"}
    """
    return task_provider.add_task(
        summary=task_data.summary,
        calendar_name=task_data.calendar_name,
        due_date=task_data.due_date,
        description=task_data.description
    )


@task_mcp.tool("edit_due_date")
def edit_due_date(task_update: TaskUpdate) -> str:
    """Update the due date of an existing task.

    Args:
        task_update (TaskUpdate): Task update data including summary, calendar name, and new due date

    Returns:
        str: Success message with updated task details

    Examples:
        {"summary": "Buy Eggs", "calendar_name": "Personal", "new_due_date": "2025-07-08"}
        {"summary": "Automate Auth Test", "calendar_name": "Work", "new_due_date": null}
    """
    return task_provider.edit_due_date(
        summary=task_update.summary,
        calendar_name=task_update.calendar_name,
        new_due_date=task_update.new_due_date
    )


@task_mcp.tool("complete_task")
def complete_task(task_complete: TaskComplete) -> str:
    """Mark an existing task as completed.

    Args:
        task_complete (TaskComplete): Task completion data including summary and calendar name

    Returns:
        str: Success message confirming task completion

    Examples:
        {"summary": "Buy Eggs", "calendar_name": "Personal"}
        {"summary": "Automate Auth Test", "calendar_name": "Work"}
    """
    return task_provider.complete_task(
        summary=task_complete.summary,
        calendar_name=task_complete.calendar_name
    )


if __name__ == "__main__":
    task_mcp.run(transport="stdio")