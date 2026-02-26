"""
Tests for src.utils.timezone_utils module.
"""

import pytest
from unittest.mock import patch, Mock
from datetime import datetime
from zoneinfo import ZoneInfo
import os

from src.utils.timezone_utils import (
    get_user_timezone,
    parse_datetime_to_utc,
    utc_to_user_timezone,
    format_datetime_for_user,
    validate_datetime_string,
)


class TestGetUserTimezone:
    """Tests for get_user_timezone function."""

    @patch("src.utils.timezone_utils.datetime")
    def test_get_system_timezone(self, mock_datetime):
        """Test getting timezone from system datetime."""
        # Mock system timezone
        mock_tz = ZoneInfo("America/New_York")
        mock_dt = Mock()
        mock_dt.astimezone.return_value.tzinfo = mock_tz
        mock_datetime.now.return_value = mock_dt

        result = get_user_timezone()
        assert str(result) == str(mock_tz)

    @patch.dict(os.environ, {"TZ": "Europe/London"})
    @patch("src.utils.timezone_utils.datetime")
    def test_fallback_to_tz_environment_variable(self, mock_datetime):
        """Test fallback to TZ environment variable when system timezone fails."""
        # Mock system timezone to raise exception
        mock_datetime.now.side_effect = Exception("System timezone error")

        result = get_user_timezone()
        assert str(result) == "Europe/London"

    @patch.dict(os.environ, {}, clear=True)  # Clear TZ env var
    @patch("src.utils.timezone_utils.datetime")
    def test_final_fallback_to_utc(self, mock_datetime):
        """Test final fallback to UTC when everything fails."""
        # Mock both system timezone and ZoneInfo to fail
        mock_datetime.now.side_effect = Exception("System timezone error")

        with patch("src.utils.timezone_utils.ZoneInfo") as mock_zoneinfo:
            # First call (system timezone) raises exception
            # Second call (TZ env var) raises exception
            # Third call (UTC fallback) succeeds
            mock_zoneinfo.side_effect = [Exception("TZ error"), ZoneInfo("UTC")]

            result = get_user_timezone()
            assert str(result) == "UTC"

    @patch.dict(os.environ, {"TZ": "Invalid/Timezone"})
    @patch("src.utils.timezone_utils.datetime")
    def test_invalid_tz_environment_variable(self, mock_datetime):
        """Test handling of invalid TZ environment variable."""
        mock_datetime.now.side_effect = Exception("System timezone error")

        result = get_user_timezone()
        # Should fallback to UTC when TZ env var is invalid
        assert str(result) == "UTC"


class TestParseDatetimeToUtc:
    """Tests for parse_datetime_to_utc function."""

    def test_parse_utc_datetime_with_z_suffix(self):
        """Test parsing UTC datetime with Z suffix."""
        result = parse_datetime_to_utc("2025-07-12T14:30:00Z")

        expected = datetime(2025, 7, 12, 14, 30, 0, tzinfo=ZoneInfo("UTC"))
        assert result == expected
        assert str(result.tzinfo) == "UTC"

    def test_parse_utc_datetime_with_offset(self):
        """Test parsing UTC datetime with +00:00 offset."""
        result = parse_datetime_to_utc("2025-07-12T14:30:00+00:00")

        expected = datetime(2025, 7, 12, 14, 30, 0, tzinfo=ZoneInfo("UTC"))
        assert result == expected

    def test_parse_timezone_aware_datetime(self):
        """Test parsing timezone-aware datetime and converting to UTC."""
        # EST is UTC-5 in winter
        result = parse_datetime_to_utc("2025-01-12T09:30:00-05:00")

        # 9:30 AM EST = 2:30 PM UTC
        expected = datetime(2025, 1, 12, 14, 30, 0, tzinfo=ZoneInfo("UTC"))
        assert result == expected

    def test_parse_different_timezone_offsets(self):
        """Test parsing various timezone offsets."""
        test_cases = [
            (
                "2025-07-12T12:00:00+02:00",
                datetime(2025, 7, 12, 10, 0, 0, tzinfo=ZoneInfo("UTC")),
            ),  # CEST
            (
                "2025-07-12T12:00:00-08:00",
                datetime(2025, 7, 12, 20, 0, 0, tzinfo=ZoneInfo("UTC")),
            ),  # PST
            (
                "2025-07-12T12:00:00+05:30",
                datetime(2025, 7, 12, 6, 30, 0, tzinfo=ZoneInfo("UTC")),
            ),  # IST
        ]

        for input_dt, expected in test_cases:
            result = parse_datetime_to_utc(input_dt)
            assert result == expected

    def test_parse_naive_datetime_raises_error(self):
        """Test that naive datetime (no timezone) raises ValueError."""
        with pytest.raises(
            ValueError, match="Datetime must include timezone information"
        ):
            parse_datetime_to_utc("2025-07-12T14:30:00")

    def test_parse_invalid_datetime_format(self):
        """Test that invalid datetime format raises ValueError."""
        invalid_formats = [
            "not-a-datetime",
            "2025-07-12",  # Date only
            "14:30:00",  # Time only
            "2025-13-12T14:30:00Z",  # Invalid month
            "2025-07-32T14:30:00Z",  # Invalid day
        ]

        for invalid_dt in invalid_formats:
            with pytest.raises(ValueError):
                parse_datetime_to_utc(invalid_dt)

    def test_error_message_includes_input(self):
        """Test that error message includes the invalid input."""
        invalid_input = "bad-datetime"
        with pytest.raises(ValueError) as exc_info:
            parse_datetime_to_utc(invalid_input)

        assert invalid_input in str(exc_info.value)
        assert "Expected format" in str(exc_info.value)


class TestUtcToUserTimezone:
    """Tests for utc_to_user_timezone function."""

    @patch("src.utils.timezone_utils.get_user_timezone")
    def test_convert_utc_to_user_timezone(self, mock_get_timezone):
        """Test converting UTC datetime to user timezone."""
        mock_get_timezone.return_value = ZoneInfo("America/New_York")

        utc_dt = datetime(2025, 7, 12, 18, 30, 0, tzinfo=ZoneInfo("UTC"))
        result = utc_to_user_timezone(utc_dt)

        # 6:30 PM UTC = 2:30 PM EDT (summer time)
        expected = datetime(2025, 7, 12, 14, 30, 0, tzinfo=ZoneInfo("America/New_York"))
        assert result.replace(tzinfo=None) == expected.replace(
            tzinfo=None
        )  # Compare without timezone info
        assert str(result.tzinfo) == "America/New_York"

    @patch("src.utils.timezone_utils.get_user_timezone")
    def test_convert_naive_utc_datetime(self, mock_get_timezone):
        """Test converting naive datetime (assumed UTC) to user timezone."""
        mock_get_timezone.return_value = ZoneInfo("Europe/London")

        # Naive datetime (no timezone info)
        naive_dt = datetime(2025, 1, 12, 12, 0, 0)
        result = utc_to_user_timezone(naive_dt)

        # Should assume it's UTC and convert to London time (GMT in winter)
        expected = datetime(2025, 1, 12, 12, 0, 0, tzinfo=ZoneInfo("Europe/London"))
        assert result.replace(tzinfo=None) == expected.replace(tzinfo=None)

    @patch("src.utils.timezone_utils.get_user_timezone")
    def test_different_user_timezones(self, mock_get_timezone):
        """Test conversion to different user timezones."""
        utc_dt = datetime(2025, 7, 12, 12, 0, 0, tzinfo=ZoneInfo("UTC"))

        timezone_tests = [
            (ZoneInfo("UTC"), 12),  # UTC: no change
            (ZoneInfo("Asia/Tokyo"), 21),  # JST: UTC+9
            (ZoneInfo("Australia/Sydney"), 22),  # AEST: UTC+10 (summer)
        ]

        for tz, expected_hour in timezone_tests:
            mock_get_timezone.return_value = tz
            result = utc_to_user_timezone(utc_dt)
            assert result.hour == expected_hour
            assert str(result.tzinfo) == str(tz)


class TestFormatDatetimeForUser:
    """Tests for format_datetime_for_user function."""

    @patch("src.utils.timezone_utils.utc_to_user_timezone")
    def test_format_valid_datetime(self, mock_convert):
        """Test formatting valid UTC datetime for user."""
        # Mock the conversion
        user_dt = datetime(2025, 7, 12, 14, 30, 0, tzinfo=ZoneInfo("America/New_York"))
        mock_convert.return_value = user_dt

        utc_dt = datetime(2025, 7, 12, 18, 30, 0, tzinfo=ZoneInfo("UTC"))
        result = format_datetime_for_user(utc_dt)

        # Should return ISO format of converted datetime
        expected = user_dt.isoformat()
        assert result == expected

        # Verify conversion was called
        mock_convert.assert_called_once_with(utc_dt)

    def test_format_none_datetime(self):
        """Test formatting None datetime returns None."""
        result = format_datetime_for_user(None)
        assert result is None

    @patch("src.utils.timezone_utils.utc_to_user_timezone")
    def test_format_datetime_iso_format(self, mock_convert):
        """Test that formatted datetime is in ISO format."""
        user_dt = datetime(2025, 7, 12, 14, 30, 45, tzinfo=ZoneInfo("Europe/London"))
        mock_convert.return_value = user_dt

        utc_dt = datetime(2025, 7, 12, 13, 30, 45, tzinfo=ZoneInfo("UTC"))
        result = format_datetime_for_user(utc_dt)

        # Should be ISO format with timezone info
        assert "2025-07-12T14:30:45" in result
        assert "Europe/London" in result or "+01:00" in result  # Timezone info present


class TestValidateDatetimeString:
    """Tests for validate_datetime_string function."""

    def test_validate_valid_datetime_strings(self):
        """Test validation of valid timezone-aware datetime strings."""
        valid_datetimes = [
            "2025-07-12T14:30:00Z",
            "2025-07-12T14:30:00+00:00",
            "2025-07-12T14:30:00-05:00",
            "2025-01-01T00:00:00+02:30",
            "2025-12-31T23:59:59-11:00",
        ]

        for valid_dt in valid_datetimes:
            assert validate_datetime_string(valid_dt) is True

    def test_validate_invalid_datetime_strings(self):
        """Test validation of invalid datetime strings."""
        invalid_datetimes = [
            "2025-07-12T14:30:00",  # No timezone
            "not-a-datetime",
            "2025-07-12",  # Date only
            "14:30:00Z",  # Time only
            "2025-13-01T12:00:00Z",  # Invalid month
            "2025-07-32T12:00:00Z",  # Invalid day
            "",  # Empty string
            "2025-07-12T25:00:00Z",  # Invalid hour
        ]

        for invalid_dt in invalid_datetimes:
            assert validate_datetime_string(invalid_dt) is False

    def test_validate_edge_cases(self):
        """Test validation of edge case datetime strings."""
        # Leap year February 29
        assert validate_datetime_string("2024-02-29T12:00:00Z") is True
        # Non-leap year February 29
        assert validate_datetime_string("2025-02-29T12:00:00Z") is False

        # Extreme timezone offsets
        assert validate_datetime_string("2025-07-12T12:00:00+14:00") is True  # Kiribati
        assert (
            validate_datetime_string("2025-07-12T12:00:00-12:00") is True
        )  # Baker Island


class TestTimezoneUtilsIntegration:
    """Integration tests for timezone utilities working together."""

    @patch("src.utils.timezone_utils.get_user_timezone")
    def test_round_trip_datetime_conversion(self, mock_get_timezone):
        """Test round-trip conversion: parse -> format -> parse."""
        mock_get_timezone.return_value = ZoneInfo("America/Chicago")

        # Start with a timezone-aware datetime string
        original = "2025-07-12T14:30:00-05:00"

        # Parse to UTC
        utc_dt = parse_datetime_to_utc(original)

        # Format for user (converts to Chicago time)
        formatted = format_datetime_for_user(utc_dt)

        # Should be valid for parsing again
        assert validate_datetime_string(formatted) is True

        # Parse again should give us the same UTC time
        reparsed_utc = parse_datetime_to_utc(formatted)
        assert reparsed_utc == utc_dt

    def test_consistency_between_validation_and_parsing(self):
        """Test that validation and parsing are consistent."""
        test_strings = [
            "2025-07-12T14:30:00Z",
            "2025-07-12T14:30:00+02:00",
            "2025-07-12T14:30:00",  # Invalid (no timezone)
            "invalid-datetime",
        ]

        for test_string in test_strings:
            is_valid = validate_datetime_string(test_string)

            if is_valid:
                # If validation says it's valid, parsing should work
                try:
                    result = parse_datetime_to_utc(test_string)
                    assert result is not None
                except ValueError:
                    pytest.fail(
                        f"Validation said '{test_string}' is valid but parsing failed"
                    )
            else:
                # If validation says it's invalid, parsing should raise ValueError
                with pytest.raises(ValueError):
                    parse_datetime_to_utc(test_string)

    @patch("src.utils.timezone_utils.get_user_timezone")
    def test_timezone_conversion_preserves_moment_in_time(self, mock_get_timezone):
        """Test that timezone conversions preserve the same moment in time."""
        mock_get_timezone.return_value = ZoneInfo("Pacific/Auckland")  # UTC+12/+13

        # A specific moment in time
        utc_moment = datetime(2025, 7, 12, 12, 0, 0, tzinfo=ZoneInfo("UTC"))

        # Convert to user timezone
        user_moment = utc_to_user_timezone(utc_moment)

        # Convert back to UTC should give the same moment
        converted_back = user_moment.astimezone(ZoneInfo("UTC"))

        assert converted_back == utc_moment

    def test_error_handling_consistency(self):
        """Test that error handling is consistent across functions."""
        # All functions should handle None gracefully or raise appropriate errors
        assert format_datetime_for_user(None) is None

        # Invalid inputs should raise ValueError with descriptive messages
        with pytest.raises(ValueError, match="timezone"):
            parse_datetime_to_utc("2025-07-12T14:30:00")  # No timezone

        # Validation should never raise exceptions
        assert validate_datetime_string("invalid") is False
        assert validate_datetime_string("") is False
        assert validate_datetime_string("2025-07-12T14:30:00") is False
