from typing import Protocol, runtime_checkable

from src.core.models import Journal
from src.core.models.journal import JournalDelete


@runtime_checkable
class JournalProvider(Protocol):
    """Protocol for journal/notes management operations."""

    def create_journal(
        self,
        calendar_name: str,
        summary: str,
        description: str,
        date: str | None = None,
    ) -> str:
        """Create a new journal entry in the specified calendar."""
        ...

    def get_journals(
        self, calendar_name: str | None = None, date: str | None = None, past_days: int | None = None
    ) -> list[Journal]:
        """Get journal entries, optionally filtered by calendar name, date, or past days.
        
        Args:
            calendar_name: Filter by specific calendar name, or None for all calendars
            date: Filter by specific date in ISO format (YYYY-MM-DD), or None for all dates
            past_days: Filter by past X days including today, or None for all dates
            
        Note:
            The 'date' and 'past_days' parameters are mutually exclusive.
        """
        ...

    def edit_journal(
        self,
        summary: str,
        calendar_name: str,
        new_description: str,
        append: bool = True,
    ) -> str:
        """Edit an existing journal entry's description."""
        ...

    def delete_journal(self, journal_delete: JournalDelete) -> str:
        """Delete a journal entry from the specified calendar."""
        ...
