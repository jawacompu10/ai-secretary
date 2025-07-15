def vcalendar_to_dict(vcal_data: str) -> dict:
    """Parse VCALENDAR data into a dictionary.

    Note: This simple implementation has limitations:
    - Properties with colons in values will be split incorrectly
    - VTODO-specific properties only, ignores VCALENDAR wrapper
    """
    result = {}
    lines = vcal_data.strip().split("\n")
    current_key = None

    for line in lines:
        stripped_line = line.strip()

        # Skip BEGIN/END lines
        if stripped_line.startswith(("BEGIN:", "END:")):
            continue

        # Check if it's a continuation line (starts with whitespace)
        if line.startswith((" ", "\t")) and current_key:
            result[current_key] += "\n" + stripped_line
        elif ":" in stripped_line:
            key, value = stripped_line.split(":", 1)
            result[key] = value
            current_key = key

    return result


def escape_vcalendar_text(text: str) -> str:
    """Escape special characters in text for VCALENDAR format.
    
    Args:
        text (str): Raw text to escape
        
    Returns:
        str: Text with VCALENDAR special characters properly escaped
        
    VCALENDAR escaping rules:
    - Backslashes: \ -> \\
    - Newlines: \n -> \\n  
    - Commas: , -> \\,
    - Semicolons: ; -> \\;
    """
    return (
        text.replace("\\", "\\\\")  # Must be first to avoid double-escaping
        .replace("\n", "\\n")
        .replace(",", "\\,")
        .replace(";", "\\;")
    )


def get_vcalendar_property(vcal_data: str, property_name: str) -> str | None:
    """Extract a specific property value from VCALENDAR data.

    Args:
        vcal_data (str): Raw VCALENDAR data
        property_name (str): Property name to extract (e.g., 'DESCRIPTION', 'SUMMARY')

    Returns:
        str | None: Property value with continuation lines joined, or None if not found

    Handles multiline properties with continuation lines that start with whitespace.
    """
    lines = vcal_data.split("\n")
    property_value = None
    collecting_continuation = False

    for line in lines:
        if line.startswith(f"{property_name}:"):
            # Found the property, extract value after colon
            property_value = line[len(property_name) + 1 :]
            collecting_continuation = True
        elif collecting_continuation and line.startswith((" ", "\t")):
            # Continuation line - add to property value
            property_value += "\n" + line.strip()
        elif collecting_continuation:
            # End of continuation lines
            break

    return property_value


def update_vcalendar_property(
    vcal_data: str, property_name: str, new_value: str, component_type: str = "VJOURNAL"
) -> str:
    """Update or add a property in VCALENDAR data.

    Args:
        vcal_data (str): Raw VCALENDAR data
        property_name (str): Property name to update (e.g., 'DESCRIPTION', 'SUMMARY')
        new_value (str): New property value (will be automatically escaped)
        component_type (str): VCALENDAR component type (VJOURNAL, VTODO, VEVENT, etc.)

    Returns:
        str: Updated VCALENDAR data

    If the property exists, replaces it and any continuation lines.
    If the property doesn't exist, adds it before END:{component_type}.
    """
    lines = vcal_data.split("\n")
    new_lines = []
    skip_next_lines = False
    property_found = False
    escaped_value = escape_vcalendar_text(new_value)

    for i, line in enumerate(lines):
        if line.startswith(f"{property_name}:"):
            # Replace existing property
            new_lines.append(f"{property_name}:{escaped_value}")
            skip_next_lines = True
            property_found = True
        elif skip_next_lines and line.startswith((" ", "\t")):
            # Skip continuation lines of old property
            continue
        else:
            skip_next_lines = False
            new_lines.append(line)

    # If property wasn't found, add it before END:{component_type}
    if not property_found:
        for i, line in enumerate(new_lines):
            if line == f"END:{component_type}":
                new_lines.insert(i, f"{property_name}:{escaped_value}")
                break

    return "\n".join(new_lines)
