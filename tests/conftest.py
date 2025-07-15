"""
Pytest configuration and shared fixtures.
"""

import pytest
from unittest.mock import Mock


@pytest.fixture
def mock_calendar():
    """Create a mock calendar object for testing entity finders."""
    calendar = Mock()
    calendar.name = "Test Calendar"

    # Mock todos
    mock_todo1 = Mock()
    mock_todo1.data = "MOCK_TODO_DATA_1"
    mock_todo2 = Mock()
    mock_todo2.data = "MOCK_TODO_DATA_2"
    calendar.todos.return_value = [mock_todo1, mock_todo2]

    # Mock journals
    mock_journal1 = Mock()
    mock_journal1.data = "MOCK_JOURNAL_DATA_1"
    mock_journal2 = Mock()
    mock_journal2.data = "MOCK_JOURNAL_DATA_2"
    calendar.journals.return_value = [mock_journal1, mock_journal2]

    # Mock events
    mock_event1 = Mock()
    mock_event1.data = "MOCK_EVENT_DATA_1"
    mock_event2 = Mock()
    mock_event2.data = "MOCK_EVENT_DATA_2"
    calendar.events.return_value = [mock_event1, mock_event2]

    return calendar


@pytest.fixture
def mock_calendars_list(mock_calendar):
    """Create a list of mock calendars for testing."""
    calendar1 = Mock()
    calendar1.name = "Work"

    calendar2 = Mock()
    calendar2.name = "Personal"

    return [calendar1, calendar2, mock_calendar]


@pytest.fixture
def sample_dates():
    """Provide sample date strings for testing."""
    return {
        "valid_date": "2025-07-12",
        "valid_datetime": "2025-07-12T14:30:00",
        "valid_datetime_with_tz": "2025-07-12T14:30:00+00:00",
        "invalid_date": "not-a-date",
        "invalid_format": "12-07-2025",
        "empty_string": "",
        "whitespace": "   ",
    }


@pytest.fixture
def sample_strings():
    """Provide sample strings for validation testing."""
    return {
        "valid_string": "Valid content",
        "empty_string": "",
        "whitespace_only": "   ",
        "none_value": None,
        "string_with_spaces": "  Content with spaces  ",
    }
