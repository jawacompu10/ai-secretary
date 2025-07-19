from src.core.models import Task, TaskDelete, TaskMove, TaskStatusChange
from src.providers.task_provider import TaskProvider
from src.utils.date_utils import parse_due_date, calculate_past_days_range
from src.utils.entity_finder_utils import find_calendar_by_name, find_task_by_summary
from src.utils.validation_utils import validate_task_summary, validate_calendar_name
from .base import CalDavBase


class CalDavTaskService(TaskProvider):
    """CalDAV service implementation for task/todo management operations."""

    def __init__(self, caldav_base: CalDavBase):
        """Initialize with shared CalDAV base instance."""
        self.caldav_base = caldav_base

    @property
    def calendars(self):
        """Access shared calendars from base instance."""
        return self.caldav_base.calendars

    def get_tasks(
        self,
        include_completed: bool = False,
        calendar_name: str | None = None,
        past_days: int | None = None,
    ) -> list[Task]:
        """Get tasks from calendars, optionally filtered by calendar name and/or past days.

        Args:
            include_completed (bool): Whether to include completed tasks
            calendar_name (str | None): Filter tasks by specific calendar name, or None for all calendars
            past_days (int | None): Filter by tasks due in past X days including today, or None for all tasks

        Returns:
            list[Task]: list of Task objects from specified calendar(s)

        Raises:
            ValueError: If specified calendar not found or invalid past_days value
            RuntimeError: If unable to fetch tasks
        """
        tasks = []
        try:
            # Parse past_days filter if provided
            date_range_start = None
            date_range_end = None
            if past_days:
                if not isinstance(past_days, int) or past_days < 1:
                    raise ValueError(
                        f"past_days must be a positive integer, got: {past_days}"
                    )
                date_range_start, date_range_end = calculate_past_days_range(past_days)

            calendars_to_search = self.calendars

            # Filter to specific calendar if requested
            if calendar_name:
                target_calendar = find_calendar_by_name(self.calendars, calendar_name)
                calendars_to_search = [target_calendar]

            for cal in calendars_to_search:
                try:
                    cal_name = str(cal.name)
                    for todo in cal.todos(include_completed=include_completed):
                        task = Task.from_todo(todo, cal_name)

                        # Apply past_days filter if specified
                        if date_range_start and date_range_end:
                            # Include tasks without due dates (they're timeless/still relevant)
                            if task.due_on is None:
                                tasks.append(task)
                                continue

                            # Check if task's due date falls within the range
                            if date_range_start <= task.due_on <= date_range_end:
                                tasks.append(task)
                        else:
                            # No date filtering, include all tasks
                            tasks.append(task)

                except Exception as e:
                    # Log warning but continue with other calendars
                    print(
                        f"Warning: Failed to get tasks from calendar '{cal.name}': {e}"
                    )
                    continue
        except ValueError:
            raise  # Re-raise calendar not found error and validation errors
        except Exception as e:
            raise RuntimeError(f"Failed to get tasks: {e}")

        return tasks

    def add_task(
        self,
        summary: str,
        calendar_name: str,
        due_date: str | None = None,
        description: str | None = None,
    ) -> str:
        """Add a new task to the specified calendar.

        Args:
            summary (str): Task title/summary
            calendar_name (str): Name of the calendar to add the task to
            due_date (str | None): Due date in ISO format (YYYY-MM-DD) or None
            description (str | None): Optional task description

        Returns:
            str: Success message with task details

        Raises:
            ValueError: If summary is empty or calendar not found
            RuntimeError: If unable to create task
        """
        validate_task_summary(summary)
        validate_calendar_name(calendar_name)

        try:
            # Find the calendar and parse due date
            target_calendar = find_calendar_by_name(self.calendars, calendar_name)
            due_datetime = parse_due_date(due_date)

            # Create the task
            target_calendar.save_todo(
                summary=summary, due=due_datetime, description=description
            )

            due_str = f" (due: {due_date})" if due_date else ""
            desc_str = f" - {description}" if description else ""
            return f"Task created in '{calendar_name}': '{summary}'{due_str}{desc_str}"

        except ValueError:
            raise  # Re-raise ValueError as-is
        except Exception as e:
            raise RuntimeError(f"Failed to create task: {e}")

    def edit_due_date(
        self, summary: str, calendar_name: str, new_due_date: str | None = None
    ) -> str:
        """Update the due date of an existing task.

        Args:
            summary (str): Task summary to identify the task
            calendar_name (str): Calendar containing the task
            new_due_date (str | None): New due date in ISO format (YYYY-MM-DD) or None to remove

        Returns:
            str: Success message with task details

        Raises:
            ValueError: If task or calendar not found
            RuntimeError: If unable to update task
        """
        try:
            # Find calendar and task
            target_calendar = find_calendar_by_name(self.calendars, calendar_name)
            target_todo = find_task_by_summary(target_calendar, summary)

            # Parse new due date
            new_due_datetime = parse_due_date(new_due_date)

            # Update the due date
            target_todo.set_due(new_due_datetime)
            target_todo.save()

            due_str = f" to {new_due_date}" if new_due_date else " (removed)"
            return f"Updated due date for '{summary}' in '{calendar_name}'{due_str}"

        except ValueError:
            raise  # Re-raise ValueError as-is
        except Exception as e:
            raise RuntimeError(f"Failed to update task due date: {e}")

    def complete_task(self, summary: str, calendar_name: str) -> str:
        """Mark an existing task as completed.

        Args:
            summary (str): Task summary to identify the task
            calendar_name (str): Calendar containing the task

        Returns:
            str: Success message with task details

        Raises:
            ValueError: If task or calendar not found
            RuntimeError: If unable to complete task
        """
        try:
            # Find calendar and task
            target_calendar = find_calendar_by_name(self.calendars, calendar_name)
            target_todo = find_task_by_summary(target_calendar, summary)

            # Check if task is already completed
            task_obj = Task.from_todo(target_todo, calendar_name)
            if task_obj.completed:
                return f"Task '{summary}' in '{calendar_name}' is already completed"

            # Mark as completed
            target_todo.complete()
            target_todo.save()

            return f"Task '{summary}' in '{calendar_name}' marked as completed"

        except ValueError:
            raise  # Re-raise ValueError as-is
        except Exception as e:
            raise RuntimeError(f"Failed to complete task: {e}")

    def delete_task(self, task_delete: TaskDelete) -> str:
        """Delete an existing task from the specified calendar.

        Args:
            task_delete (TaskDelete): Task deletion details

        Returns:
            str: Success message with task details

        Raises:
            ValueError: If task or calendar not found
            RuntimeError: If unable to delete task
        """
        try:
            # Find calendar and task
            target_calendar = find_calendar_by_name(
                self.calendars, task_delete.calendar_name
            )
            target_todo = find_task_by_summary(target_calendar, task_delete.summary)

            # Delete the task
            target_todo.delete()

            return f"Task '{task_delete.summary}' deleted from '{task_delete.calendar_name}'"

        except ValueError:
            raise  # Re-raise ValueError as-is
        except Exception as e:
            raise RuntimeError(f"Failed to delete task: {e}")

    def move_task(self, task_move: TaskMove) -> str:
        """Move a task from one calendar to another.

        This operation works by:
        1. Finding the task in the source calendar
        2. Extracting its properties (summary, description, due date, completion status)
        3. Creating an identical task in the destination calendar
        4. Deleting the original task from the source calendar

        Args:
            task_move (TaskMove): Task move details with source and destination calendars

        Returns:
            str: Success message with move details

        Raises:
            ValueError: If task, source calendar, or destination calendar not found
            RuntimeError: If unable to move task
        """
        try:
            # Find source calendar and task
            source_calendar = find_calendar_by_name(
                self.calendars, task_move.source_calendar
            )
            source_todo = find_task_by_summary(source_calendar, task_move.summary)

            # Find destination calendar
            destination_calendar = find_calendar_by_name(
                self.calendars, task_move.destination_calendar
            )

            # Extract task properties from source task
            from src.utils.vcalendar_parser import vcalendar_to_dict

            props = vcalendar_to_dict(source_todo.data)

            summary = props.get("SUMMARY", "Untitled Task")
            description = props.get("DESCRIPTION")
            due_date = source_todo.get_due()

            # Create the task in destination calendar
            destination_calendar.save_todo(
                summary=summary, due=due_date, description=description
            )

            # If the original task was completed, mark the new one as completed
            if props.get("STATUS") == "COMPLETED":
                # Find the newly created task and mark it as completed
                new_todo = find_task_by_summary(destination_calendar, summary)
                new_todo.complete()
                new_todo.save()

            # Delete the original task from source calendar
            source_todo.delete()

            return f"Task '{task_move.summary}' moved from '{task_move.source_calendar}' to '{task_move.destination_calendar}'"

        except ValueError:
            raise  # Re-raise ValueError as-is
        except Exception as e:
            raise RuntimeError(f"Failed to move task: {e}")

    def change_status(self, task_status_change: TaskStatusChange) -> str:
        """Change the status of an existing task.

        Args:
            task_status_change (TaskStatusChange): Task status change details

        Returns:
            str: Success message with status change details

        Raises:
            ValueError: If task or calendar not found, or invalid status
            RuntimeError: If unable to change task status
        """
        try:
            # Find calendar and task
            target_calendar = find_calendar_by_name(
                self.calendars, task_status_change.calendar_name
            )
            target_todo = find_task_by_summary(
                target_calendar, task_status_change.summary
            )

            # Set the new status
            if task_status_change.new_status == "COMPLETED":
                target_todo.complete()
            else:
                # For NEEDS-ACTION and IN-PROCESS, set the status property directly
                target_todo.icalendar_component['STATUS'] = task_status_change.new_status

            # Save the changes
            target_todo.save()

            return f"Task '{task_status_change.summary}' in '{task_status_change.calendar_name}' status changed to '{task_status_change.new_status}'"

        except ValueError:
            raise  # Re-raise ValueError as-is
        except Exception as e:
            raise RuntimeError(f"Failed to change task status: {e}")
