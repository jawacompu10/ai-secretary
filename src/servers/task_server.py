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

from src.core.models import Task, TaskCreate, TaskUpdate, TaskComplete, TaskDelete, TaskMove
from src.providers.task_provider import TaskProvider
from src.providers.caldav_provider import create_calendar_provider

# Initialize the task provider
task_provider: TaskProvider = create_calendar_provider()
task_mcp = FastMCP("Tasks")


@task_mcp.tool("get_tasks")
def get_tasks(
    include_completed: bool = False, calendar_name: str | None = None, past_days: int | None = None
) -> list[Task]:
    """Get tasks from calendars, optionally filtered by calendar name and/or past days.

    Args:
        include_completed (bool): Whether to include completed tasks. Defaults to False.
        calendar_name (str | None): Filter tasks by specific calendar name, or None for all calendars
        past_days (int | None): Filter by tasks due in past X days including today, or None for all tasks.
                               🔥 AUTOMATIC DEFAULT: When include_completed=True and past_days=None, 
                               this automatically defaults to 7 days to prevent overwhelming results.

    Returns:
        list[Task]: List of Task objects from specified calendar(s)

    Examples:
        get_tasks()  # All active tasks from all calendars
        get_tasks(calendar_name="Work")  # Only work tasks
        get_tasks(include_completed=True)  # 🔥 AUTO-LIMITED: Completed tasks from past 7 days only
        get_tasks(include_completed=True, past_days=30)  # Override: All tasks from past 30 days
        get_tasks(past_days=7)  # Tasks due in past 7 days from all calendars
        get_tasks(calendar_name="Work", past_days=14)  # Work tasks due in past 14 days
        get_tasks(include_completed=True, calendar_name="Personal")  # 🔥 AUTO-LIMITED: Personal completed tasks from past 7 days

    Use cases:
        - **Recent task review**: Get past 7 days of tasks for weekly review
        - **Completed task analysis**: Use include_completed=True for recent productivity analysis (auto-limited to 7 days)
        - **Overdue task check**: Get past 1-3 days to find recently overdue tasks
        - **Calendar-specific focus**: Combine calendar_name with past_days for targeted reviews
        - **Avoid overwhelming results**: Completed tasks are auto-limited to 7 days unless past_days is specified

    💡 Client Implementation Suggestion:
        When include_completed=True and past_days is None, inform the user:
        "Showing completed tasks from the past 7 days. Would you like to see more? 
        I can get completed tasks from the past 30 days."

    Note:
        Tasks without due dates are always included when past_days filter is used, 
        as they are considered "timeless" and still relevant.
    """
    # Apply default past_days when include_completed=True to avoid overwhelming results
    if include_completed and past_days is None:
        past_days = 7  # Default to past 7 days for completed tasks
    
    return task_provider.get_tasks(
        include_completed=include_completed, calendar_name=calendar_name, past_days=past_days
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
        description=task_data.description,
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
        new_due_date=task_update.new_due_date,
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
        summary=task_complete.summary, calendar_name=task_complete.calendar_name
    )


@task_mcp.tool("delete_task")
def delete_task(task_delete: TaskDelete) -> str:
    """Delete an existing task from a calendar.

    Args:
        task_delete (TaskDelete): Task deletion data including summary and calendar name

    Returns:
        str: Success message confirming task deletion

    Examples:
        {"summary": "Buy Eggs", "calendar_name": "Personal"}
        {"summary": "Automate Auth Test", "calendar_name": "Work"}
    """
    return task_provider.delete_task(task_delete)


@task_mcp.tool("move_task")
def move_task(task_move: TaskMove) -> str:
    """Move a task from one calendar to another.

    This operation copies the task (including all properties like due date, description, 
    and completion status) to the destination calendar and removes it from the source calendar.

    Args:
        task_move (TaskMove): Task move data including summary, source calendar, and destination calendar

    Returns:
        str: Success message confirming task move

    Examples:
        {"summary": "Schedule team meeting", "source_calendar": "Personal", "destination_calendar": "Work"}
        {"summary": "Research new laptop", "source_calendar": "Work", "destination_calendar": "Personal"}
    """
    return task_provider.move_task(task_move)


if __name__ == "__main__":
    task_mcp.run(transport="stdio")
