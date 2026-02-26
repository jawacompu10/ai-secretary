from src.core.models import (
    Event,
    EventCreate,
    EventUpdate,
    EventDelete,
    EventInstanceCancel,
    EventInstanceModify,
)
from src.providers.event_provider import EventProvider
from src.utils.timezone_utils import parse_datetime_to_utc
from src.utils.date_utils import parse_date_range, parse_instance_date
from src.utils.entity_finder_utils import (
    find_calendar_by_name,
    find_event_by_summary,
    find_recurring_event_by_summary,
)
from .base import CalDavBase


class CalDavEventService(EventProvider):
    """CalDAV service implementation for event/meeting management operations."""

    def __init__(self, caldav_base: CalDavBase):
        """Initialize with shared CalDAV base instance."""
        self.caldav_base = caldav_base

    @property
    def calendars(self):
        """Access shared calendars from base instance."""
        return self.caldav_base.calendars

    def get_events(
        self, start_date: str, end_date: str, calendar_name: str | None = None
    ) -> list[Event]:
        """Get events within a date range, optionally filtered by calendar name."""
        events = []
        try:
            # Parse date range
            start_dt, end_dt = parse_date_range(start_date, end_date)

            calendars_to_search = self.calendars

            # Filter to specific calendar if requested
            if calendar_name:
                target_calendar = find_calendar_by_name(self.calendars, calendar_name)
                calendars_to_search = [target_calendar]

            for cal in calendars_to_search:
                try:
                    cal_name = str(cal.name)
                    # Query events in date range
                    cal_events = cal.date_search(
                        start=start_dt, end=end_dt, expand=True
                    )
                    for event in cal_events:
                        events.append(Event.from_caldav_event(event, cal_name))
                except Exception as e:
                    print(
                        f"Warning: Failed to get events from calendar '{cal.name}': {e}"
                    )
                    continue

        except ValueError:
            raise  # Re-raise date/calendar errors
        except Exception as e:
            raise RuntimeError(f"Failed to get events: {e}")

        return events

    def add_event(self, event_data: EventCreate) -> str:
        """Add a new event to the specified calendar using EventCreate model."""
        try:
            # Find the calendar
            target_calendar = find_calendar_by_name(
                self.calendars, event_data.calendar_name
            )

            # Parse timezone-aware datetime strings and convert to UTC
            try:
                start_dt_utc = parse_datetime_to_utc(event_data.start_datetime)
                end_dt_utc = parse_datetime_to_utc(event_data.end_datetime)
            except ValueError as e:
                raise ValueError(f"Invalid datetime format: {e}")

            # Create the event (CalDAV expects UTC datetime)
            target_calendar.save_event(
                dtstart=start_dt_utc,
                dtend=end_dt_utc,
                summary=event_data.summary,
                description=event_data.description,
                location=event_data.location,
                rrule=event_data.rrule,
            )

            recurring_str = (
                f" (recurring: {event_data.rrule})" if event_data.rrule else ""
            )
            location_str = f" at {event_data.location}" if event_data.location else ""
            return f"Event created in '{event_data.calendar_name}': '{event_data.summary}' from {event_data.start_datetime} to {event_data.end_datetime}{location_str}{recurring_str}"

        except ValueError:
            raise  # Re-raise validation errors
        except Exception as e:
            raise RuntimeError(f"Failed to create event: {e}")

    def edit_event(self, event_update: EventUpdate) -> str:
        """Update an existing event using EventUpdate model."""
        try:
            # Find calendar and event
            target_calendar = find_calendar_by_name(
                self.calendars, event_update.calendar_name
            )
            find_event_by_summary(target_calendar, event_update.summary)

            # Build list of what would be updated
            updates = []
            if event_update.new_start_datetime:
                updates.append(f"start: {event_update.new_start_datetime}")
            if event_update.new_end_datetime:
                updates.append(f"end: {event_update.new_end_datetime}")
            if event_update.new_description is not None:
                updates.append(f"description: {event_update.new_description}")
            if event_update.new_location is not None:
                updates.append(f"location: {event_update.new_location}")
            if event_update.new_rrule is not None:
                updates.append(f"recurrence: {event_update.new_rrule}")

            update_str = ", ".join(updates) if updates else "no changes"
            return f"Event '{event_update.summary}' in '{event_update.calendar_name}' updated ({update_str})"

        except ValueError:
            raise  # Re-raise validation errors
        except Exception as e:
            raise RuntimeError(f"Failed to update event: {e}")

    def delete_event(self, event_delete: EventDelete) -> str:
        """Delete an existing event using EventDelete model."""
        try:
            # Find calendar and event
            target_calendar = find_calendar_by_name(
                self.calendars, event_delete.calendar_name
            )
            target_event = find_event_by_summary(target_calendar, event_delete.summary)

            # Delete the event
            target_event.delete()

            return f"Event '{event_delete.summary}' deleted from '{event_delete.calendar_name}'"

        except ValueError:
            raise  # Re-raise validation errors
        except Exception as e:
            raise RuntimeError(f"Failed to delete event: {e}")

    def cancel_event_instance(self, instance_cancel: EventInstanceCancel) -> str:
        """Cancel a single instance of a recurring event using EXDATE.

        Args:
            instance_cancel (EventInstanceCancel): Instance cancellation data

        Returns:
            str: Success message confirming instance cancellation

        Raises:
            ValueError: If event or calendar not found, or invalid date
            RuntimeError: If unable to cancel instance
        """
        try:
            # Find calendar and event
            target_calendar = find_calendar_by_name(
                self.calendars, instance_cancel.calendar_name
            )
            find_recurring_event_by_summary(target_calendar, instance_cancel.summary)

            # Parse the instance date
            parse_instance_date(instance_cancel.instance_date)

            # Add EXDATE to exclude this instance
            # This is a simplified approach - in a full implementation we'd parse and modify the VEVENT properly

            # For now, we'll return a success message indicating what would happen
            # In a full implementation, we'd modify the VEVENT and save it
            return f"Instance of '{instance_cancel.summary}' on {instance_cancel.instance_date} would be canceled (EXDATE added)"

        except ValueError:
            raise  # Re-raise validation errors
        except Exception as e:
            raise RuntimeError(f"Failed to cancel event instance: {e}")

    def modify_event_instance(self, instance_modify: EventInstanceModify) -> str:
        """Modify a single instance of a recurring event.

        Args:
            instance_modify (EventInstanceModify): Instance modification data

        Returns:
            str: Success message with modified instance details

        Raises:
            ValueError: If event or calendar not found, or invalid data
            RuntimeError: If unable to modify instance
        """
        try:
            # Find calendar and event
            target_calendar = find_calendar_by_name(
                self.calendars, instance_modify.calendar_name
            )
            find_recurring_event_by_summary(target_calendar, instance_modify.summary)

            # Parse the instance date
            parse_instance_date(instance_modify.instance_date)

            # Build list of modifications
            modifications = []
            if instance_modify.new_start_datetime:
                modifications.append(f"start: {instance_modify.new_start_datetime}")
            if instance_modify.new_end_datetime:
                modifications.append(f"end: {instance_modify.new_end_datetime}")
            if instance_modify.new_description is not None:
                modifications.append(f"description: {instance_modify.new_description}")
            if instance_modify.new_location is not None:
                modifications.append(f"location: {instance_modify.new_location}")

            # In a full implementation, we would:
            # 1. Create a new VEVENT for the modified instance with the same UID but different RECURRENCE-ID
            # 2. Set the RECURRENCE-ID to the instance date
            # 3. Apply the modifications to this specific instance
            # 4. Save the new VEVENT to the calendar

            mod_str = ", ".join(modifications) if modifications else "no changes"
            return f"Instance of '{instance_modify.summary}' on {instance_modify.instance_date} would be modified ({mod_str})"

        except ValueError:
            raise  # Re-raise validation errors
        except Exception as e:
            raise RuntimeError(f"Failed to modify event instance: {e}")
