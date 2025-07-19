"""
Tests for src.providers.caldav.journal_service module.
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timezone

from src.providers.caldav.journal_service import CalDavJournalService
from src.providers.caldav.base import CalDavBase


@pytest.fixture
def mock_caldav_base():
    """Create a mock CalDavBase instance for testing."""
    base = Mock(spec=CalDavBase)

    # Mock calendar
    mock_calendar = Mock()
    mock_calendar.name = "Test Journal Calendar"
    mock_calendar.save_journal = Mock()

    # Mock calendars property
    base.calendars = [mock_calendar]

    return base


@pytest.fixture
def journal_service(mock_caldav_base):
    """Create a CalDavJournalService instance with mocked base."""
    return CalDavJournalService(mock_caldav_base)


@pytest.fixture
def mock_calendar_found():
    """Create a mock calendar that will be returned by find_calendar_by_name."""
    mock_calendar = Mock()
    mock_calendar.name = "Personal"
    mock_calendar.save_journal = Mock()
    return mock_calendar


class TestCalDavJournalServiceCreate:
    """Tests for CalDavJournalService.create_journal method."""

    @patch("src.providers.caldav.journal_service.find_calendar_by_name")
    @patch("src.providers.caldav.journal_service.validate_journal_summary")
    @patch("src.providers.caldav.journal_service.validate_journal_description")
    @patch("src.providers.caldav.journal_service.validate_calendar_name")
    def test_journal_creation_with_explicit_date(
        self,
        mock_validate_calendar,
        mock_validate_description,
        mock_validate_summary,
        mock_find_calendar,
        journal_service,
        mock_calendar_found,
    ):
        """Test journal creation with specific date provided."""
        # Setup
        mock_find_calendar.return_value = mock_calendar_found
        test_date = "2025-07-19"
        # With timezone fix, datetime should be timezone-aware
        from zoneinfo import ZoneInfo

        expected_dtstart = datetime(2025, 7, 19, tzinfo=ZoneInfo("UTC"))

        # Execute
        result = journal_service.create_journal(
            calendar_name="Personal",
            summary="Test Journal Entry",
            description="This is a test journal entry.",
            date=test_date,
        )

        # Verify validations were called
        mock_validate_summary.assert_called_once_with("Test Journal Entry")
        mock_validate_description.assert_called_once_with(
            "This is a test journal entry."
        )
        mock_validate_calendar.assert_called_once_with("Personal")

        # Verify calendar lookup
        mock_find_calendar.assert_called_once_with(
            journal_service.calendars, "Personal"
        )

        # Verify save_journal was called with correct parameters
        mock_calendar_found.save_journal.assert_called_once_with(
            summary="Test Journal Entry",
            description="This is a test journal entry.",
            dtstart=expected_dtstart,
        )

        # Verify return message
        expected_message = "Journal entry created in 'Personal': 'Test Journal Entry' on 2025-07-19 - This is a test journal entry."
        assert result == expected_message

    @patch("src.providers.caldav.journal_service.find_calendar_by_name")
    @patch("src.providers.caldav.journal_service.validate_journal_summary")
    @patch("src.providers.caldav.journal_service.validate_journal_description")
    @patch("src.providers.caldav.journal_service.validate_calendar_name")
    @patch("src.providers.caldav.journal_service.datetime")
    def test_journal_creation_with_today(
        self,
        mock_datetime,
        mock_validate_calendar,
        mock_validate_description,
        mock_validate_summary,
        mock_find_calendar,
        journal_service,
        mock_calendar_found,
    ):
        """Test journal creation defaults to today when no date provided."""
        # Setup
        mock_find_calendar.return_value = mock_calendar_found

        # Mock datetime.now() to return a fixed date
        fixed_now = datetime(2025, 7, 19, 15, 30, 0, tzinfo=timezone.utc)
        mock_datetime.now.return_value = fixed_now
        mock_datetime.fromisoformat.return_value = datetime(2025, 7, 19)

        # Execute
        result = journal_service.create_journal(
            calendar_name="Personal",
            summary="Today's Journal",
            description="Auto-dated journal entry.",
            date=None,
        )

        # Verify datetime.now was called with UTC timezone
        mock_datetime.now.assert_called_once_with(timezone.utc)

        # Verify datetime.fromisoformat was called with today's date
        mock_datetime.fromisoformat.assert_called_once_with("2025-07-19")

        # Verify save_journal was called
        mock_calendar_found.save_journal.assert_called_once()
        call_args = mock_calendar_found.save_journal.call_args
        assert call_args[1]["summary"] == "Today's Journal"
        assert call_args[1]["description"] == "Auto-dated journal entry."

        # Verify return message indicates "today"
        expected_message = "Journal entry created in 'Personal': 'Today's Journal' (today) - Auto-dated journal entry."
        assert result == expected_message

    @patch("src.providers.caldav.journal_service.find_calendar_by_name")
    @patch("src.providers.caldav.journal_service.validate_journal_summary")
    @patch("src.providers.caldav.journal_service.validate_journal_description")
    @patch("src.providers.caldav.journal_service.validate_calendar_name")
    def test_journal_creation_different_timezones(
        self,
        mock_validate_calendar,
        mock_validate_description,
        mock_validate_summary,
        mock_find_calendar,
        journal_service,
        mock_calendar_found,
    ):
        """Test journal creation handles timezone-aware dates correctly."""
        # Setup
        mock_find_calendar.return_value = mock_calendar_found

        # Test various date formats
        # With timezone fix, datetime should be timezone-aware
        from zoneinfo import ZoneInfo

        test_cases = [
            ("2025-07-19", datetime(2025, 7, 19, tzinfo=ZoneInfo("UTC"))),
            ("2025-12-31", datetime(2025, 12, 31, tzinfo=ZoneInfo("UTC"))),
            ("2025-01-01", datetime(2025, 1, 1, tzinfo=ZoneInfo("UTC"))),
        ]

        for test_date, expected_dtstart in test_cases:
            # Reset mock for each test case
            mock_calendar_found.save_journal.reset_mock()

            # Execute
            result = journal_service.create_journal(
                calendar_name="Personal",
                summary=f"Entry for {test_date}",
                description=f"Journal entry for {test_date}.",
                date=test_date,
            )

            # Verify save_journal was called with correct dtstart
            mock_calendar_found.save_journal.assert_called_once_with(
                summary=f"Entry for {test_date}",
                description=f"Journal entry for {test_date}.",
                dtstart=expected_dtstart,
            )

            # Verify return message format
            expected_message = f"Journal entry created in 'Personal': 'Entry for {test_date}' on {test_date} - Journal entry for {test_date}."
            assert result == expected_message

    @patch("src.providers.caldav.journal_service.find_calendar_by_name")
    @patch("src.providers.caldav.journal_service.validate_journal_summary")
    @patch("src.providers.caldav.journal_service.validate_journal_description")
    @patch("src.providers.caldav.journal_service.validate_calendar_name")
    @patch("src.providers.caldav.journal_service.datetime")
    def test_journal_creation_without_date(
        self,
        mock_datetime,
        mock_validate_calendar,
        mock_validate_description,
        mock_validate_summary,
        mock_find_calendar,
        journal_service,
        mock_calendar_found,
    ):
        """Test journal creation behavior when date parameter omitted entirely."""
        # Setup
        mock_find_calendar.return_value = mock_calendar_found

        # Mock datetime functions
        fixed_now = datetime(2025, 7, 19, 10, 15, 30, tzinfo=timezone.utc)
        mock_datetime.now.return_value = fixed_now
        mock_datetime.fromisoformat.return_value = datetime(2025, 7, 19)

        # Execute - call without date parameter at all
        result = journal_service.create_journal(
            calendar_name="Personal",
            summary="Undated Journal",
            description="Journal without explicit date.",
        )

        # Verify datetime.now was called to get current time
        mock_datetime.now.assert_called_once_with(timezone.utc)

        # Verify fromisoformat was called with auto-generated date
        mock_datetime.fromisoformat.assert_called_once_with("2025-07-19")

        # Verify save_journal was called
        mock_calendar_found.save_journal.assert_called_once()
        call_args = mock_calendar_found.save_journal.call_args
        assert call_args[1]["summary"] == "Undated Journal"
        assert call_args[1]["description"] == "Journal without explicit date."

        # Verify return message indicates auto-generated date
        expected_message = "Journal entry created in 'Personal': 'Undated Journal' (today) - Journal without explicit date."
        assert result == expected_message


class TestCalDavJournalServiceErrorHandling:
    """Tests for error handling in CalDavJournalService.create_journal method."""

    @patch("src.providers.caldav.journal_service.validate_journal_summary")
    def test_invalid_summary_raises_validation_error(
        self, mock_validate_summary, journal_service
    ):
        """Test that invalid summary raises ValidationError."""
        # Setup
        mock_validate_summary.side_effect = ValueError("Summary cannot be empty")

        # Execute & Verify
        with pytest.raises(ValueError, match="Summary cannot be empty"):
            journal_service.create_journal(
                calendar_name="Personal", summary="", description="Valid description."
            )

    @patch("src.providers.caldav.journal_service.validate_journal_description")
    @patch("src.providers.caldav.journal_service.validate_journal_summary")
    def test_invalid_description_raises_validation_error(
        self, mock_validate_summary, mock_validate_description, journal_service
    ):
        """Test that invalid description raises ValidationError."""
        # Setup
        mock_validate_description.side_effect = ValueError(
            "Description cannot be empty"
        )

        # Execute & Verify
        with pytest.raises(ValueError, match="Description cannot be empty"):
            journal_service.create_journal(
                calendar_name="Personal", summary="Valid summary", description=""
            )

    @patch("src.providers.caldav.journal_service.find_calendar_by_name")
    @patch("src.providers.caldav.journal_service.validate_journal_summary")
    @patch("src.providers.caldav.journal_service.validate_journal_description")
    @patch("src.providers.caldav.journal_service.validate_calendar_name")
    def test_invalid_calendar_raises_value_error(
        self,
        mock_validate_calendar,
        mock_validate_description,
        mock_validate_summary,
        mock_find_calendar,
        journal_service,
    ):
        """Test that non-existent calendar raises ValueError."""
        # Setup
        mock_find_calendar.side_effect = ValueError("Calendar 'NonExistent' not found")

        # Execute & Verify
        with pytest.raises(ValueError, match="Calendar 'NonExistent' not found"):
            journal_service.create_journal(
                calendar_name="NonExistent",
                summary="Valid summary",
                description="Valid description.",
            )

    @patch("src.providers.caldav.journal_service.find_calendar_by_name")
    @patch("src.providers.caldav.journal_service.validate_journal_summary")
    @patch("src.providers.caldav.journal_service.validate_journal_description")
    @patch("src.providers.caldav.journal_service.validate_calendar_name")
    def test_invalid_date_format_raises_value_error(
        self,
        mock_validate_calendar,
        mock_validate_description,
        mock_validate_summary,
        mock_find_calendar,
        journal_service,
        mock_calendar_found,
    ):
        """Test that invalid date format raises ValueError."""
        # Setup
        mock_find_calendar.return_value = mock_calendar_found

        # Execute & Verify
        with pytest.raises(ValueError, match="Invalid date format"):
            journal_service.create_journal(
                calendar_name="Personal",
                summary="Valid summary",
                description="Valid description.",
                date="invalid-date-format",
            )

    @patch("src.providers.caldav.journal_service.find_calendar_by_name")
    @patch("src.providers.caldav.journal_service.validate_journal_summary")
    @patch("src.providers.caldav.journal_service.validate_journal_description")
    @patch("src.providers.caldav.journal_service.validate_calendar_name")
    def test_caldav_error_raises_runtime_error(
        self,
        mock_validate_calendar,
        mock_validate_description,
        mock_validate_summary,
        mock_find_calendar,
        journal_service,
        mock_calendar_found,
    ):
        """Test that CalDAV save errors raise RuntimeError."""
        # Setup
        mock_find_calendar.return_value = mock_calendar_found
        mock_calendar_found.save_journal.side_effect = Exception("CalDAV server error")

        # Execute & Verify
        with pytest.raises(RuntimeError, match="Failed to create journal"):
            journal_service.create_journal(
                calendar_name="Personal",
                summary="Valid summary",
                description="Valid description.",
                date="2025-07-19",
            )


class TestCalDavJournalServiceIntegration:
    """Integration tests for CalDavJournalService."""

    def test_uses_shared_caldav_base(self, mock_caldav_base):
        """Test that service uses the injected CalDavBase instance."""
        service = CalDavJournalService(mock_caldav_base)

        # Verify the service stores the base reference
        assert service.caldav_base is mock_caldav_base

        # Verify calendars property delegates to base
        assert service.calendars is mock_caldav_base.calendars

    @patch("src.providers.caldav.journal_service.find_calendar_by_name")
    @patch("src.providers.caldav.journal_service.validate_journal_summary")
    @patch("src.providers.caldav.journal_service.validate_journal_description")
    @patch("src.providers.caldav.journal_service.validate_calendar_name")
    def test_calendar_cache_integration(
        self,
        mock_validate_calendar,
        mock_validate_description,
        mock_validate_summary,
        mock_find_calendar,
        journal_service,
        mock_calendar_found,
    ):
        """Test that calendar lookup uses shared calendar cache."""
        # Setup
        mock_find_calendar.return_value = mock_calendar_found

        # Execute
        journal_service.create_journal(
            calendar_name="Personal",
            summary="Test",
            description="Test description.",
            date="2025-07-19",
        )

        # Verify find_calendar_by_name was called with the shared calendars
        mock_find_calendar.assert_called_once_with(
            journal_service.calendars, "Personal"
        )

    def test_edge_case_special_characters(self, journal_service, mock_calendar_found):
        """Test handling of special characters in journal content."""
        with (
            patch(
                "src.providers.caldav.journal_service.find_calendar_by_name"
            ) as mock_find,
            patch("src.providers.caldav.journal_service.validate_journal_summary"),
            patch("src.providers.caldav.journal_service.validate_journal_description"),
            patch("src.providers.caldav.journal_service.validate_calendar_name"),
        ):
            mock_find.return_value = mock_calendar_found

            # Test with unicode and emojis
            result = journal_service.create_journal(
                calendar_name="Personal",
                summary="Journal with émojis 🎉",
                description="Content with special chars: ñáéíóú @#$%",
                date="2025-07-19",
            )

            # Verify the call was made with special characters intact
            mock_calendar_found.save_journal.assert_called_once()
            call_args = mock_calendar_found.save_journal.call_args
            assert "émojis 🎉" in call_args[1]["summary"]
            assert "ñáéíóú" in call_args[1]["description"]

            # Verify return message preserves special characters
            assert "émojis 🎉" in result
            assert "ñáéíóú" in result
