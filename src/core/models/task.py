from datetime import date
from caldav import Todo
from pydantic import BaseModel, Field
from typing import Literal

from src.utils.icalendar_utils import parse_caldav_component, normalize_caldav_summary


class TaskCreate(BaseModel):
    """Model for creating a new task."""

    summary: str = Field(..., description="Task title/summary")
    calendar_name: str = Field(
        ..., description="Name of the calendar to add the task to"
    )
    due_date: str | None = Field(
        None, description="Due date in ISO format (YYYY-MM-DD)"
    )
    description: str | None = Field(
        None, description="Optional detailed task description"
    )


class TaskUpdate(BaseModel):
    """Model for updating a task's due date."""

    summary: str = Field(..., description="Task summary to identify the task")
    calendar_name: str = Field(..., description="Calendar containing the task")
    new_due_date: str | None = Field(
        None, description="New due date in ISO format (YYYY-MM-DD) or None to remove"
    )


class TaskComplete(BaseModel):
    """Model for marking a task as complete."""

    summary: str = Field(..., description="Task summary to identify the task")
    calendar_name: str = Field(..., description="Calendar containing the task")


class TaskDelete(BaseModel):
    """Model for deleting a task."""

    summary: str = Field(..., description="Task summary to identify the task")
    calendar_name: str = Field(..., description="Calendar containing the task")


class TaskMove(BaseModel):
    """Model for moving a task between calendars."""

    summary: str = Field(..., description="Task summary to identify the task")
    source_calendar: str = Field(..., description="Source calendar containing the task")
    destination_calendar: str = Field(
        ..., description="Destination calendar for the task"
    )


class TaskStatusChange(BaseModel):
    """Model for changing a task's status."""

    summary: str = Field(..., description="Task summary to identify the task")
    calendar_name: str = Field(..., description="Calendar containing the task")
    new_status: Literal["NEEDS-ACTION", "IN-PROCESS", "COMPLETED"] = Field(
        ..., description="New status to set for the task"
    )


class Task(BaseModel):
    """Task model representing a calendar task/todo."""

    name: str  # Keep for backward compatibility, maps to summary
    summary: str | None = Field(default=None)  # VCALENDAR SUMMARY
    description: str | None = Field(default=None)  # VCALENDAR DESCRIPTION
    calendar_name: str = Field(
        ..., description="Name of the calendar containing this task"
    )
    due_on: date | None
    completed: bool
    status: str | None = Field(default=None)

    @classmethod
    def from_todo(cls, todo: Todo, calendar_name: str):
        props = parse_caldav_component(todo.data, "VTODO")
        raw_summary = props.get("SUMMARY", "Untitled Task")
        # Normalize summary to remove any CalDAV line break artifacts
        summary = normalize_caldav_summary(raw_summary)

        return cls(
            name=summary,  # For backward compatibility
            summary=summary,
            description=props.get("DESCRIPTION"),
            calendar_name=calendar_name,
            due_on=todo.get_due(),
            completed=props.get("STATUS") == "COMPLETED",
            status=props.get("STATUS"),
        )
