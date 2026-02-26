"""
Tests for src.utils.entity_finder_utils module.
"""

import pytest
from unittest.mock import Mock, patch

from src.utils.entity_finder_utils import (
    find_calendar_by_name,
    find_task_by_summary,
    find_journal_by_summary,
    find_event_by_summary,
    find_recurring_event_by_summary,
)


class TestFindCalendarByName:
    """Tests for find_calendar_by_name function."""

    def test_find_existing_calendar(self, mock_calendars_list):
        """Test finding an existing calendar by name."""
        result = find_calendar_by_name(mock_calendars_list, "Work")
        assert str(result.name) == "Work"

    def test_find_another_existing_calendar(self, mock_calendars_list):
        """Test finding another existing calendar by name."""
        result = find_calendar_by_name(mock_calendars_list, "Personal")
        assert str(result.name) == "Personal"

    def test_find_nonexistent_calendar(self, mock_calendars_list):
        """Test finding a non-existent calendar raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            find_calendar_by_name(mock_calendars_list, "NonExistent")

        error_message = str(exc_info.value)
        assert "Calendar 'NonExistent' not found" in error_message
        assert "Available calendars:" in error_message
        assert "Work" in error_message
        assert "Personal" in error_message

    def test_find_calendar_empty_list(self):
        """Test finding calendar in empty list raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            find_calendar_by_name([], "AnyCalendar")

        error_message = str(exc_info.value)
        assert "Calendar 'AnyCalendar' not found" in error_message
        assert "Available calendars: []" in error_message

    def test_find_calendar_case_sensitive(self, mock_calendars_list):
        """Test that calendar search is case-sensitive."""
        with pytest.raises(ValueError):
            find_calendar_by_name(mock_calendars_list, "work")  # lowercase

        with pytest.raises(ValueError):
            find_calendar_by_name(mock_calendars_list, "WORK")  # uppercase

    def test_find_calendar_exact_match_required(self, mock_calendars_list):
        """Test that calendar search requires exact match."""
        with pytest.raises(ValueError):
            find_calendar_by_name(mock_calendars_list, "Wor")  # partial match

        with pytest.raises(ValueError):
            find_calendar_by_name(mock_calendars_list, "Work Calendar")  # extra words


class TestFindTaskBySummary:
    """Tests for find_task_by_summary function."""

    @patch("src.utils.entity_finder_utils.Task")
    def test_find_existing_task(self, mock_task_class, mock_calendar):
        """Test finding an existing task by summary."""
        # Setup mock Task.from_todo to return task objects with summaries
        mock_task1 = Mock()
        mock_task1.summary = "Task 1"
        mock_task2 = Mock()
        mock_task2.summary = "Task 2"

        mock_task_class.from_todo.side_effect = [mock_task1, mock_task2]

        # Find the first task
        result = find_task_by_summary(mock_calendar, "Task 1")

        # Should return the underlying todo object, not the Task model
        assert result == mock_calendar.todos.return_value[0]

        # Verify Task.from_todo was called correctly
        assert mock_task_class.from_todo.call_count >= 1
        mock_task_class.from_todo.assert_any_call(
            mock_calendar.todos.return_value[0], str(mock_calendar.name)
        )

    @patch("src.utils.entity_finder_utils.Task")
    def test_find_second_task(self, mock_task_class, mock_calendar):
        """Test finding the second task in the list."""
        mock_task1 = Mock()
        mock_task1.summary = "Task 1"
        mock_task2 = Mock()
        mock_task2.summary = "Task 2"

        mock_task_class.from_todo.side_effect = [mock_task1, mock_task2]

        result = find_task_by_summary(mock_calendar, "Task 2")

        # Should return the second todo object
        assert result == mock_calendar.todos.return_value[1]

    @patch("src.utils.entity_finder_utils.Task")
    def test_find_nonexistent_task(self, mock_task_class, mock_calendar):
        """Test finding a non-existent task raises ValueError."""
        mock_task1 = Mock()
        mock_task1.summary = "Task 1"
        mock_task2 = Mock()
        mock_task2.summary = "Task 2"

        mock_task_class.from_todo.side_effect = [mock_task1, mock_task2]

        with pytest.raises(ValueError) as exc_info:
            find_task_by_summary(mock_calendar, "NonExistent Task")

        error_message = str(exc_info.value)
        assert "Task 'NonExistent Task' not found" in error_message
        assert f"calendar '{str(mock_calendar.name)}'" in error_message

    @patch("src.utils.entity_finder_utils.Task")
    def test_find_task_empty_calendar(self, mock_task_class):
        """Test finding task in calendar with no todos."""
        empty_calendar = Mock()
        empty_calendar.name = "Empty Calendar"
        empty_calendar.todos.return_value = []

        with pytest.raises(ValueError) as exc_info:
            find_task_by_summary(empty_calendar, "Any Task")

        error_message = str(exc_info.value)
        assert "Task 'Any Task' not found" in error_message
        assert f"calendar '{str(empty_calendar.name)}'" in error_message


class TestFindJournalBySummary:
    """Tests for find_journal_by_summary function."""

    @patch("src.utils.entity_finder_utils.Journal")
    def test_find_existing_journal(self, mock_journal_class, mock_calendar):
        """Test finding an existing journal by summary."""
        mock_journal1 = Mock()
        mock_journal1.summary = "Journal 1"
        mock_journal2 = Mock()
        mock_journal2.summary = "Journal 2"

        mock_journal_class.from_caldav_journal.side_effect = [
            mock_journal1,
            mock_journal2,
        ]

        result = find_journal_by_summary(mock_calendar, "Journal 1")

        assert result == mock_calendar.journals.return_value[0]

        # Verify Journal.from_caldav_journal was called correctly
        assert mock_journal_class.from_caldav_journal.call_count >= 1
        mock_journal_class.from_caldav_journal.assert_any_call(
            mock_calendar.journals.return_value[0], str(mock_calendar.name)
        )

    @patch("src.utils.entity_finder_utils.Journal")
    def test_find_nonexistent_journal(self, mock_journal_class, mock_calendar):
        """Test finding a non-existent journal raises ValueError."""
        mock_journal1 = Mock()
        mock_journal1.summary = "Journal 1"

        mock_journal_class.from_caldav_journal.return_value = mock_journal1

        with pytest.raises(ValueError) as exc_info:
            find_journal_by_summary(mock_calendar, "NonExistent Journal")

        error_message = str(exc_info.value)
        assert "Journal 'NonExistent Journal' not found" in error_message
        assert f"calendar '{str(mock_calendar.name)}'" in error_message


class TestFindEventBySummary:
    """Tests for find_event_by_summary function."""

    @patch("src.utils.entity_finder_utils.Event")
    def test_find_existing_event(self, mock_event_class, mock_calendar):
        """Test finding an existing event by summary."""
        mock_event1 = Mock()
        mock_event1.summary = "Event 1"
        mock_event2 = Mock()
        mock_event2.summary = "Event 2"

        mock_event_class.from_caldav_event.side_effect = [mock_event1, mock_event2]

        result = find_event_by_summary(mock_calendar, "Event 1")

        assert result == mock_calendar.events.return_value[0]

        # Verify Event.from_caldav_event was called correctly
        assert mock_event_class.from_caldav_event.call_count >= 1
        mock_event_class.from_caldav_event.assert_any_call(
            mock_calendar.events.return_value[0], str(mock_calendar.name)
        )

    @patch("src.utils.entity_finder_utils.Event")
    def test_find_nonexistent_event(self, mock_event_class, mock_calendar):
        """Test finding a non-existent event raises ValueError."""
        mock_event1 = Mock()
        mock_event1.summary = "Event 1"

        mock_event_class.from_caldav_event.return_value = mock_event1

        with pytest.raises(ValueError) as exc_info:
            find_event_by_summary(mock_calendar, "NonExistent Event")

        error_message = str(exc_info.value)
        assert "Event 'NonExistent Event' not found" in error_message
        assert f"calendar '{str(mock_calendar.name)}'" in error_message


class TestFindRecurringEventBySummary:
    """Tests for find_recurring_event_by_summary function."""

    @patch("src.utils.entity_finder_utils.Event")
    def test_find_existing_recurring_event(self, mock_event_class, mock_calendar):
        """Test finding an existing recurring event by summary."""
        # Setup non-recurring event
        mock_event1 = Mock()
        mock_event1.summary = "Non-Recurring Event"
        mock_event1.is_recurring = False

        # Setup recurring event
        mock_event2 = Mock()
        mock_event2.summary = "Recurring Event"
        mock_event2.is_recurring = True

        mock_event_class.from_caldav_event.side_effect = [mock_event1, mock_event2]

        result = find_recurring_event_by_summary(mock_calendar, "Recurring Event")

        assert result == mock_calendar.events.return_value[1]

    @patch("src.utils.entity_finder_utils.Event")
    def test_find_nonrecurring_event_by_recurring_search(
        self, mock_event_class, mock_calendar
    ):
        """Test that non-recurring events are not found by recurring search."""
        mock_event1 = Mock()
        mock_event1.summary = "Non-Recurring Event"
        mock_event1.is_recurring = False

        mock_event_class.from_caldav_event.return_value = mock_event1

        with pytest.raises(ValueError) as exc_info:
            find_recurring_event_by_summary(mock_calendar, "Non-Recurring Event")

        error_message = str(exc_info.value)
        assert "Recurring event 'Non-Recurring Event' not found" in error_message

    @patch("src.utils.entity_finder_utils.Event")
    def test_find_nonexistent_recurring_event(self, mock_event_class, mock_calendar):
        """Test finding a non-existent recurring event raises ValueError."""
        mock_event1 = Mock()
        mock_event1.summary = "Some Event"
        mock_event1.is_recurring = True

        mock_event_class.from_caldav_event.return_value = mock_event1

        with pytest.raises(ValueError) as exc_info:
            find_recurring_event_by_summary(
                mock_calendar, "NonExistent Recurring Event"
            )

        error_message = str(exc_info.value)
        assert (
            "Recurring event 'NonExistent Recurring Event' not found" in error_message
        )
        assert f"calendar '{str(mock_calendar.name)}'" in error_message


class TestEntityFinderUtilsIntegration:
    """Integration tests for entity finder utilities."""

    def test_calendar_name_from_protocol_method(self):
        """Test that calendar names come from .name property."""
        # Create calendars with different name sources
        calendar1 = Mock()
        calendar1.name = "String Name"

        calendar2 = Mock()
        calendar2.name = "123"  # String from .name property

        calendar3 = Mock()
        calendar3.name = "Mock Name"

        calendars = [calendar1, calendar2, calendar3]

        # Should find calendar with string name
        result = find_calendar_by_name(calendars, "String Name")
        assert result == calendar1

        # Should find calendar with numeric string name
        result = find_calendar_by_name(calendars, "123")
        assert result == calendar2

        # Should find calendar with mock name
        result = find_calendar_by_name(calendars, "Mock Name")
        assert result == calendar3

    @patch("src.utils.entity_finder_utils.Task")
    @patch("src.utils.entity_finder_utils.Journal")
    @patch("src.utils.entity_finder_utils.Event")
    def test_all_finders_handle_empty_collections(
        self, mock_event, mock_journal, mock_task
    ):
        """Test that all finder functions handle empty collections properly."""
        empty_calendar = Mock()
        empty_calendar.name = "Empty Calendar"
        empty_calendar.todos.return_value = []
        empty_calendar.journals.return_value = []
        empty_calendar.events.return_value = []

        # All finders should raise ValueError for empty collections
        with pytest.raises(ValueError, match="Task .* not found"):
            find_task_by_summary(empty_calendar, "Any Task")

        with pytest.raises(ValueError, match="Journal .* not found"):
            find_journal_by_summary(empty_calendar, "Any Journal")

        with pytest.raises(ValueError, match="Event .* not found"):
            find_event_by_summary(empty_calendar, "Any Event")

        with pytest.raises(ValueError, match="Recurring event .* not found"):
            find_recurring_event_by_summary(empty_calendar, "Any Recurring Event")

    def test_error_messages_are_descriptive(self, mock_calendars_list):
        """Test that error messages provide helpful information."""
        # Calendar not found error should list available calendars
        with pytest.raises(ValueError) as exc_info:
            find_calendar_by_name(mock_calendars_list, "NotFound")

        error_msg = str(exc_info.value)
        assert "NotFound" in error_msg
        assert "Available calendars:" in error_msg

        # Entity not found errors should include calendar name and entity name
        calendar = mock_calendars_list[0]

        # Set up the calendar to return empty todos list
        calendar.todos.return_value = []

        with pytest.raises(ValueError) as exc_info:
            find_task_by_summary(calendar, "NotFound")

        error_msg = str(exc_info.value)
        assert "NotFound" in error_msg
        assert str(calendar.name) in error_msg
