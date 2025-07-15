"""
Tests for src.utils.vcalendar_parser module.
"""

from src.utils.vcalendar_parser import (
    vcalendar_to_dict,
    escape_vcalendar_text,
    get_vcalendar_property,
    update_vcalendar_property,
)


class TestVcalendarToDict:
    """Tests for vcalendar_to_dict function."""

    def test_parse_simple_vcalendar(self):
        """Test parsing simple VCALENDAR data."""
        vcal_data = """BEGIN:VCALENDAR
SUMMARY:Test Event
DESCRIPTION:A simple test event
DTSTART:20250712T140000Z
END:VCALENDAR"""

        result = vcalendar_to_dict(vcal_data)

        assert result["SUMMARY"] == "Test Event"
        assert result["DESCRIPTION"] == "A simple test event"
        assert result["DTSTART"] == "20250712T140000Z"
        assert "BEGIN" not in result
        assert "END" not in result

    def test_parse_vcalendar_with_continuation_lines(self):
        """Test parsing VCALENDAR with continuation lines (folded lines)."""
        vcal_data = """BEGIN:VTODO
SUMMARY:Short title
DESCRIPTION:This is a very long description that spans multiple lines
 and continues here with proper folding
 and maybe even a third line
DTSTART:20250712T140000Z
END:VTODO"""

        result = vcalendar_to_dict(vcal_data)

        expected_desc = """This is a very long description that spans multiple lines
and continues here with proper folding
and maybe even a third line"""

        assert result["SUMMARY"] == "Short title"
        assert result["DESCRIPTION"] == expected_desc
        assert result["DTSTART"] == "20250712T140000Z"

    def test_parse_vcalendar_with_colons_in_values(self):
        """Test parsing VCALENDAR with colons in property values."""
        vcal_data = """BEGIN:VEVENT
SUMMARY:Meeting at 2:30 PM
DESCRIPTION:URL: https://example.com:8080/path
LOCATION:Room 1:2:3
END:VEVENT"""

        result = vcalendar_to_dict(vcal_data)

        # Note: This tests the limitation mentioned in the docstring
        assert result["SUMMARY"] == "Meeting at 2:30 PM"
        # Due to the simple implementation, values with colons may be split incorrectly
        # This test documents the current behavior
        assert "DESCRIPTION" in result
        assert "LOCATION" in result

    def test_parse_empty_vcalendar(self):
        """Test parsing empty or minimal VCALENDAR data."""
        vcal_data = """BEGIN:VCALENDAR
END:VCALENDAR"""

        result = vcalendar_to_dict(vcal_data)
        assert result == {}

    def test_parse_vcalendar_with_whitespace_variations(self):
        """Test parsing VCALENDAR with various whitespace scenarios."""
        vcal_data = """BEGIN:VTODO
SUMMARY:  Task with spaces  
DESCRIPTION:Normal description
PRIORITY:1
CATEGORY:Work
LOCATION:Tabbed location
END:VTODO"""

        result = vcalendar_to_dict(vcal_data)

        assert (
            result["SUMMARY"] == "  Task with spaces"
        )  # Preserves leading whitespace, strips trailing
        assert result["DESCRIPTION"] == "Normal description"
        assert result["PRIORITY"] == "1"
        assert result["CATEGORY"] == "Work"
        assert result["LOCATION"] == "Tabbed location"


class TestEscapeVcalendarText:
    """Tests for escape_vcalendar_text function."""

    def test_escape_backslashes(self):
        """Test escaping backslashes in text."""
        text = "Path\\to\\file"
        result = escape_vcalendar_text(text)
        assert result == "Path\\\\to\\\\file"

    def test_escape_newlines(self):
        """Test escaping newlines in text."""
        text = "Line 1\nLine 2\nLine 3"
        result = escape_vcalendar_text(text)
        assert result == "Line 1\\nLine 2\\nLine 3"

    def test_escape_commas(self):
        """Test escaping commas in text."""
        text = "Item 1, Item 2, Item 3"
        result = escape_vcalendar_text(text)
        assert result == "Item 1\\, Item 2\\, Item 3"

    def test_escape_semicolons(self):
        """Test escaping semicolons in text."""
        text = "Value1;Value2;Value3"
        result = escape_vcalendar_text(text)
        assert result == "Value1\\;Value2\\;Value3"

    def test_escape_multiple_special_characters(self):
        """Test escaping text with multiple special characters."""
        text = "Multi\\line\nwith, special; chars"
        result = escape_vcalendar_text(text)
        assert result == "Multi\\\\line\\nwith\\, special\\; chars"

    def test_escape_order_matters(self):
        """Test that backslashes are escaped first to avoid double-escaping."""
        text = "Already\\,escaped\\;text"
        result = escape_vcalendar_text(text)
        # Should not double-escape the existing backslashes
        assert result == "Already\\\\\\,escaped\\\\\\;text"

    def test_escape_empty_string(self):
        """Test escaping empty string."""
        result = escape_vcalendar_text("")
        assert result == ""

    def test_escape_text_without_special_chars(self):
        """Test escaping text without special characters."""
        text = "Normal text without special characters"
        result = escape_vcalendar_text(text)
        assert result == text  # Should be unchanged


class TestGetVcalendarProperty:
    """Tests for get_vcalendar_property function."""

    def test_get_existing_property(self):
        """Test getting an existing property from VCALENDAR data."""
        vcal_data = """BEGIN:VTODO
SUMMARY:Test Task
DESCRIPTION:Task description
PRIORITY:1
END:VTODO"""

        assert get_vcalendar_property(vcal_data, "SUMMARY") == "Test Task"
        assert get_vcalendar_property(vcal_data, "DESCRIPTION") == "Task description"
        assert get_vcalendar_property(vcal_data, "PRIORITY") == "1"

    def test_get_nonexistent_property(self):
        """Test getting a non-existent property returns None."""
        vcal_data = """BEGIN:VTODO
SUMMARY:Test Task
END:VTODO"""

        result = get_vcalendar_property(vcal_data, "NONEXISTENT")
        assert result is None

    def test_get_property_with_continuation_lines(self):
        """Test getting property with continuation lines."""
        vcal_data = """BEGIN:VTODO
SUMMARY:Test Task
DESCRIPTION:This is a long description
 that continues on the next line
 and even has a third line
PRIORITY:1
END:VTODO"""

        result = get_vcalendar_property(vcal_data, "DESCRIPTION")
        expected = """This is a long description
that continues on the next line
and even has a third line"""
        assert result == expected

    def test_get_property_case_sensitive(self):
        """Test that property names are case-sensitive."""
        vcal_data = """BEGIN:VTODO
SUMMARY:Test Task
summary:lowercase
END:VTODO"""

        assert get_vcalendar_property(vcal_data, "SUMMARY") == "Test Task"
        assert get_vcalendar_property(vcal_data, "summary") == "lowercase"
        assert get_vcalendar_property(vcal_data, "Summary") is None

    def test_get_property_with_colon_in_value(self):
        """Test getting property with colon in the value."""
        vcal_data = """BEGIN:VEVENT
SUMMARY:Meeting
DESCRIPTION:Time: 14:30, Location: Room A:B
END:VEVENT"""

        result = get_vcalendar_property(vcal_data, "DESCRIPTION")
        assert result == "Time: 14:30, Location: Room A:B"

    def test_get_first_occurrence_when_duplicate(self):
        """Test that first occurrence is returned when property appears multiple times."""
        vcal_data = """BEGIN:VTODO
SUMMARY:First Summary
DESCRIPTION:Task description
SUMMARY:Second Summary
END:VTODO"""

        result = get_vcalendar_property(vcal_data, "SUMMARY")
        assert result == "First Summary"


class TestUpdateVcalendarProperty:
    """Tests for update_vcalendar_property function."""

    def test_update_existing_property(self):
        """Test updating an existing property."""
        vcal_data = """BEGIN:VJOURNAL
SUMMARY:Old Summary
DESCRIPTION:Old description
DTSTART:20250712T140000Z
END:VJOURNAL"""

        result = update_vcalendar_property(
            vcal_data, "DESCRIPTION", "New description content", "VJOURNAL"
        )

        # Should contain the updated description
        assert "DESCRIPTION:New description content" in result
        # Should not contain the old description
        assert "Old description" not in result
        # Other properties should be preserved
        assert "SUMMARY:Old Summary" in result
        assert "DTSTART:20250712T140000Z" in result

    def test_update_property_with_special_characters(self):
        """Test updating property with special characters (auto-escaped)."""
        vcal_data = """BEGIN:VJOURNAL
SUMMARY:Test
DESCRIPTION:Old content
END:VJOURNAL"""

        new_content = "Multi\nline with, special; chars\\backslash"
        result = update_vcalendar_property(
            vcal_data, "DESCRIPTION", new_content, "VJOURNAL"
        )

        # Should contain escaped version
        assert (
            "DESCRIPTION:Multi\\nline with\\, special\\; chars\\\\backslash" in result
        )

    def test_add_new_property(self):
        """Test adding a new property that doesn't exist."""
        vcal_data = """BEGIN:VJOURNAL
SUMMARY:Test Summary
DTSTART:20250712T140000Z
END:VJOURNAL"""

        result = update_vcalendar_property(
            vcal_data, "DESCRIPTION", "New description", "VJOURNAL"
        )

        # Should contain the new property before END:VJOURNAL
        lines = result.split("\n")
        description_line_idx = None
        end_line_idx = None

        for i, line in enumerate(lines):
            if line.startswith("DESCRIPTION:"):
                description_line_idx = i
            elif line == "END:VJOURNAL":
                end_line_idx = i

        assert description_line_idx is not None
        assert end_line_idx is not None
        assert description_line_idx < end_line_idx
        assert "DESCRIPTION:New description" in result

    def test_update_property_with_continuation_lines(self):
        """Test updating property that has continuation lines."""
        vcal_data = """BEGIN:VTODO
SUMMARY:Test Task
DESCRIPTION:Old multi-line description
 with continuation lines
 and more content
PRIORITY:1
END:VTODO"""

        result = update_vcalendar_property(
            vcal_data, "DESCRIPTION", "New single line description", "VTODO"
        )

        # Should replace all lines of the old property
        assert "DESCRIPTION:New single line description" in result
        assert "Old multi-line description" not in result
        assert "with continuation lines" not in result
        assert "and more content" not in result
        # Other properties should be preserved
        assert "SUMMARY:Test Task" in result
        assert "PRIORITY:1" in result

    def test_update_different_component_types(self):
        """Test updating properties in different component types."""
        component_tests = [
            ("VTODO", "TODO task"),
            ("VEVENT", "Event description"),
            ("VJOURNAL", "Journal entry"),
            ("VFREEBUSY", "Freebusy info"),
        ]

        for component_type, description in component_tests:
            vcal_data = f"""BEGIN:{component_type}
SUMMARY:Test
END:{component_type}"""

            result = update_vcalendar_property(
                vcal_data, "DESCRIPTION", description, component_type
            )

            assert f"DESCRIPTION:{description}" in result
            assert f"BEGIN:{component_type}" in result
            assert f"END:{component_type}" in result

    def test_update_preserves_line_structure(self):
        """Test that update preserves the overall VCALENDAR structure."""
        vcal_data = """BEGIN:VCALENDAR
VERSION:2.0
PRODID:Test
BEGIN:VJOURNAL
UID:test-uid-123
SUMMARY:Journal Entry
DESCRIPTION:Old content
DTSTART:20250712T140000Z
END:VJOURNAL
END:VCALENDAR"""

        result = update_vcalendar_property(
            vcal_data, "DESCRIPTION", "Updated content", "VJOURNAL"
        )

        # Should preserve overall structure
        assert result.startswith("BEGIN:VCALENDAR")
        assert result.endswith("END:VCALENDAR")
        assert "VERSION:2.0" in result
        assert "PRODID:Test" in result
        assert "UID:test-uid-123" in result
        assert "DESCRIPTION:Updated content" in result
        assert "Old content" not in result


class TestVcalendarParserIntegration:
    """Integration tests for VCALENDAR parser utilities."""

    def test_round_trip_property_operations(self):
        """Test round-trip: get property -> update property -> get property."""
        vcal_data = """BEGIN:VJOURNAL
SUMMARY:Test Journal
DESCRIPTION:Original description
DTSTART:20250712T140000Z
END:VJOURNAL"""

        # Get original property
        original = get_vcalendar_property(vcal_data, "DESCRIPTION")
        assert original == "Original description"

        # Update property
        updated_vcal = update_vcalendar_property(
            vcal_data, "DESCRIPTION", "Updated description", "VJOURNAL"
        )

        # Get updated property
        updated = get_vcalendar_property(updated_vcal, "DESCRIPTION")
        assert updated == "Updated description"

        # Original should be gone
        assert "Original description" not in updated_vcal

    def test_escape_and_update_integration(self):
        """Test that escaping works correctly in update operations."""
        vcal_data = """BEGIN:VJOURNAL
SUMMARY:Test
END:VJOURNAL"""

        # Content with special characters that need escaping
        special_content = "Line 1\nLine 2, with comma; and semicolon\\backslash"

        # Update property (should auto-escape)
        updated_vcal = update_vcalendar_property(
            vcal_data, "DESCRIPTION", special_content, "VJOURNAL"
        )

        # The raw VCALENDAR should contain escaped version
        assert (
            "Line 1\\nLine 2\\, with comma\\; and semicolon\\\\backslash"
            in updated_vcal
        )

        # But getting the property should return unescaped version
        # Note: get_vcalendar_property doesn't unescape, this tests current behavior
        retrieved = get_vcalendar_property(updated_vcal, "DESCRIPTION")
        assert (
            retrieved == "Line 1\\nLine 2\\, with comma\\; and semicolon\\\\backslash"
        )

    def test_multiple_property_updates(self):
        """Test updating multiple properties in sequence."""
        vcal_data = """BEGIN:VTODO
SUMMARY:Original Task
DESCRIPTION:Original description
PRIORITY:3
END:VTODO"""

        # Update summary
        step1 = update_vcalendar_property(vcal_data, "SUMMARY", "Updated Task", "VTODO")

        # Update description
        step2 = update_vcalendar_property(
            step1, "DESCRIPTION", "Updated description", "VTODO"
        )

        # Add new property
        step3 = update_vcalendar_property(step2, "STATUS", "IN-PROCESS", "VTODO")

        # Verify all updates
        assert get_vcalendar_property(step3, "SUMMARY") == "Updated Task"
        assert get_vcalendar_property(step3, "DESCRIPTION") == "Updated description"
        assert get_vcalendar_property(step3, "PRIORITY") == "3"  # Unchanged
        assert get_vcalendar_property(step3, "STATUS") == "IN-PROCESS"  # New

        # Original values should be gone
        assert "Original Task" not in step3
        assert "Original description" not in step3

    def test_parser_handles_malformed_input_gracefully(self):
        """Test that parser handles malformed input without crashing."""
        malformed_inputs = [
            "",  # Empty string
            "Not valid VCALENDAR at all",
            "BEGIN:VTODO\nSUMMARY\nEND:VTODO",  # Missing colon
            "SUMMARY:Task",  # No BEGIN/END
        ]

        for malformed_input in malformed_inputs:
            # Should not crash
            result = vcalendar_to_dict(malformed_input)
            assert isinstance(result, dict)

            # get_vcalendar_property should handle gracefully
            get_vcalendar_property(malformed_input, "SUMMARY")
            # May return None or unexpected results, but shouldn't crash

            # update_vcalendar_property should handle gracefully
            updated = update_vcalendar_property(
                malformed_input, "TEST", "value", "VTODO"
            )
            assert isinstance(updated, str)
