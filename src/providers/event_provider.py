from typing import Protocol, runtime_checkable

from src.core.models import Event, EventCreate, EventUpdate, EventDelete, EventInstanceCancel, EventInstanceModify


@runtime_checkable
class EventProvider(Protocol):
    """Protocol for event/meeting management operations."""

    def get_events(self, start_date: str, end_date: str, calendar_name: str | None = None) -> list[Event]:
        """Get events within a date range, optionally filtered by calendar name."""
        ...

    def add_event(self, event_data: EventCreate) -> str:
        """Add a new event to the specified calendar."""
        ...

    def edit_event(self, event_update: EventUpdate) -> str:
        """Update an existing event."""
        ...

    def delete_event(self, event_delete: EventDelete) -> str:
        """Delete an existing event."""
        ...

    def cancel_event_instance(self, instance_cancel: EventInstanceCancel) -> str:
        """Cancel a single instance of a recurring event."""
        ...

    def modify_event_instance(self, instance_modify: EventInstanceModify) -> str:
        """Modify a single instance of a recurring event."""
        ...