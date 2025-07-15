from datetime import datetime
from zoneinfo import ZoneInfo
from caldav import Event as CalDavEvent
from pydantic import BaseModel, Field

from src.utils.vcalendar_parser import vcalendar_to_dict
from src.utils.timezone_utils import format_datetime_for_user


class EventCreate(BaseModel):
    """Model for creating a new event."""

    summary: str = Field(..., description="Event title/summary")
    calendar_name: str = Field(
        ..., description="Name of the calendar to add the event to"
    )
    start_datetime: str = Field(
        ...,
        description="Start datetime in ISO format with timezone (YYYY-MM-DDTHH:MM:SS+TZ or YYYY-MM-DDTHH:MM:SSZ)",
    )
    end_datetime: str = Field(
        ...,
        description="End datetime in ISO format with timezone (YYYY-MM-DDTHH:MM:SS+TZ or YYYY-MM-DDTHH:MM:SSZ)",
    )
    description: str | None = Field(
        None, description="Optional detailed event description"
    )
    location: str | None = Field(None, description="Optional event location")
    rrule: str | None = Field(
        None,
        description="Recurrence rule in RRULE format (e.g., 'FREQ=WEEKLY;BYDAY=TU')",
    )


class EventUpdate(BaseModel):
    """Model for updating an event."""

    summary: str = Field(..., description="Event summary to identify the event")
    calendar_name: str = Field(..., description="Calendar containing the event")
    new_start_datetime: str | None = Field(
        None,
        description="New start datetime in ISO format with timezone (YYYY-MM-DDTHH:MM:SS+TZ or YYYY-MM-DDTHH:MM:SSZ)",
    )
    new_end_datetime: str | None = Field(
        None,
        description="New end datetime in ISO format with timezone (YYYY-MM-DDTHH:MM:SS+TZ or YYYY-MM-DDTHH:MM:SSZ)",
    )
    new_description: str | None = Field(None, description="New event description")
    new_location: str | None = Field(None, description="New event location")
    new_rrule: str | None = Field(
        None, description="New recurrence rule in RRULE format"
    )


class EventDelete(BaseModel):
    """Model for deleting an event."""

    summary: str = Field(..., description="Event summary to identify the event")
    calendar_name: str = Field(..., description="Calendar containing the event")


class EventInstanceCancel(BaseModel):
    """Model for canceling a single instance of a recurring event."""

    summary: str = Field(
        ..., description="Recurring event summary to identify the event series"
    )
    calendar_name: str = Field(..., description="Calendar containing the event")
    instance_date: str = Field(
        ...,
        description="Date of the specific instance to cancel in ISO format (YYYY-MM-DD)",
    )


class EventInstanceModify(BaseModel):
    """Model for modifying a single instance of a recurring event."""

    summary: str = Field(
        ..., description="Recurring event summary to identify the event series"
    )
    calendar_name: str = Field(..., description="Calendar containing the event")
    instance_date: str = Field(
        ...,
        description="Date of the specific instance to modify in ISO format (YYYY-MM-DD)",
    )
    new_start_datetime: str | None = Field(
        None,
        description="New start datetime for this instance in ISO format with timezone",
    )
    new_end_datetime: str | None = Field(
        None,
        description="New end datetime for this instance in ISO format with timezone",
    )
    new_description: str | None = Field(
        None, description="New description for this instance"
    )
    new_location: str | None = Field(None, description="New location for this instance")


class Event(BaseModel):
    """Event model representing a calendar event."""

    summary: str = Field(..., description="Event title/summary")
    description: str | None = Field(default=None, description="Event description")
    calendar_name: str = Field(
        ..., description="Name of the calendar containing this event"
    )
    start_datetime_utc: datetime | None = Field(
        default=None, description="Event start time in UTC (internal storage)"
    )
    end_datetime_utc: datetime | None = Field(
        default=None, description="Event end time in UTC (internal storage)"
    )
    start_datetime_local: str | None = Field(
        default=None, description="Event start time in user's timezone (for display)"
    )
    end_datetime_local: str | None = Field(
        default=None, description="Event end time in user's timezone (for display)"
    )
    location: str | None = Field(default=None, description="Event location")
    status: str | None = Field(default=None, description="Event status")
    rrule: str | None = Field(default=None, description="Recurrence rule if recurring")
    is_recurring: bool = Field(
        default=False, description="Whether this is a recurring event"
    )

    @classmethod
    def from_caldav_event(cls, event: CalDavEvent, calendar_name: str):
        """Create Event from CalDAV event object with proper timezone handling."""
        props = vcalendar_to_dict(event.data)

        # Parse datetime fields and convert to UTC
        start_dt_utc = None
        end_dt_utc = None

        if "DTSTART" in props:
            try:
                start_str = props["DTSTART"]
                start_dt_utc = cls._parse_caldav_datetime(start_str)
            except (ValueError, AttributeError):
                pass

        if "DTEND" in props:
            try:
                end_str = props["DTEND"]
                end_dt_utc = cls._parse_caldav_datetime(end_str)
            except (ValueError, AttributeError):
                pass

        # Check for recurrence rule
        rrule = props.get("RRULE")
        is_recurring = rrule is not None

        return cls(
            summary=props.get("SUMMARY", "Untitled Event"),
            description=props.get("DESCRIPTION"),
            calendar_name=calendar_name,
            start_datetime_utc=start_dt_utc,
            end_datetime_utc=end_dt_utc,
            start_datetime_local=format_datetime_for_user(start_dt_utc),
            end_datetime_local=format_datetime_for_user(end_dt_utc),
            location=props.get("LOCATION"),
            status=props.get("STATUS"),
            rrule=rrule,
            is_recurring=is_recurring,
        )

    @staticmethod
    def _parse_caldav_datetime(dt_str: str) -> datetime:
        """Parse CalDAV datetime string and convert to UTC."""
        try:
            # Handle Z suffix (UTC)
            if dt_str.endswith("Z"):
                dt_str = dt_str[:-1]
                dt = datetime.fromisoformat(dt_str)
                return dt.replace(tzinfo=ZoneInfo("UTC"))

            # Handle timezone offset
            if "+" in dt_str or dt_str.count("-") > 2:  # Has timezone
                return datetime.fromisoformat(dt_str).astimezone(ZoneInfo("UTC"))

            # Handle YYYYMMDDTHHMMSS format
            if "T" in dt_str and len(dt_str) == 15:
                dt = datetime.strptime(dt_str, "%Y%m%dT%H%M%S")
                # Assume UTC if no timezone specified
                return dt.replace(tzinfo=ZoneInfo("UTC"))

            # Handle YYYYMMDD format (date only)
            if len(dt_str) == 8:
                dt = datetime.strptime(dt_str, "%Y%m%d")
                return dt.replace(tzinfo=ZoneInfo("UTC"))

            # Fallback to fromisoformat
            dt = datetime.fromisoformat(dt_str)
            if dt.tzinfo is None:
                # Assume UTC if no timezone
                dt = dt.replace(tzinfo=ZoneInfo("UTC"))
            else:
                # Convert to UTC
                dt = dt.astimezone(ZoneInfo("UTC"))

            return dt

        except (ValueError, AttributeError) as e:
            raise ValueError(f"Unable to parse datetime: {dt_str} - {e}")
