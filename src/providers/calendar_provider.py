from typing import Protocol, runtime_checkable


@runtime_checkable
class CalendarProvider(Protocol):
    """Protocol for core calendar management operations."""

    def get_all_calendar_names(self) -> list[str]:
        """Get a list of all calendar names."""
        ...

    def create_new_calendar(self, name: str) -> None:
        """Create a new calendar with the given name."""
        ...
