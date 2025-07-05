import sys
from pathlib import Path
from typing import Protocol

# Add parent directory to sys.path for config import
sys.path.insert(0, str(Path(__file__).parent.parent))

from caldav import DAVClient, Calendar
from models import Task
from config import calendar_config


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

    def get_tasks(self, include_completed: bool = False) -> list[Task]:
        """Get all tasks from all calendars.

        Args:
            include_completed (bool): Whether to include completed tasks

        Returns:
            list[Task]: list of Task objects from all calendars

        Raises:
            RuntimeError: If unable to fetch tasks
        """
        tasks = []
        try:
            for cal in self.calendars:
                try:
                    for todo in cal.todos(include_completed=include_completed):
                        tasks.append(Task.from_todo(todo))
                except Exception as e:
                    # Log warning but continue with other calendars
                    print(
                        f"Warning: Failed to get tasks from calendar '{cal.name}': {e}"
                    )
                    continue
        except Exception as e:
            raise RuntimeError(f"Failed to get tasks: {e}")

        return tasks


def create_calendar_provider() -> CalendarProvider:
    """Factory function to create a CalendarProvider instance with config."""
    return CalDavService(
        url=calendar_config.url,
        username=calendar_config.username,
        password=calendar_config.password,
    )
