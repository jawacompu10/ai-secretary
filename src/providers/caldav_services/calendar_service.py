from src.providers.calendar_provider import CalendarProvider
from src.utils.validation_utils import validate_calendar_name
from .base import CalDavBase


class CalDavCalendarService(CalendarProvider):
    """CalDAV service implementation for calendar management operations."""

    def __init__(self, caldav_base: CalDavBase):
        """Initialize with shared CalDAV base instance."""
        self.caldav_base = caldav_base

    @property
    def calendars(self):
        """Access shared calendars from base instance."""
        return self.caldav_base.calendars

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
        validate_calendar_name(name)

        try:
            self.caldav_base.principal.make_calendar(name)
            # Invalidate cached calendars
            self.caldav_base.invalidate_calendar_cache()
        except Exception as e:
            raise RuntimeError(f"Failed to create calendar '{name}': {e}")
