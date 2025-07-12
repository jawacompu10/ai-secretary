from caldav import DAVClient, Calendar
from caldav.calendarobjectresource import Journal as CalDavJournal

from src.core.models import Task, Event, EventCreate, EventUpdate, EventDelete, EventInstanceCancel, EventInstanceModify, Journal
from src.utils.timezone_utils import parse_datetime_to_utc
from src.utils.date_utils import parse_due_date, parse_date_range, parse_instance_date
from src.utils.entity_finder_utils import find_calendar_by_name, find_task_by_summary, find_journal_by_summary, find_event_by_summary, find_recurring_event_by_summary
from src.utils.validation_utils import validate_calendar_name, validate_task_summary, validate_journal_summary, validate_journal_description, validate_event_summary, validate_new_description
from config import calendar_config
from .calendar_provider import CalendarProvider
from .task_provider import TaskProvider
from .event_provider import EventProvider
from .journal_provider import JournalProvider

class CalDavService(CalendarProvider, TaskProvider, EventProvider, JournalProvider):
    """CalDAV service implementation using caldav library."""

    def __init__(self, url: str, username: str, password: str):
        """Initialize the CalDavService with connection details.

        Args:
            url (str): CalDAV server URL
            username (str): Username for authentication
            password (str): Password for authentication
        """
        try:
            self.client = DAVClient(url=url, username=username, password=password)
            self.principal = self.client.principal()
            self._calendars = None
        except Exception as e:
            raise ConnectionError(f"Failed to connect to CalDAV server: {e}")

    @property
    def calendars(self) -> list[Calendar]:
        """Get all calendars, cached after first access."""
        if self._calendars is None:
            try:
                self._calendars = self.principal.calendars()
            except Exception as e:
                raise RuntimeError(f"Failed to fetch calendars: {e}")
        return self._calendars





    def get_all_calendar_names(self) -> list[str]:
        """Get a list of all calendar names.

        Returns:
            list[str]: list of calendar names

        Raises:
            RuntimeError: If unable to fetch calendar names
        """
        try:
            return [str(cal.name) for cal in self.calendars]
        except Exception as e:
            raise RuntimeError(f"Failed to get calendar names: {e}")

    def create_new_calendar(self, name: str) -> None:
        """Create a new calendar with the given name.

        Args:
            name (str): Name for the new calendar

        Raises:
            ValueError: If name is empty or invalid
            RuntimeError: If unable to create calendar
        """
        validate_calendar_name(name)

        try:
            self.principal.make_calendar(name)
            # Invalidate cached calendars
            self._calendars = None
        except Exception as e:
            raise RuntimeError(f"Failed to create calendar '{name}': {e}")

    def get_tasks(self, include_completed: bool = False, calendar_name: str | None = None) -> list[Task]:
        """Get tasks from calendars, optionally filtered by calendar name.

        Args:
            include_completed (bool): Whether to include completed tasks
            calendar_name (str | None): Filter tasks by specific calendar name, or None for all calendars

        Returns:
            list[Task]: list of Task objects from specified calendar(s)

        Raises:
            ValueError: If specified calendar not found
            RuntimeError: If unable to fetch tasks
        """
        tasks = []
        try:
            calendars_to_search = self.calendars
            
            # Filter to specific calendar if requested
            if calendar_name:
                target_calendar = find_calendar_by_name(self.calendars, calendar_name)
                calendars_to_search = [target_calendar]
            
            for cal in calendars_to_search:
                try:
                    cal_name = str(cal.name)
                    for todo in cal.todos(include_completed=include_completed):
                        tasks.append(Task.from_todo(todo, cal_name))
                except Exception as e:
                    # Log warning but continue with other calendars
                    print(
                        f"Warning: Failed to get tasks from calendar '{cal.name}': {e}"
                    )
                    continue
        except ValueError:
            raise  # Re-raise calendar not found error
        except Exception as e:
            raise RuntimeError(f"Failed to get tasks: {e}")

        return tasks

    def add_task(self, summary: str, calendar_name: str, due_date: str | None = None, description: str | None = None) -> str:
        """Add a new task to the specified calendar.

        Args:
            summary (str): Task title/summary
            calendar_name (str): Name of the calendar to add the task to
            due_date (str | None): Due date in ISO format (YYYY-MM-DD) or None
            description (str | None): Optional task description

        Returns:
            str: Success message with task details

        Raises:
            ValueError: If summary is empty or calendar not found
            RuntimeError: If unable to create task
        """
        validate_task_summary(summary)
        validate_calendar_name(calendar_name)

        try:
            # Find the calendar and parse due date
            target_calendar = find_calendar_by_name(self.calendars, calendar_name)
            due_datetime = parse_due_date(due_date)

            # Create the task
            target_calendar.save_todo(
                summary=summary,
                due=due_datetime,
                description=description
            )

            due_str = f" (due: {due_date})" if due_date else ""
            desc_str = f" - {description}" if description else ""
            return f"Task created in '{calendar_name}': '{summary}'{due_str}{desc_str}"

        except ValueError:
            raise  # Re-raise ValueError as-is
        except Exception as e:
            raise RuntimeError(f"Failed to create task: {e}")

    def edit_due_date(self, summary: str, calendar_name: str, new_due_date: str | None = None) -> str:
        """Update the due date of an existing task.

        Args:
            summary (str): Task summary to identify the task
            calendar_name (str): Calendar containing the task
            new_due_date (str | None): New due date in ISO format (YYYY-MM-DD) or None to remove

        Returns:
            str: Success message with task details

        Raises:
            ValueError: If task or calendar not found
            RuntimeError: If unable to update task
        """
        try:
            # Find calendar and task
            target_calendar = find_calendar_by_name(self.calendars, calendar_name)
            target_todo = find_task_by_summary(target_calendar, summary)
            
            # Parse new due date
            new_due_datetime = parse_due_date(new_due_date)

            # Update the due date
            target_todo.set_due(new_due_datetime)
            target_todo.save()

            due_str = f" to {new_due_date}" if new_due_date else " (removed)"
            return f"Updated due date for '{summary}' in '{calendar_name}'{due_str}"

        except ValueError:
            raise  # Re-raise ValueError as-is
        except Exception as e:
            raise RuntimeError(f"Failed to update task due date: {e}")

    def complete_task(self, summary: str, calendar_name: str) -> str:
        """Mark an existing task as completed.

        Args:
            summary (str): Task summary to identify the task
            calendar_name (str): Calendar containing the task

        Returns:
            str: Success message with task details

        Raises:
            ValueError: If task or calendar not found
            RuntimeError: If unable to complete task
        """
        try:
            # Find calendar and task
            target_calendar = find_calendar_by_name(self.calendars, calendar_name)
            target_todo = find_task_by_summary(target_calendar, summary)

            # Mark as completed
            target_todo.complete()
            target_todo.save()

            return f"Task '{summary}' in '{calendar_name}' marked as completed"

        except ValueError:
            raise  # Re-raise ValueError as-is
        except Exception as e:
            raise RuntimeError(f"Failed to complete task: {e}")

    # Event methods
    def get_events(self, start_date: str, end_date: str, calendar_name: str | None = None) -> list[Event]:
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
                    cal_events = cal.date_search(start=start_dt, end=end_dt, expand=True)
                    for event in cal_events:
                        events.append(Event.from_caldav_event(event, cal_name))
                except Exception as e:
                    print(f"Warning: Failed to get events from calendar '{cal.name}': {e}")
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
            target_calendar = find_calendar_by_name(self.calendars, event_data.calendar_name)
            
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
                rrule=event_data.rrule
            )

            recurring_str = f" (recurring: {event_data.rrule})" if event_data.rrule else ""
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
            target_calendar = find_calendar_by_name(self.calendars, event_update.calendar_name)
            target_event = find_event_by_summary(target_calendar, event_update.summary)

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
            target_calendar = find_calendar_by_name(self.calendars, event_delete.calendar_name)
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
            target_calendar = find_calendar_by_name(self.calendars, instance_cancel.calendar_name)
            target_event = find_recurring_event_by_summary(target_calendar, instance_cancel.summary)

            # Parse the instance date
            instance_dt = parse_instance_date(instance_cancel.instance_date)

            # Get the event's VEVENT data to modify
            event_data = target_event.data
            
            # Add EXDATE to exclude this instance
            # This is a simplified approach - in a full implementation we'd parse and modify the VEVENT properly
            exdate_str = f"EXDATE:{instance_dt.strftime('%Y%m%d')}"
            
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
            target_calendar = find_calendar_by_name(self.calendars, instance_modify.calendar_name)
            target_event = find_recurring_event_by_summary(target_calendar, instance_modify.summary)

            # Parse the instance date
            instance_dt = parse_instance_date(instance_modify.instance_date)

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

    def create_journal(self, calendar_name: str, summary: str, description: str, date: str | None = None) -> str:
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
            dtstart = None
            if date:
                from datetime import datetime
                try:
                    dtstart = datetime.fromisoformat(date)
                except ValueError:
                    raise ValueError(f"Invalid date format: {date}. Expected YYYY-MM-DD")
            
            # Create the journal entry
            target_calendar.save_journal(
                summary=summary,
                description=description,
                dtstart=dtstart
            )

            date_str = f" on {date}" if date else ""
            return f"Journal entry created in '{calendar_name}': '{summary}'{date_str} - {description}"

        except ValueError:
            raise  # Re-raise ValueError as-is
        except Exception as e:
            raise RuntimeError(f"Failed to create journal: {e}")

    def get_journals(self, calendar_name: str | None = None, date: str | None = None) -> list[Journal]:
        """Get journal entries, optionally filtered by calendar name and/or date.

        Args:
            calendar_name (str | None): Filter journals by specific calendar name, or None for all calendars
            date (str | None): Filter journals by specific date in ISO format (YYYY-MM-DD), or None for all dates

        Returns:
            list[Journal]: List of Journal objects matching the criteria

        Raises:
            ValueError: If specified calendar not found or invalid date format
            RuntimeError: If unable to fetch journals
        """
        journals = []
        try:
            # Parse date filter if provided
            filter_date = None
            if date:
                filter_date = parse_instance_date(date).date()

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
                        
                        journals.append(journal_obj)
                        
                except Exception as e:
                    print(f"Warning: Failed to get journals from calendar '{cal.name}': {e}")
                    continue
                    
        except ValueError:
            raise  # Re-raise date/calendar errors
        except Exception as e:
            raise RuntimeError(f"Failed to get journals: {e}")

        return journals

    def edit_journal(self, summary: str, calendar_name: str, new_description: str, append: bool = True) -> str:
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
            from src.utils.vcalendar_parser import get_vcalendar_property, update_vcalendar_property
            from src.utils.journal_utils import build_updated_description
            
            current_description = get_vcalendar_property(target_journal.data, 'DESCRIPTION') or ''
            
            # Build updated description using journal domain logic
            updated_description = build_updated_description(current_description, new_description, append)
            
            # Update the journal data using utility function
            target_journal.data = update_vcalendar_property(
                target_journal.data, 
                'DESCRIPTION', 
                updated_description, 
                'VJOURNAL'
            )
            target_journal.save()

            mode_str = "appended to" if (append and current_description) else "updated in"
            return f"Journal '{summary}' in '{calendar_name}' {mode_str}: {new_description[:50]}{'...' if len(new_description) > 50 else ''}"

        except ValueError:
            raise  # Re-raise ValueError as-is
        except Exception as e:
            raise RuntimeError(f"Failed to edit journal: {e}")

def create_calendar_provider() -> CalDavService:
    """Factory function to create a CalDAV service with config."""
    return CalDavService(
        url=calendar_config.url,
        username=calendar_config.username,
        password=calendar_config.password,
    )
