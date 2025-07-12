from typing import Protocol, runtime_checkable

from src.core.models import Journal


@runtime_checkable
class JournalProvider(Protocol):
    """Protocol for journal/notes management operations."""

    def create_journal(self, calendar_name: str, summary: str, description: str, date: str | None = None) -> str:
        """Create a new journal entry in the specified calendar."""
        ...

    def get_journals(self, calendar_name: str | None = None, date: str | None = None) -> list[Journal]:
        """Get journal entries, optionally filtered by calendar name and/or date."""
        ...