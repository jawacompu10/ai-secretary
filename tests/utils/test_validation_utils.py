"""
Tests for src.utils.validation_utils module.
"""

import pytest

from src.utils.validation_utils import (
    validate_required_string,
    validate_calendar_name,
    validate_task_summary,
    validate_journal_summary,
    validate_journal_description,
    validate_event_summary,
    validate_new_description,
)


class TestValidateRequiredString:
    """Tests for validate_required_string function."""

    def test_validate_valid_string(self):
        """Test validation passes for valid non-empty string."""
        # Should not raise any exception
        validate_required_string("Valid content", "Test Field")

    def test_validate_string_with_spaces(self):
        """Test validation passes for string with leading/trailing spaces."""
        # Should not raise any exception
        validate_required_string("  Valid content  ", "Test Field")

    def test_validate_none_value(self):
        """Test validation fails for None value."""
        with pytest.raises(ValueError, match="Test Field cannot be empty"):
            validate_required_string(None, "Test Field")

    def test_validate_empty_string(self):
        """Test validation fails for empty string."""
        with pytest.raises(ValueError, match="Test Field cannot be empty"):
            validate_required_string("", "Test Field")

    def test_validate_whitespace_only(self):
        """Test validation fails for whitespace-only string."""
        with pytest.raises(ValueError, match="Test Field cannot be empty"):
            validate_required_string("   ", "Test Field")

    def test_validate_tab_whitespace(self):
        """Test validation fails for tab and newline whitespace."""
        with pytest.raises(ValueError, match="Test Field cannot be empty"):
            validate_required_string("\t\n  ", "Test Field")

    def test_error_message_includes_field_name(self):
        """Test error message includes the provided field name."""
        field_name = "Custom Field Name"
        with pytest.raises(ValueError, match=f"{field_name} cannot be empty"):
            validate_required_string("", field_name)

    @pytest.mark.parametrize(
        "valid_input",
        [
            "a",  # Single character
            "Valid string",
            "String with numbers 123",
            "String with symbols !@#$%",
            "Multi\nline\nstring",
            "String with unicode: 🎉",
            "   Content with surrounding spaces   ",
        ],
    )
    def test_validate_various_valid_inputs(self, valid_input):
        """Test validation passes for various valid inputs."""
        # Should not raise any exception
        validate_required_string(valid_input, "Test Field")

    @pytest.mark.parametrize(
        "invalid_input",
        [
            None,
            "",
            " ",
            "  ",
            "\t",
            "\n",
            "\r",
            "\t\n\r  ",
        ],
    )
    def test_validate_various_invalid_inputs(self, invalid_input):
        """Test validation fails for various invalid inputs."""
        with pytest.raises(ValueError, match="Test Field cannot be empty"):
            validate_required_string(invalid_input, "Test Field")


class TestValidateCalendarName:
    """Tests for validate_calendar_name function."""

    def test_validate_valid_calendar_name(self):
        """Test validation passes for valid calendar name."""
        # Should not raise any exception
        validate_calendar_name("Work Calendar")

    def test_validate_invalid_calendar_name(self):
        """Test validation fails for invalid calendar name."""
        with pytest.raises(ValueError, match="Calendar name cannot be empty"):
            validate_calendar_name("")

    def test_validate_none_calendar_name(self):
        """Test validation fails for None calendar name."""
        with pytest.raises(ValueError, match="Calendar name cannot be empty"):
            validate_calendar_name(None)

    def test_validate_whitespace_calendar_name(self):
        """Test validation fails for whitespace-only calendar name."""
        with pytest.raises(ValueError, match="Calendar name cannot be empty"):
            validate_calendar_name("   ")


class TestValidateTaskSummary:
    """Tests for validate_task_summary function."""

    def test_validate_valid_task_summary(self):
        """Test validation passes for valid task summary."""
        # Should not raise any exception
        validate_task_summary("Complete project proposal")

    def test_validate_invalid_task_summary(self):
        """Test validation fails for invalid task summary."""
        with pytest.raises(ValueError, match="Task summary cannot be empty"):
            validate_task_summary("")

    def test_validate_none_task_summary(self):
        """Test validation fails for None task summary."""
        with pytest.raises(ValueError, match="Task summary cannot be empty"):
            validate_task_summary(None)


class TestValidateJournalSummary:
    """Tests for validate_journal_summary function."""

    def test_validate_valid_journal_summary(self):
        """Test validation passes for valid journal summary."""
        # Should not raise any exception
        validate_journal_summary("Daily reflection")

    def test_validate_invalid_journal_summary(self):
        """Test validation fails for invalid journal summary."""
        with pytest.raises(ValueError, match="Journal summary cannot be empty"):
            validate_journal_summary("")

    def test_validate_none_journal_summary(self):
        """Test validation fails for None journal summary."""
        with pytest.raises(ValueError, match="Journal summary cannot be empty"):
            validate_journal_summary(None)


class TestValidateJournalDescription:
    """Tests for validate_journal_description function."""

    def test_validate_valid_journal_description(self):
        """Test validation passes for valid journal description."""
        # Should not raise any exception
        validate_journal_description("Today was a productive day...")

    def test_validate_invalid_journal_description(self):
        """Test validation fails for invalid journal description."""
        with pytest.raises(ValueError, match="Journal description cannot be empty"):
            validate_journal_description("")

    def test_validate_none_journal_description(self):
        """Test validation fails for None journal description."""
        with pytest.raises(ValueError, match="Journal description cannot be empty"):
            validate_journal_description(None)


class TestValidateEventSummary:
    """Tests for validate_event_summary function."""

    def test_validate_valid_event_summary(self):
        """Test validation passes for valid event summary."""
        # Should not raise any exception
        validate_event_summary("Team meeting")

    def test_validate_invalid_event_summary(self):
        """Test validation fails for invalid event summary."""
        with pytest.raises(ValueError, match="Event summary cannot be empty"):
            validate_event_summary("")

    def test_validate_none_event_summary(self):
        """Test validation fails for None event summary."""
        with pytest.raises(ValueError, match="Event summary cannot be empty"):
            validate_event_summary(None)


class TestValidateNewDescription:
    """Tests for validate_new_description function."""

    def test_validate_valid_new_description(self):
        """Test validation passes for valid new description."""
        # Should not raise any exception
        validate_new_description("Updated description content")

    def test_validate_invalid_new_description(self):
        """Test validation fails for invalid new description."""
        with pytest.raises(ValueError, match="New description cannot be empty"):
            validate_new_description("")

    def test_validate_none_new_description(self):
        """Test validation fails for None new description."""
        with pytest.raises(ValueError, match="New description cannot be empty"):
            validate_new_description(None)


class TestValidationUtilsIntegration:
    """Integration tests for validation utilities."""

    @pytest.mark.parametrize(
        "validator_func,error_message_part",
        [
            (validate_calendar_name, "Calendar name"),
            (validate_task_summary, "Task summary"),
            (validate_journal_summary, "Journal summary"),
            (validate_journal_description, "Journal description"),
            (validate_event_summary, "Event summary"),
            (validate_new_description, "New description"),
        ],
    )
    def test_all_validators_use_consistent_behavior(
        self, validator_func, error_message_part
    ):
        """Test that all specific validators behave consistently."""
        # Valid input should pass
        validator_func("Valid content")

        # Invalid inputs should raise ValueError with appropriate message
        with pytest.raises(ValueError, match=f"{error_message_part} cannot be empty"):
            validator_func("")

        with pytest.raises(ValueError, match=f"{error_message_part} cannot be empty"):
            validator_func(None)

        with pytest.raises(ValueError, match=f"{error_message_part} cannot be empty"):
            validator_func("   ")

    def test_validators_preserve_valid_content(self):
        """Test that validators don't modify valid content."""
        original_content = "  Valid content with spaces  "

        # All validators should accept this content without modification
        validators = [
            validate_calendar_name,
            validate_task_summary,
            validate_journal_summary,
            validate_journal_description,
            validate_event_summary,
            validate_new_description,
        ]

        for validator in validators:
            # Should not raise any exception
            validator(original_content)

    def test_custom_field_name_in_base_validator(self):
        """Test that custom field names work correctly in base validator."""
        custom_field_names = [
            "Custom Field",
            "Field Name With Spaces",
            "field_with_underscores",
            "FieldWithNumbers123",
        ]

        for field_name in custom_field_names:
            with pytest.raises(ValueError, match=f"{field_name} cannot be empty"):
                validate_required_string("", field_name)

    def test_all_validators_handle_edge_cases(self):
        """Test that all validators handle edge cases consistently."""
        edge_cases = [
            "\t",  # Tab only
            "\n",  # Newline only
            "\r\n",  # Windows line ending
            "  \t\n ",  # Mixed whitespace
        ]

        validators = [
            validate_calendar_name,
            validate_task_summary,
            validate_journal_summary,
            validate_journal_description,
            validate_event_summary,
            validate_new_description,
        ]

        for validator in validators:
            for edge_case in edge_cases:
                with pytest.raises(ValueError, match="cannot be empty"):
                    validator(edge_case)
