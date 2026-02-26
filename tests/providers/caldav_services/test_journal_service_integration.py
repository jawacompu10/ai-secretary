"""
Integration tests for src.providers.caldav.journal_service module.
Tests against real CalDAV server without mocking.
"""

import pytest
from datetime import datetime, timezone
from src.providers.caldav_provider import create_calendar_provider
from src.core.models.journal import JournalDelete


TEST_CALENDAR_NAME = "Calendar For Automated Tests"


@pytest.fixture(scope="class")
def caldav_service():
    """Create a real CalDAV service instance."""
    try:
        service = create_calendar_provider()
        return service
    except Exception as e:
        pytest.skip(f"CalDAV server not available: {e}")


@pytest.fixture(scope="class", autouse=True)
def setup_test_calendar(caldav_service):
    """Ensure test calendar exists before running tests."""
    try:
        # Check if test calendar already exists
        calendar_names = caldav_service.get_all_calendar_names()

        if TEST_CALENDAR_NAME not in calendar_names:
            # Create the test calendar
            caldav_service.create_new_calendar(TEST_CALENDAR_NAME)
            print(f"Created test calendar: {TEST_CALENDAR_NAME}")
        else:
            print(f"Using existing test calendar: {TEST_CALENDAR_NAME}")

    except Exception as e:
        pytest.skip(f"Unable to setup test calendar: {e}")


@pytest.fixture(autouse=True)
def cleanup_test_journals(caldav_service):
    """Clean up test journals after each test."""
    # Let the test run first
    yield

    try:
        # Get all journals from test calendar
        journals = caldav_service.get_journals(calendar_name=TEST_CALENDAR_NAME)

        # Delete any journals created during testing
        for journal in journals:
            if journal.summary.startswith("Test Integration"):
                try:
                    journal_delete = JournalDelete(
                        calendar_name=TEST_CALENDAR_NAME,
                        summary=journal.summary,
                        date=journal.date_local,
                    )
                    caldav_service.delete_journal(journal_delete)
                except Exception as e:
                    print(
                        f"Warning: Could not delete test journal '{journal.summary}': {e}"
                    )

    except Exception as e:
        print(f"Warning: Could not clean up test journals: {e}")


class TestCalDavJournalServiceIntegration:
    """Integration tests for CalDavJournalService with real CalDAV server."""

    def test_integration_journal_creation_with_explicit_date(self, caldav_service):
        """Test journal creation with specific date and verify via get_journals."""
        # Test data
        test_date = "2025-07-20"
        test_summary = "Test Integration Journal - Explicit Date"
        test_description = (
            "This journal was created with an explicit date for integration testing."
        )

        # Create the journal
        result = caldav_service.create_journal(
            calendar_name=TEST_CALENDAR_NAME,
            summary=test_summary,
            description=test_description,
            date=test_date,
        )

        # Verify creation success message
        assert "Journal entry created" in result
        assert TEST_CALENDAR_NAME in result
        assert test_summary in result
        assert test_date in result

        # Retrieve and verify the journal
        journals = caldav_service.get_journals(calendar_name=TEST_CALENDAR_NAME)

        # Find our test journal
        created_journal = None
        for journal in journals:
            if journal.summary == test_summary:
                created_journal = journal
                break

        # Verify journal was created and retrieved correctly
        assert (
            created_journal is not None
        ), f"Journal '{test_summary}' not found in retrieved journals"
        assert created_journal.summary == test_summary

        # Handle potential line breaks that CalDAV servers may add
        normalized_description = created_journal.description.replace("\n", " ").strip()
        assert normalized_description == test_description
        assert created_journal.calendar_name == TEST_CALENDAR_NAME

        # Verify date was stored correctly
        assert created_journal.date_utc is not None
        # Date should be exactly July 20, 2025
        assert created_journal.date_utc.year == 2025
        assert created_journal.date_utc.month == 7
        assert created_journal.date_utc.day == 20

        # Verify local date display
        assert created_journal.date_local is not None
        assert "2025-07-20" in created_journal.date_local

    def test_integration_journal_creation_with_today(self, caldav_service):
        """Test journal creation defaults to today when no date provided."""
        # Test data
        test_summary = "Test Integration Journal - Today"
        test_description = "This journal should default to today's date."

        # Get today's date for comparison
        today = datetime.now(timezone.utc).date()

        # Create the journal without explicit date
        result = caldav_service.create_journal(
            calendar_name=TEST_CALENDAR_NAME,
            summary=test_summary,
            description=test_description,
            date=None,
        )

        # Verify creation success message indicates "today"
        assert "Journal entry created" in result
        assert TEST_CALENDAR_NAME in result
        assert test_summary in result
        assert "(today)" in result

        # Retrieve and verify the journal
        journals = caldav_service.get_journals(calendar_name=TEST_CALENDAR_NAME)

        # Find our test journal
        created_journal = None
        for journal in journals:
            if journal.summary == test_summary:
                created_journal = journal
                break

        # Verify journal was created correctly
        assert created_journal is not None
        assert created_journal.summary == test_summary

        # Handle potential line breaks that CalDAV servers may add
        normalized_description = created_journal.description.replace("\n", " ").strip()
        assert normalized_description == test_description

        # Verify date is today
        assert created_journal.date_utc is not None
        journal_date = created_journal.date_utc.date()
        assert journal_date == today, f"Expected {today}, got {journal_date}"

    def test_integration_journal_creation_different_timezones(self, caldav_service):
        """Test journal creation handles different dates correctly."""
        test_cases = [
            ("2025-01-01", "New Year's Day"),
            ("2025-12-31", "New Year's Eve"),
            ("2025-02-29", "Leap Year Day"),  # 2025 is not a leap year, but let's test
            ("2025-06-15", "Mid-year Date"),
        ]

        created_journals = []

        for test_date, description in test_cases:
            test_summary = f"Test Integration Journal - {description}"
            test_description = f"Journal created for {description} on {test_date}."

            # Skip leap year test for non-leap years
            if test_date == "2025-02-29":
                # 2025 is not a leap year, so skip this test
                continue

            # Create the journal
            result = caldav_service.create_journal(
                calendar_name=TEST_CALENDAR_NAME,
                summary=test_summary,
                description=test_description,
                date=test_date,
            )

            # Verify creation success
            assert "Journal entry created" in result
            assert test_date in result

            created_journals.append((test_summary, test_date, test_description))

        # Retrieve all journals and verify each one
        journals = caldav_service.get_journals(calendar_name=TEST_CALENDAR_NAME)

        for test_summary, test_date, test_description in created_journals:
            # Find the journal
            found_journal = None
            for journal in journals:
                if journal.summary == test_summary:
                    found_journal = journal
                    break

            # Verify journal exists and has correct data
            assert found_journal is not None, f"Journal '{test_summary}' not found"

            # Handle potential line breaks that CalDAV servers may add
            normalized_description = found_journal.description.replace(
                "\n", " "
            ).strip()
            assert normalized_description == test_description

            # Parse expected date
            expected_date = datetime.fromisoformat(test_date).date()
            actual_date = found_journal.date_utc.date()
            assert (
                actual_date == expected_date
            ), f"Expected {expected_date}, got {actual_date}"

    def test_integration_journal_creation_without_date(self, caldav_service):
        """Test journal creation when date parameter is completely omitted."""
        # Test data
        test_summary = "Test Integration Journal - No Date Parameter"
        test_description = "This journal was created without any date parameter."

        # Get today's date for comparison
        today = datetime.now(timezone.utc).date()

        # Create the journal without date parameter
        result = caldav_service.create_journal(
            calendar_name=TEST_CALENDAR_NAME,
            summary=test_summary,
            description=test_description,
        )

        # Verify creation success message
        assert "Journal entry created" in result
        assert test_summary in result
        assert "(today)" in result

        # Retrieve and verify the journal
        journals = caldav_service.get_journals(calendar_name=TEST_CALENDAR_NAME)

        # Find our test journal
        created_journal = None
        for journal in journals:
            if journal.summary == test_summary:
                created_journal = journal
                break

        # Verify journal was created correctly
        assert created_journal is not None
        assert created_journal.summary == test_summary

        # Handle potential line breaks that CalDAV servers may add
        normalized_description = created_journal.description.replace("\n", " ").strip()
        assert normalized_description == test_description

        # Verify date defaults to today
        assert created_journal.date_utc is not None
        journal_date = created_journal.date_utc.date()
        assert journal_date == today, f"Expected {today}, got {journal_date}"

    def test_get_journals_by_calendar(self, caldav_service):
        """Test retrieving journals filtered by calendar name."""
        # Create a test journal
        test_summary = "Test Integration Journal - Calendar Filter"
        test_description = "Testing calendar-specific journal retrieval."

        caldav_service.create_journal(
            calendar_name=TEST_CALENDAR_NAME,
            summary=test_summary,
            description=test_description,
            date="2025-07-21",
        )

        # Retrieve journals from test calendar only
        test_calendar_journals = caldav_service.get_journals(
            calendar_name=TEST_CALENDAR_NAME
        )

        # Verify we get journals and they're all from the test calendar
        assert len(test_calendar_journals) > 0
        for journal in test_calendar_journals:
            assert journal.calendar_name == TEST_CALENDAR_NAME

        # Verify our test journal is in the results
        found = any(j.summary == test_summary for j in test_calendar_journals)
        assert (
            found
        ), f"Test journal '{test_summary}' not found in calendar-filtered results"

    def test_get_journals_by_date(self, caldav_service):
        """Test retrieving journals filtered by specific date."""
        # Create a journal with specific date
        test_date = "2025-07-22"
        test_summary = "Test Integration Journal - Date Filter"
        test_description = "Testing date-specific journal retrieval."

        caldav_service.create_journal(
            calendar_name=TEST_CALENDAR_NAME,
            summary=test_summary,
            description=test_description,
            date=test_date,
        )

        # Retrieve journals for that specific date
        date_filtered_journals = caldav_service.get_journals(
            calendar_name=TEST_CALENDAR_NAME, date=test_date
        )

        # Verify we get journals for the specified date
        assert len(date_filtered_journals) > 0

        # Verify our test journal is in the results
        found_journal = None
        for journal in date_filtered_journals:
            if journal.summary == test_summary:
                found_journal = journal
                break

        assert found_journal is not None
        assert found_journal.description == test_description

        # Verify the date matches
        journal_date = found_journal.date_utc.date()
        expected_date = datetime.fromisoformat(test_date).date()
        assert journal_date == expected_date

    def test_journal_roundtrip_verification(self, caldav_service):
        """Test complete journal roundtrip: create → retrieve → verify all fields."""
        # Test data with special characters
        test_summary = "Test Integration Journal - Roundtrip 🎉"
        test_description = "Testing roundtrip with spëcial chärs and émojis! @#$%^&*()"
        test_date = "2025-07-23"

        # Create the journal
        create_result = caldav_service.create_journal(
            calendar_name=TEST_CALENDAR_NAME,
            summary=test_summary,
            description=test_description,
            date=test_date,
        )

        # Verify creation message
        assert test_summary in create_result
        assert test_description in create_result
        assert test_date in create_result

        # Retrieve and verify
        journals = caldav_service.get_journals(calendar_name=TEST_CALENDAR_NAME)

        # Find our journal
        found_journal = None
        for journal in journals:
            if journal.summary == test_summary:
                found_journal = journal
                break

        # Comprehensive verification
        assert found_journal is not None, "Journal not found after creation"

        # Verify all fields match exactly
        assert found_journal.summary == test_summary, "Summary doesn't match"

        # Handle potential line breaks that CalDAV servers may add
        normalized_description = found_journal.description.replace("\n", " ").strip()
        assert normalized_description == test_description, "Description doesn't match"
        assert (
            found_journal.calendar_name == TEST_CALENDAR_NAME
        ), "Calendar name doesn't match"

        # Verify date handling
        assert found_journal.date_utc is not None, "date_utc is None"
        assert found_journal.date_local is not None, "date_local is None"

        # Verify date accuracy
        expected_date = datetime.fromisoformat(test_date).date()
        actual_date = found_journal.date_utc.date()
        assert (
            actual_date == expected_date
        ), f"Date mismatch: expected {expected_date}, got {actual_date}"

        # Verify special characters preserved
        assert "🎉" in found_journal.summary, "Emoji not preserved in summary"
        assert (
            "spëcial chärs" in found_journal.description
        ), "Special characters not preserved"
        assert (
            "émojis!" in found_journal.description
        ), "Accented characters not preserved"

    def test_real_caldav_error_handling(self, caldav_service):
        """Test error handling with real CalDAV server."""
        # Test invalid calendar name
        with pytest.raises(ValueError, match="not found"):
            caldav_service.create_journal(
                calendar_name="NonExistentCalendar",
                summary="Test Journal",
                description="This should fail.",
            )

        # Test invalid date format
        with pytest.raises(ValueError, match="Invalid date format"):
            caldav_service.create_journal(
                calendar_name=TEST_CALENDAR_NAME,
                summary="Test Journal",
                description="This should fail too.",
                date="invalid-date",
            )


class TestCalDavJournalServiceIntegrationAdvanced:
    """Advanced integration tests for journal service."""

    def test_multiple_journals_same_date(self, caldav_service):
        """Test creating multiple journals on the same date."""
        test_date = "2025-07-24"
        journals_data = [
            ("Morning Journal", "What happened in the morning"),
            ("Afternoon Journal", "What happened in the afternoon"),
            ("Evening Journal", "What happened in the evening"),
        ]

        # Create multiple journals on same date
        for summary, description in journals_data:
            full_summary = f"Test Integration Journal - {summary}"
            caldav_service.create_journal(
                calendar_name=TEST_CALENDAR_NAME,
                summary=full_summary,
                description=description,
                date=test_date,
            )

        # Retrieve journals for that date
        date_journals = caldav_service.get_journals(
            calendar_name=TEST_CALENDAR_NAME, date=test_date
        )

        # Verify all journals were created and retrieved
        found_summaries = [
            j.summary
            for j in date_journals
            if j.summary.startswith("Test Integration Journal")
        ]
        assert (
            len(found_summaries) >= 3
        ), f"Expected at least 3 journals, found {len(found_summaries)}"

        # Verify each journal exists
        for summary, description in journals_data:
            full_summary = f"Test Integration Journal - {summary}"
            found = any(
                j.summary == full_summary and j.description == description
                for j in date_journals
            )
            assert found, f"Journal '{full_summary}' not found"

    def test_journal_with_long_content(self, caldav_service):
        """Test journal creation with very long content."""
        test_summary = "Test Integration Journal - Long Content"

        # Create a long description (1000+ characters)
        long_description = "This is a very long journal entry. " * 50
        long_description += "\n\nWith multiple paragraphs and lots of content to test how the CalDAV server handles large text blocks."

        # Create the journal
        result = caldav_service.create_journal(
            calendar_name=TEST_CALENDAR_NAME,
            summary=test_summary,
            description=long_description,
            date="2025-07-25",
        )

        # Verify creation succeeded
        assert "Journal entry created" in result

        # Retrieve and verify
        journals = caldav_service.get_journals(calendar_name=TEST_CALENDAR_NAME)
        found_journal = None
        for journal in journals:
            if journal.summary == test_summary:
                found_journal = journal
                break

        # Verify long content was preserved
        assert found_journal is not None
        assert len(found_journal.description) > 1000, "Long description was truncated"

        # Check for key phrases in the description (no normalization needed with icalendar library)
        assert "multiple paragraphs" in found_journal.description, f"Key phrase not found in: {found_journal.description[-200:]}"
