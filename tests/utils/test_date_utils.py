"""
Tests for src.utils.date_utils module.
"""

import pytest
from datetime import datetime, date

from src.utils.date_utils import (
    parse_due_date,
    parse_date_range,
    parse_instance_date,
    validate_date_string,
)


class TestParseDueDate:
    """Tests for parse_due_date function."""

    def test_parse_valid_date(self):
        """Test parsing a valid ISO date string."""
        result = parse_due_date("2025-07-12")
        expected = date(2025, 7, 12)
        assert result == expected
        assert isinstance(result, date)

    def test_parse_none_input(self):
        """Test parsing None input returns None."""
        result = parse_due_date(None)
        assert result is None

    def test_parse_empty_string(self):
        """Test parsing empty string returns None."""
        result = parse_due_date("")
        assert result is None

    def test_parse_whitespace_string(self):
        """Test parsing whitespace-only string returns None."""
        result = parse_due_date("   ")
        assert result is None

    @pytest.mark.parametrize(
        "invalid_date",
        [
            "not-a-date",
            "2025-13-01",  # Invalid month
            "2025-07-32",  # Invalid day
            "25-07-12",  # Wrong format
            "2025/07/12",  # Wrong separator
            "2025-7-12",  # Missing leading zero
        ],
    )
    def test_parse_invalid_dates(self, invalid_date):
        """Test parsing invalid date strings raises ValueError."""
        with pytest.raises(ValueError, match="Invalid due date format"):
            parse_due_date(invalid_date)

    def test_parse_datetime_string(self):
        """Test parsing datetime string extracts date part."""
        result = parse_due_date("2025-07-12T14:30:00")
        expected = date(2025, 7, 12)
        assert result == expected


class TestParseDateRange:
    """Tests for parse_date_range function."""

    def test_parse_valid_date_range(self):
        """Test parsing valid start and end dates."""
        start_dt, end_dt = parse_date_range("2025-07-12", "2025-07-15")

        assert isinstance(start_dt, datetime)
        assert isinstance(end_dt, datetime)
        assert start_dt == datetime(2025, 7, 12)
        assert end_dt == datetime(2025, 7, 15)

    def test_parse_datetime_range(self):
        """Test parsing datetime strings."""
        start_dt, end_dt = parse_date_range(
            "2025-07-12T09:00:00", "2025-07-12T17:00:00"
        )

        assert start_dt == datetime(2025, 7, 12, 9, 0, 0)
        assert end_dt == datetime(2025, 7, 12, 17, 0, 0)

    def test_parse_invalid_start_date(self):
        """Test invalid start date raises ValueError."""
        with pytest.raises(ValueError, match="Invalid date format"):
            parse_date_range("invalid-date", "2025-07-15")

    def test_parse_invalid_end_date(self):
        """Test invalid end date raises ValueError."""
        with pytest.raises(ValueError, match="Invalid date format"):
            parse_date_range("2025-07-12", "invalid-date")

    def test_parse_both_invalid_dates(self):
        """Test both invalid dates raises ValueError."""
        with pytest.raises(ValueError, match="Invalid date format"):
            parse_date_range("invalid-start", "invalid-end")

    def test_parse_end_before_start_date(self):
        """Test that end date before start date raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            parse_date_range("2025-07-15", "2025-07-12")

        error_msg = str(exc_info.value)
        assert (
            "End date (2025-07-12) cannot be before start date (2025-07-15)"
            in error_msg
        )

    def test_parse_same_start_end_date(self):
        """Test that same start and end dates are allowed."""
        start_dt, end_dt = parse_date_range("2025-07-12", "2025-07-12")

        assert start_dt == end_dt
        assert start_dt == datetime(2025, 7, 12)

    def test_parse_end_before_start_with_times(self):
        """Test validation works with datetime strings."""
        # Same day but end time before start time
        with pytest.raises(ValueError) as exc_info:
            parse_date_range("2025-07-12T17:00:00", "2025-07-12T09:00:00")

        error_msg = str(exc_info.value)
        assert "cannot be before" in error_msg
        assert "2025-07-12T17:00:00" in error_msg
        assert "2025-07-12T09:00:00" in error_msg

    def test_parse_different_days_end_before_start(self):
        """Test validation works across different days."""
        with pytest.raises(ValueError) as exc_info:
            parse_date_range("2025-07-15T09:00:00", "2025-07-14T17:00:00")

        error_msg = str(exc_info.value)
        assert "cannot be before" in error_msg

    def test_error_message_preserves_original_input(self):
        """Test that error messages include the original input strings."""
        start_date = "2025-12-31"
        end_date = "2025-01-01"

        with pytest.raises(ValueError) as exc_info:
            parse_date_range(start_date, end_date)

        error_msg = str(exc_info.value)
        assert start_date in error_msg
        assert end_date in error_msg
        assert "cannot be before" in error_msg


class TestParseInstanceDate:
    """Tests for parse_instance_date function."""

    def test_parse_valid_date(self):
        """Test parsing valid ISO date string."""
        result = parse_instance_date("2025-07-12")
        expected = datetime(2025, 7, 12)
        assert result == expected
        assert isinstance(result, datetime)

    def test_parse_valid_datetime(self):
        """Test parsing valid ISO datetime string."""
        result = parse_instance_date("2025-07-12T14:30:00")
        expected = datetime(2025, 7, 12, 14, 30, 0)
        assert result == expected

    @pytest.mark.parametrize(
        "invalid_date",
        [
            "not-a-date",
            "2025-13-01",
            "2025-07-32",
            "25-07-12",
            "2025/07/12",
        ],
    )
    def test_parse_invalid_dates(self, invalid_date):
        """Test parsing invalid date strings raises ValueError."""
        with pytest.raises(ValueError, match="Invalid date format"):
            parse_instance_date(invalid_date)

    def test_error_message_includes_input(self):
        """Test error message includes the invalid input."""
        invalid_input = "bad-date-format"
        with pytest.raises(ValueError, match=f"Invalid date format: {invalid_input}"):
            parse_instance_date(invalid_input)


class TestValidateDateString:
    """Tests for validate_date_string function."""

    @pytest.mark.parametrize(
        "valid_date",
        [
            "2025-07-12",
            "2025-01-01",
            "2025-12-31",
            "2025-07-12T14:30:00",
            "2025-07-12T00:00:00",
            "2025-07-12T23:59:59",
        ],
    )
    def test_validate_valid_dates(self, valid_date):
        """Test validation returns True for valid dates."""
        assert validate_date_string(valid_date) is True

    @pytest.mark.parametrize(
        "invalid_date",
        [
            "not-a-date",
            "2025-13-01",  # Invalid month
            "2025-07-32",  # Invalid day
            "25-07-12",  # Wrong format
            "2025/07/12",  # Wrong separator
            "",  # Empty string
            "   ",  # Whitespace
        ],
    )
    def test_validate_invalid_dates(self, invalid_date):
        """Test validation returns False for invalid dates."""
        assert validate_date_string(invalid_date) is False

    def test_validate_edge_cases(self):
        """Test validation with edge cases."""
        # Leap year
        assert validate_date_string("2024-02-29") is True
        # Non-leap year
        assert validate_date_string("2025-02-29") is False

        # Start of year
        assert validate_date_string("2025-01-01") is True
        # End of year
        assert validate_date_string("2025-12-31") is True


class TestDateUtilsIntegration:
    """Integration tests for date utilities working together."""

    def test_parse_due_date_and_validate_consistency(self):
        """Test that parse_due_date and validate_date_string are consistent."""
        valid_dates = ["2025-07-12", "2025-01-01", "2025-12-31"]
        invalid_dates = ["not-a-date", "2025-13-01", "2025-07-32"]

        for valid_date in valid_dates:
            # If validate_date_string says it's valid, parse_due_date should work
            assert validate_date_string(valid_date) is True
            result = parse_due_date(valid_date)
            assert result is not None
            assert isinstance(result, date)

        for invalid_date in invalid_dates:
            # If validate_date_string says it's invalid, parse_due_date should raise
            assert validate_date_string(invalid_date) is False
            with pytest.raises(ValueError):
                parse_due_date(invalid_date)

    def test_round_trip_date_parsing(self):
        """Test that dates can be round-tripped through string representation."""
        original_date = date(2025, 7, 12)
        date_string = original_date.isoformat()
        parsed_date = parse_due_date(date_string)

        assert parsed_date == original_date

    def test_date_range_ordering(self):
        """Test that date range parsing preserves ordering."""
        start_dt, end_dt = parse_date_range("2025-07-12", "2025-07-15")
        assert start_dt < end_dt

        # Test same day
        start_dt, end_dt = parse_date_range("2025-07-12", "2025-07-12")
        assert start_dt == end_dt

        # Test that invalid ordering is rejected
        with pytest.raises(ValueError, match="cannot be before"):
            parse_date_range("2025-07-15", "2025-07-12")
