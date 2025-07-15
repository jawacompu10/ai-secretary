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
        self, calendar_name: str | None = None, date: str | None = None
    ) -> list[Journal]:
        """Get journal entries, optionally filtered by calendar name and/or date."""
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
