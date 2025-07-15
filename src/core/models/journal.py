from datetime import datetime
from zoneinfo import ZoneInfo
from caldav.calendarobjectresource import Journal as CalDavJournal
from pydantic import BaseModel, Field

from src.utils.vcalendar_parser import vcalendar_to_dict
from src.utils.timezone_utils import format_datetime_for_user


class Journal(BaseModel):
    """Journal model representing a calendar journal entry."""

    summary: str = Field(..., description="Journal title/summary")
    description: str | None = Field(
        default=None, description="Journal content/description"
    )
    calendar_name: str = Field(
        ..., description="Name of the calendar containing this journal"
    )
    date_utc: datetime | None = Field(
        default=None, description="Journal date in UTC (internal storage)"
    )
    date_local: str | None = Field(
        default=None, description="Journal date in user's timezone (for display)"
    )
    status: str | None = Field(default=None, description="Journal status")

    @classmethod
    def from_caldav_journal(cls, journal: CalDavJournal, calendar_name: str):
        """Create Journal from CalDAV journal object with proper timezone handling."""
        props = vcalendar_to_dict(journal.data)

        # Parse date field and convert to UTC
        date_dt_utc = None

        if "DTSTART" in props:
            try:
                date_str = props["DTSTART"]
                date_dt_utc = cls._parse_caldav_datetime(date_str)
            except (ValueError, AttributeError):
                pass

        return cls(
            summary=props.get("SUMMARY", "Untitled Journal"),
            description=props.get("DESCRIPTION"),
            calendar_name=calendar_name,
            date_utc=date_dt_utc,
            date_local=format_datetime_for_user(date_dt_utc),
            status=props.get("STATUS"),
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


class JournalDelete(BaseModel):
    """Model for deleting a journal entry."""

    summary: str = Field(..., description="Journal summary to identify the journal")
    calendar_name: str = Field(..., description="Calendar containing the journal")
    date: str | None = Field(None, description="Journal date in ISO format (YYYY-MM-DD) to distinguish between journals with same summary")
