from datetime import datetime, timezone
from caldav import Journal as CaldavJournal

from src.core.models import Journal
from src.core.models.journal import JournalDelete
from src.providers.journal_provider import JournalProvider
from src.utils.date_utils import parse_instance_date, calculate_past_days_range
from src.utils.entity_finder_utils import (
    find_calendar_by_name,
    find_journal_by_summary,
    find_journal_by_summary_and_date,
)
from src.utils.validation_utils import (
    validate_calendar_name,
    validate_journal_summary,
    validate_journal_description,
    validate_new_description,
)
from src.utils.timezone_utils import get_user_timezone
from .base import CalDavBase


class CalDavJournalService(JournalProvider):
    """CalDAV service implementation for journal/notes management operations."""

    def __init__(self, caldav_base: CalDavBase):
        """Initialize with shared CalDAV base instance."""
        self.caldav_base = caldav_base

    @property
    def calendars(self):
        """Access shared calendars from base instance."""
        return self.caldav_base.calendars

    def create_journal(
        self,
        calendar_name: str,
        summary: str,
        description: str,
        date: str | None = None,
    ) -> str:
        """Create a new journal entry in the specified calendar.

        Args:
            calendar_name (str): Name of the calendar to add the journal to
            summary (str): Journal title/summary
            description (str): Journal content/description
            date (str | None): Journal date in ISO format (YYYY-MM-DD) or None for today

        Returns:
            str: Success message with journal details

        Raises:
            ValueError: If summary/description is empty or calendar not found
            RuntimeError: If unable to create journal
        """
        validate_journal_summary(summary)
        validate_journal_description(description)
        validate_calendar_name(calendar_name)

        try:
            # Find the calendar
            target_calendar = find_calendar_by_name(self.calendars, calendar_name)

            # Parse date if provided
            original_date = date
            dtstart = None
            if not date:
                date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            try:
                dtstart = datetime.fromisoformat(date)
                # If no timezone specified, assume user's local timezone
                if dtstart.tzinfo is None:
                    user_tz = get_user_timezone()
                    dtstart = dtstart.replace(tzinfo=user_tz)
            except ValueError:
                raise ValueError(f"Invalid date format: {date}. Expected YYYY-MM-DD")

            # Create the journal entry
            target_calendar.save_journal(
                summary=summary, description=description, dtstart=dtstart
            )

            date_str = f" on {date}" if original_date else " (today)"
            return f"Journal entry created in '{calendar_name}': '{summary}'{date_str} - {description}"

        except ValueError:
            raise  # Re-raise ValueError as-is
        except Exception as e:
            raise RuntimeError(f"Failed to create journal: {e}")

    def get_journals(
        self,
        calendar_name: str | None = None,
        date: str | None = None,
        past_days: int | None = None,
    ) -> list[Journal]:
        """Get journal entries, optionally filtered by calendar name, date, or past days.

        Args:
            calendar_name (str | None): Filter journals by specific calendar name, or None for all calendars
            date (str | None): Filter journals by specific date in ISO format (YYYY-MM-DD), or None for all dates
            past_days (int | None): Filter journals from past X days including today, or None for all dates

        Returns:
            list[Journal]: List of Journal objects matching the criteria

        Raises:
            ValueError: If specified calendar not found, invalid date format, or both date and past_days are provided
            RuntimeError: If unable to fetch journals
        """
        journals = []
        try:
            # Validate mutually exclusive parameters
            if date and past_days:
                raise ValueError(
                    "Cannot specify both 'date' and 'past_days' parameters. They are mutually exclusive."
                )

            # Parse date filter if provided
            filter_date = None
            if date:
                filter_date = parse_instance_date(date).date()

            # Parse past_days filter if provided
            date_range_start = None
            date_range_end = None
            if past_days:
                if not isinstance(past_days, int) or past_days < 1:
                    raise ValueError(
                        f"past_days must be a positive integer, got: {past_days}"
                    )
                date_range_start, date_range_end = calculate_past_days_range(past_days)

            calendars_to_search = self.calendars

            # Filter to specific calendar if requested
            if calendar_name:
                target_calendar = find_calendar_by_name(self.calendars, calendar_name)
                calendars_to_search = [target_calendar]

            for cal in calendars_to_search:
                try:
                    cal_name = str(cal.name)
                    # Get all journals from the calendar
                    cal_journals = cal.journals()

                    for journal in cal_journals:
                        journal_obj = Journal.from_caldav_journal(journal, cal_name)

                        # Apply date filter if specified
                        if filter_date and journal_obj.date_utc:
                            journal_date = journal_obj.date_utc.date()
                            if journal_date != filter_date:
                                continue

                        # Apply past_days filter if specified
                        if date_range_start and date_range_end and journal_obj.date_utc:
                            journal_date = journal_obj.date_utc.date()
                            if not (date_range_start <= journal_date <= date_range_end):
                                continue

                        journals.append(journal_obj)

                except Exception as e:
                    print(
                        f"Warning: Failed to get journals from calendar '{cal.name}': {e}"
                    )
                    continue

        except ValueError:
            raise  # Re-raise date/calendar errors
        except Exception as e:
            raise RuntimeError(f"Failed to get journals: {e}")

        return journals

    def edit_journal(
        self,
        summary: str,
        calendar_name: str,
        new_description: str,
        append: bool = True,
    ) -> str:
        """Edit an existing journal entry's description.

        Args:
            summary (str): Journal summary to identify the journal
            calendar_name (str): Calendar containing the journal
            new_description (str): New description content
            append (bool): If True, append to existing description with timestamp. If False, replace entirely.

        Returns:
            str: Success message with journal details

        Raises:
            ValueError: If journal or calendar not found, or if description is empty
            RuntimeError: If unable to update journal
        """
        validate_new_description(new_description)

        try:
            # Find calendar and journal
            target_calendar = find_calendar_by_name(self.calendars, calendar_name)
            target_journal = find_journal_by_summary(target_calendar, summary)

            # Get current description using utility function
            from src.utils.vcalendar_parser import (
                get_vcalendar_property,
                update_vcalendar_property,
            )
            from src.utils.journal_utils import build_updated_description

            current_description = (
                get_vcalendar_property(target_journal.data, "DESCRIPTION") or ""
            )

            # Build updated description using journal domain logic
            updated_description = build_updated_description(
                current_description, new_description, append
            )

            # Update the journal data using utility function
            target_journal.data = update_vcalendar_property(
                target_journal.data, "DESCRIPTION", updated_description, "VJOURNAL"
            )
            target_journal.save()

            mode_str = (
                "appended to" if (append and current_description) else "updated in"
            )
            return f"Journal '{summary}' in '{calendar_name}' {mode_str}: {new_description[:50]}{'...' if len(new_description) > 50 else ''}"

        except ValueError:
            raise  # Re-raise ValueError as-is
        except Exception as e:
            raise RuntimeError(f"Failed to edit journal: {e}")

    def delete_journal(self, journal_delete: JournalDelete) -> str:
        """Delete a journal entry from the specified calendar.

        Args:
            journal_delete (JournalDelete): Journal deletion details

        Returns:
            str: Success message with journal details

        Raises:
            ValueError: If journal or calendar not found
            RuntimeError: If unable to delete journal
        """
        try:
            # Find calendar and journal
            target_calendar = find_calendar_by_name(
                self.calendars, journal_delete.calendar_name
            )
            target_journal: CaldavJournal = find_journal_by_summary_and_date(
                target_calendar, journal_delete.summary, journal_delete.date
            )

            # Delete the journal
            target_journal.delete()

            date_info = f" from {journal_delete.date}" if journal_delete.date else ""
            return f"Journal '{journal_delete.summary}'{date_info} deleted from '{journal_delete.calendar_name}'"

        except ValueError:
            raise  # Re-raise validation errors
        except Exception as e:
            raise RuntimeError(f"Failed to delete journal: {e}")
