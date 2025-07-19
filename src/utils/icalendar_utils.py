"""
Utility functions for parsing CalDAV VCALENDAR data using the icalendar library.

This module provides helper functions to replace our custom vcalendar parser
with the industry-standard icalendar library, which properly handles
CalDAV line folding without introducing unwanted newlines.
"""

import icalendar
from typing import Dict, Any, Optional


def parse_caldav_component(vcal_data: str, component_type: str = None) -> Dict[str, Any]:
    """Parse CalDAV VCALENDAR data into a dictionary using icalendar library.
    
    Args:
        vcal_data (str): Raw VCALENDAR data from CalDAV server
        component_type (str, optional): Specific component type to extract (VTODO, VJOURNAL, VEVENT)
                                       If None, returns properties from the first found component
    
    Returns:
        Dict[str, Any]: Dictionary of component properties with string values
        
    Raises:
        ValueError: If VCALENDAR data is invalid or component not found
    """
    try:
        cal = icalendar.Calendar.from_ical(vcal_data)
        
        # Find the target component
        for component in cal.walk():
            # Skip VCALENDAR wrapper
            if component.name == 'VCALENDAR':
                continue
                
            # Check if this is the component we want
            if component_type:
                if component.name != component_type:
                    continue
            else:
                # No specific type requested, take first calendar component
                if component.name not in ['VTODO', 'VJOURNAL', 'VEVENT']:
                    continue
                
            # Extract properties and convert to strings
            props = {}
            for key, value in component.items():
                if isinstance(value, (list, tuple)):
                    # Handle multi-value properties (rare in our use case)
                    props[key] = str(value[0]) if value else ""
                else:
                    # For icalendar objects, extract the actual value if possible
                    if hasattr(value, 'to_ical'):
                        # This is an icalendar property object, get its iCalendar representation
                        props[key] = value.to_ical().decode('utf-8')
                    else:
                        # Convert other types to string
                        props[key] = str(value)
            
            return props
            
        # If no component found
        component_info = f" of type {component_type}" if component_type else ""
        raise ValueError(f"No calendar component{component_info} found in VCALENDAR data")
        
    except ValueError as e:
        if "not found" in str(e).lower() or "invalid" in str(e).lower():
            raise ValueError(f"Invalid VCALENDAR data: {e}")
        else:
            raise
    except Exception as e:
        raise ValueError(f"Failed to parse VCALENDAR data: {e}")


def get_component_property(vcal_data: str, property_name: str, component_type: str = None) -> Optional[str]:
    """Extract a specific property value from CalDAV VCALENDAR data.
    
    Args:
        vcal_data (str): Raw VCALENDAR data from CalDAV server
        property_name (str): Property name to extract (e.g., 'SUMMARY', 'DESCRIPTION', 'DTSTART')
        component_type (str, optional): Specific component type to search in
        
    Returns:
        Optional[str]: Property value as string, or None if not found
        
    Raises:
        ValueError: If VCALENDAR data is invalid
    """
    try:
        props = parse_caldav_component(vcal_data, component_type)
        return props.get(property_name)
    except ValueError:
        # Re-raise parsing errors
        raise
    except Exception as e:
        raise ValueError(f"Failed to extract property {property_name}: {e}")


def normalize_caldav_summary(summary: str) -> str:
    """Normalize CalDAV summary text by removing unwanted artifacts.
    
    This function handles cases where the icalendar library applies RFC 5545
    escaping rules to summary fields that need to be unescaped for user display.
    
    Args:
        summary (str): Raw summary text from icalendar library
        
    Returns:
        str: Normalized summary with escaping removed and whitespace cleaned
    """
    if not summary:
        return summary
        
    # Remove line breaks and normalize whitespace
    normalized = ' '.join(summary.split())
    
    # Unescape RFC 5545 special characters that icalendar might escape
    # Based on RFC 5545: https://tools.ietf.org/html/rfc5545#section-3.3.11
    normalized = normalized.replace('\\,', ',')  # Comma
    normalized = normalized.replace('\\;', ';')  # Semicolon
    normalized = normalized.replace('\\\\', '\\')  # Backslash (must be last)
    
    return normalized.strip()