from datetime import date
from caldav import Todo
from pydantic import BaseModel, Field, field_validator, model_validator
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


class TaskQuery(BaseModel):
    """Model for querying tasks with various filters."""
    
    include_completed: bool = Field(
        default=False, description="Whether to include completed tasks"
    )
    calendar_name: str | None = Field(
        default=None, description="Filter tasks by specific calendar name, or None for all calendars"
    )
    past_days: int | None = Field(
        default=None, description="Filter by tasks due in past X days including today, or None for all tasks"
    )
    future_days: int | None = Field(
        default=None, description="Filter by tasks due in future X days including today, or None for all tasks"
    )

    @field_validator('past_days', 'future_days')
    @classmethod
    def validate_positive_days(cls, v):
        """Validate that days values are positive integers when provided."""
        if v is not None and (not isinstance(v, int) or v < 1):
            raise ValueError("Days must be a positive integer")
        return v

    @model_validator(mode='after')
    def validate_mutually_exclusive_days(self):
        """Validate that past_days and future_days are not both specified."""
        if self.past_days is not None and self.future_days is not None:
            raise ValueError("Cannot specify both past_days and future_days filters")
        return self


class Task(BaseModel):
    """Task model representing a calendar task/todo."""

    summary: str = Field(..., description="Task title/summary")  # VCALENDAR SUMMARY
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
            summary=summary,
            description=props.get("DESCRIPTION"),
            calendar_name=calendar_name,
            due_on=todo.get_due(),
            completed=props.get("STATUS") == "COMPLETED",
            status=props.get("STATUS"),
        )
