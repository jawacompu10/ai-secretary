from caldav import DAVClient, Calendar

from ..core.models import Task
from config import calendar_config
from .base import CalendarProvider


class CalDavService:
    """CalDAV service implementation using caldav library."""

    def __init__(self, url: str, username: str, password: str):
        """Initialize the CalDavService with connection details.

        Args:
            url (str): CalDAV server URL
            username (str): Username for authentication
            password (str): Password for authentication
        """
        try:
            self.client = DAVClient(url=url, username=username, password=password)
            self.principal = self.client.principal()
            self._calendars = None
        except Exception as e:
            raise ConnectionError(f"Failed to connect to CalDAV server: {e}")

    @property
    def calendars(self) -> list[Calendar]:
        """Get all calendars, cached after first access."""
        if self._calendars is None:
            try:
                self._calendars = self.principal.calendars()
            except Exception as e:
                raise RuntimeError(f"Failed to fetch calendars: {e}")
        return self._calendars

    def _find_calendar(self, calendar_name: str):
        """Helper method to find a calendar by name.
        
        Args:
            calendar_name (str): Name of the calendar to find
            
        Returns:
            Calendar: The found calendar object
            
        Raises:
            ValueError: If calendar not found
        """
        for calendar in self.calendars:
            if str(calendar.name) == calendar_name:
                return calendar
        
        available_calendars = [str(cal.name) for cal in self.calendars]
        raise ValueError(f"Calendar '{calendar_name}' not found. Available calendars: {available_calendars}")

    def _find_task(self, calendar, summary: str):
        """Helper method to find a task by summary in a calendar.
        
        Args:
            calendar: Calendar object to search in
            summary (str): Task summary to find
            
        Returns:
            Todo: The found todo object
            
        Raises:
            ValueError: If task not found
        """
        for todo in calendar.todos():
            if Task.from_todo(todo, calendar.name).summary == summary:
                return todo
        
        raise ValueError(f"Task '{summary}' not found in calendar '{calendar.name}'")

    def _parse_due_date(self, due_date_str: str | None):
        """Helper method to parse due date string.
        
        Args:
            due_date_str (str | None): Due date in ISO format or None
            
        Returns:
            date | None: Parsed date object or None
            
        Raises:
            ValueError: If date format is invalid
        """
        if not due_date_str:
            return None
        
        from datetime import datetime
        try:
            return datetime.fromisoformat(due_date_str).date()
        except ValueError:
            raise ValueError(f"Invalid due date format: {due_date_str}. Expected YYYY-MM-DD")

    def get_all_calendar_names(self) -> list[str]:
        """Get a list of all calendar names.

        Returns:
            list[str]: list of calendar names

        Raises:
            RuntimeError: If unable to fetch calendar names
        """
        try:
            return [str(cal.name) for cal in self.calendars]
        except Exception as e:
            raise RuntimeError(f"Failed to get calendar names: {e}")

    def create_new_calendar(self, name: str) -> None:
        """Create a new calendar with the given name.

        Args:
            name (str): Name for the new calendar

        Raises:
            ValueError: If name is empty or invalid
            RuntimeError: If unable to create calendar
        """
        if not name or not name.strip():
            raise ValueError("Calendar name cannot be empty")

        try:
            self.principal.make_calendar(name)
            # Invalidate cached calendars
            self._calendars = None
        except Exception as e:
            raise RuntimeError(f"Failed to create calendar '{name}': {e}")

    def get_tasks(self, include_completed: bool = False, calendar_name: str | None = None) -> list[Task]:
        """Get tasks from calendars, optionally filtered by calendar name.

        Args:
            include_completed (bool): Whether to include completed tasks
            calendar_name (str | None): Filter tasks by specific calendar name, or None for all calendars

        Returns:
            list[Task]: list of Task objects from specified calendar(s)

        Raises:
            ValueError: If specified calendar not found
            RuntimeError: If unable to fetch tasks
        """
        tasks = []
        try:
            calendars_to_search = self.calendars
            
            # Filter to specific calendar if requested
            if calendar_name:
                target_calendar = self._find_calendar(calendar_name)
                calendars_to_search = [target_calendar]
            
            for cal in calendars_to_search:
                try:
                    cal_name = str(cal.name)
                    for todo in cal.todos(include_completed=include_completed):
                        tasks.append(Task.from_todo(todo, cal_name))
                except Exception as e:
                    # Log warning but continue with other calendars
                    print(
                        f"Warning: Failed to get tasks from calendar '{cal.name}': {e}"
                    )
                    continue
        except ValueError:
            raise  # Re-raise calendar not found error
        except Exception as e:
            raise RuntimeError(f"Failed to get tasks: {e}")

        return tasks

    def add_task(self, summary: str, calendar_name: str, due_date: str | None = None, description: str | None = None) -> str:
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
        if not summary or not summary.strip():
            raise ValueError("Task summary cannot be empty")

        if not calendar_name or not calendar_name.strip():
            raise ValueError("Calendar name cannot be empty")

        try:
            # Find the calendar and parse due date
            target_calendar = self._find_calendar(calendar_name)
            due_datetime = self._parse_due_date(due_date)

            # Create the task
            target_calendar.save_todo(
                summary=summary,
                due=due_datetime,
                description=description
            )

            due_str = f" (due: {due_date})" if due_date else ""
            desc_str = f" - {description}" if description else ""
            return f"Task created in '{calendar_name}': '{summary}'{due_str}{desc_str}"

        except ValueError:
            raise  # Re-raise ValueError as-is
        except Exception as e:
            raise RuntimeError(f"Failed to create task: {e}")

    def edit_due_date(self, summary: str, calendar_name: str, new_due_date: str | None = None) -> str:
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
            target_calendar = self._find_calendar(calendar_name)
            target_todo = self._find_task(target_calendar, summary)
            
            # Parse new due date
            new_due_datetime = self._parse_due_date(new_due_date)

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
            target_calendar = self._find_calendar(calendar_name)
            target_todo = self._find_task(target_calendar, summary)

            # Mark as completed
            target_todo.complete()
            target_todo.save()

            return f"Task '{summary}' in '{calendar_name}' marked as completed"

        except ValueError:
            raise  # Re-raise ValueError as-is
        except Exception as e:
            raise RuntimeError(f"Failed to complete task: {e}")


def create_calendar_provider() -> CalendarProvider:
    """Factory function to create a CalendarProvider instance with config."""
    return CalDavService(
        url=calendar_config.url,
        username=calendar_config.username,
        password=calendar_config.password,
    )
