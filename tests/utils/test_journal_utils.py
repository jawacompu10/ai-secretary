"""
Tests for src.utils.journal_utils module.
"""

from unittest.mock import patch
from datetime import datetime
from zoneinfo import ZoneInfo

from src.utils.journal_utils import build_updated_description


class TestBuildUpdatedDescription:
    """Tests for build_updated_description function."""

    def test_replace_mode_with_empty_current(self):
        """Test replace mode with empty current description."""
        result = build_updated_description("", "New content", append=False)
        assert result == "New content"

    def test_replace_mode_with_existing_current(self):
        """Test replace mode with existing current description."""
        current = "Old content that will be replaced"
        new_content = "Brand new content"

        result = build_updated_description(current, new_content, append=False)
        assert result == "Brand new content"
        assert "Old content" not in result

    def test_append_mode_with_empty_current(self):
        """Test append mode with empty current description."""
        result = build_updated_description("", "New content", append=True)
        assert result == "New content"

    @patch("src.utils.journal_utils.get_user_timezone")
    @patch("src.utils.journal_utils.datetime")
    def test_append_mode_with_existing_current(self, mock_datetime, mock_get_timezone):
        """Test append mode with existing current description."""
        # Setup mocks
        mock_tz = ZoneInfo("UTC")
        mock_get_timezone.return_value = mock_tz

        mock_now = datetime(2025, 7, 12, 15, 30, 0, tzinfo=mock_tz)
        mock_datetime.now.return_value = mock_now

        current = "Existing content"
        new_content = "Additional content"

        result = build_updated_description(current, new_content, append=True)

        expected = "Existing content\n\n--- [2025-07-12 15:30] ---\nAdditional content"
        assert result == expected

        # Verify mocks were called correctly
        mock_get_timezone.assert_called_once()
        mock_datetime.now.assert_called_once_with(mock_tz)

    @patch("src.utils.journal_utils.get_user_timezone")
    @patch("src.utils.journal_utils.datetime")
    def test_append_mode_timestamp_format(self, mock_datetime, mock_get_timezone):
        """Test that append mode uses correct timestamp format."""
        # Setup mocks for different times
        mock_tz = ZoneInfo("America/New_York")
        mock_get_timezone.return_value = mock_tz

        # Test various timestamp formats
        test_times = [
            datetime(2025, 1, 1, 0, 0, 0, tzinfo=mock_tz),  # Start of year, midnight
            datetime(
                2025, 12, 31, 23, 59, 59, tzinfo=mock_tz
            ),  # End of year, late night
            datetime(2025, 7, 4, 12, 30, 45, tzinfo=mock_tz),  # Mid-year, midday
        ]

        expected_timestamps = [
            "--- [2025-01-01 00:00] ---",
            "--- [2025-12-31 23:59] ---",
            "--- [2025-07-04 12:30] ---",
        ]

        for test_time, expected_timestamp in zip(test_times, expected_timestamps):
            mock_datetime.now.return_value = test_time

            result = build_updated_description("Old", "New", append=True)
            assert expected_timestamp in result

    def test_append_mode_preserves_content_structure(self):
        """Test that append mode preserves content structure."""
        current = "Line 1\nLine 2\n\nParagraph 2"
        new_content = "New line 1\nNew line 2"

        with (
            patch("src.utils.journal_utils.get_user_timezone") as mock_tz,
            patch("src.utils.journal_utils.datetime") as mock_dt,
        ):
            mock_tz.return_value = ZoneInfo("UTC")
            mock_dt.now.return_value = datetime(
                2025, 7, 12, 15, 30, tzinfo=ZoneInfo("UTC")
            )

            result = build_updated_description(current, new_content, append=True)

            # Should preserve original structure and add new content with timestamp
            lines = result.split("\n")
            assert lines[0] == "Line 1"
            assert lines[1] == "Line 2"
            assert lines[2] == ""  # Empty line preserved
            assert lines[3] == "Paragraph 2"
            assert lines[4] == ""  # Separator line
            assert "--- [2025-07-12 15:30] ---" in lines[5]
            assert lines[6] == "New line 1"
            assert lines[7] == "New line 2"

    def test_append_default_parameter(self):
        """Test that append defaults to True."""
        current = "Existing"
        new_content = "New"

        with (
            patch("src.utils.journal_utils.get_user_timezone") as mock_tz,
            patch("src.utils.journal_utils.datetime") as mock_dt,
        ):
            mock_tz.return_value = ZoneInfo("UTC")
            mock_dt.now.return_value = datetime(
                2025, 7, 12, 15, 30, tzinfo=ZoneInfo("UTC")
            )

            # Call without append parameter (should default to True)
            result = build_updated_description(current, new_content)

            # Should include timestamp (append mode)
            assert "--- [2025-07-12 15:30] ---" in result
            assert "Existing" in result
            assert "New" in result

    @patch("src.utils.journal_utils.get_user_timezone")
    @patch("src.utils.journal_utils.datetime")
    def test_multiple_appends_create_history(self, mock_datetime, mock_get_timezone):
        """Test that multiple appends create a chronological history."""
        mock_tz = ZoneInfo("UTC")
        mock_get_timezone.return_value = mock_tz

        # First append
        mock_datetime.now.return_value = datetime(2025, 7, 12, 10, 0, tzinfo=mock_tz)
        first_result = build_updated_description(
            "Initial content", "First addition", append=True
        )

        # Second append
        mock_datetime.now.return_value = datetime(2025, 7, 12, 15, 30, tzinfo=mock_tz)
        second_result = build_updated_description(
            first_result, "Second addition", append=True
        )

        # Should contain all content with timestamps
        assert "Initial content" in second_result
        assert "--- [2025-07-12 10:00] ---" in second_result
        assert "First addition" in second_result
        assert "--- [2025-07-12 15:30] ---" in second_result
        assert "Second addition" in second_result

        # Verify chronological order
        first_timestamp_pos = second_result.find("--- [2025-07-12 10:00] ---")
        second_timestamp_pos = second_result.find("--- [2025-07-12 15:30] ---")
        assert first_timestamp_pos < second_timestamp_pos

    def test_edge_cases_with_special_characters(self):
        """Test handling of special characters in content."""
        current = "Content with émojis 🎉 and special chars: @#$%"
        new_content = "More spécial content with unicode: ñáéíóú"

        # Replace mode
        result_replace = build_updated_description(current, new_content, append=False)
        assert result_replace == new_content
        assert "émojis" not in result_replace

        # Append mode
        with (
            patch("src.utils.journal_utils.get_user_timezone") as mock_tz,
            patch("src.utils.journal_utils.datetime") as mock_dt,
        ):
            mock_tz.return_value = ZoneInfo("UTC")
            mock_dt.now.return_value = datetime(
                2025, 7, 12, 15, 30, tzinfo=ZoneInfo("UTC")
            )

            result_append = build_updated_description(current, new_content, append=True)
            assert "émojis 🎉" in result_append
            assert "ñáéíóú" in result_append
            assert "--- [2025-07-12 15:30] ---" in result_append

    def test_whitespace_handling(self):
        """Test handling of various whitespace scenarios."""
        test_cases = [
            ("", "content", False, "content"),
            ("  ", "content", False, "content"),
            ("content", "", False, ""),
            (
                "content",
                "  new  ",
                False,
                "  new  ",
            ),  # Preserves whitespace in new content
        ]

        for current, new_content, append, expected in test_cases:
            result = build_updated_description(current, new_content, append)
            assert result == expected

    @patch("src.utils.journal_utils.get_user_timezone")
    def test_timezone_integration(self, mock_get_timezone):
        """Test integration with timezone utilities."""
        # Test with different timezones
        timezones = [
            ZoneInfo("UTC"),
            ZoneInfo("America/New_York"),
            ZoneInfo("Europe/London"),
            ZoneInfo("Asia/Tokyo"),
        ]

        for tz in timezones:
            mock_get_timezone.return_value = tz

            with patch("src.utils.journal_utils.datetime") as mock_dt:
                mock_dt.now.return_value = datetime(2025, 7, 12, 15, 30, tzinfo=tz)

                result = build_updated_description("Old", "New", append=True)

                # Should call get_user_timezone and datetime.now with correct timezone
                mock_get_timezone.assert_called()
                mock_dt.now.assert_called_with(tz)

                # Should include timestamp
                assert "--- [2025-07-12 15:30] ---" in result


class TestJournalUtilsIntegration:
    """Integration tests for journal utilities."""

    def test_build_description_consistency(self):
        """Test that build_updated_description behavior is consistent."""
        content_pairs = [
            ("", "new"),
            ("old", "new"),
            ("multi\nline\ncontent", "single line"),
            ("single line", "multi\nline\nnew"),
        ]

        for current, new_content in content_pairs:
            # Replace mode should always return exactly the new content
            replace_result = build_updated_description(
                current, new_content, append=False
            )
            assert replace_result == new_content

            # Append mode with empty current should return exactly the new content
            if not current.strip():
                append_result = build_updated_description(
                    current, new_content, append=True
                )
                assert append_result == new_content

    def test_real_world_usage_patterns(self):
        """Test realistic usage patterns for journal descriptions."""
        with (
            patch("src.utils.journal_utils.get_user_timezone") as mock_tz,
            patch("src.utils.journal_utils.datetime") as mock_dt,
        ):
            mock_tz.return_value = ZoneInfo("UTC")
            mock_dt.now.return_value = datetime(
                2025, 7, 12, 9, 0, tzinfo=ZoneInfo("UTC")
            )

            # Initial journal entry
            initial = "Started working on the new feature today."

            # First update (append)
            mock_dt.now.return_value = datetime(
                2025, 7, 12, 12, 30, tzinfo=ZoneInfo("UTC")
            )
            first_update = build_updated_description(
                initial,
                "Made good progress on the API design. Need to review with team.",
                append=True,
            )

            # Second update (append)
            mock_dt.now.return_value = datetime(
                2025, 7, 12, 17, 45, tzinfo=ZoneInfo("UTC")
            )
            second_update = build_updated_description(
                first_update,
                "Team review went well. Ready to start implementation tomorrow.",
                append=True,
            )

            # Final correction (replace)
            final_correction = build_updated_description(
                second_update,
                "Comprehensive journal entry: Started new feature, designed API, team review successful. Implementation begins tomorrow.",
                append=False,
            )

            # Verify the progression
            assert initial in first_update
            assert "--- [2025-07-12 12:30] ---" in first_update

            assert initial in second_update
            assert "--- [2025-07-12 12:30] ---" in second_update
            assert "--- [2025-07-12 17:45] ---" in second_update

            assert initial not in final_correction
            assert "Comprehensive journal entry" in final_correction
            assert "---" not in final_correction  # No timestamps in replace mode
