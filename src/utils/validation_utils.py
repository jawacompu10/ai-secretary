"""
Input validation utilities for calendar operations.

Provider-agnostic validation utilities that can be used by any
calendar provider implementation (CalDAV, Google Calendar, Microsoft Graph, etc.).
"""


def validate_required_string(value: str | None, field_name: str) -> None:
    """Validate that a required string field is not empty.

    Args:
        value (str | None): Value to validate
        field_name (str): Name of the field for error messages

    Raises:
        ValueError: If value is None, empty, or only whitespace
    """
    if not value or not value.strip():
        raise ValueError(f"{field_name} cannot be empty")


def validate_calendar_name(calendar_name: str | None) -> None:
    """Validate calendar name input.

    Args:
        calendar_name (str | None): Calendar name to validate

    Raises:
        ValueError: If calendar name is empty or invalid
    """
    validate_required_string(calendar_name, "Calendar name")


def validate_task_summary(summary: str | None) -> None:
    """Validate task summary input.

    Args:
        summary (str | None): Task summary to validate

    Raises:
        ValueError: If summary is empty or invalid
    """
    validate_required_string(summary, "Task summary")


def validate_journal_summary(summary: str | None) -> None:
    """Validate journal summary input.

    Args:
        summary (str | None): Journal summary to validate

    Raises:
        ValueError: If summary is empty or invalid
    """
    validate_required_string(summary, "Journal summary")


def validate_journal_description(description: str | None) -> None:
    """Validate journal description input.

    Args:
        description (str | None): Journal description to validate

    Raises:
        ValueError: If description is empty or invalid
    """
    validate_required_string(description, "Journal description")


def validate_event_summary(summary: str | None) -> None:
    """Validate event summary input.

    Args:
        summary (str | None): Event summary to validate

    Raises:
        ValueError: If summary is empty or invalid
    """
    validate_required_string(summary, "Event summary")


def validate_new_description(description: str | None) -> None:
    """Validate new description input for updates.

    Args:
        description (str | None): New description to validate

    Raises:
        ValueError: If description is empty or invalid
    """
    validate_required_string(description, "New description")
