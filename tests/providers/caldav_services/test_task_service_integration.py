"""
Integration tests for src.providers.caldav.task_service module.
Tests against real CalDAV server without mocking to verify icalendar library fixes.
"""

import pytest
from src.providers.caldav_provider import create_calendar_provider
from src.core.models.task import TaskDelete, TaskStatusChange


TEST_CALENDAR_NAME = "Calendar For Automated Tests"


@pytest.fixture(scope="class")
def caldav_service():
    """Create a real CalDAV service instance."""
    try:
        service = create_calendar_provider()
        return service
    except Exception as e:
        pytest.skip(f"CalDAV server not available: {e}")


@pytest.fixture(scope="class", autouse=True)
def setup_test_calendar(caldav_service):
    """Ensure test calendar exists before running tests."""
    try:
        # Check if test calendar already exists
        calendar_names = caldav_service.get_all_calendar_names()

        if TEST_CALENDAR_NAME not in calendar_names:
            # Create the test calendar
            caldav_service.create_new_calendar(TEST_CALENDAR_NAME)
            print(f"Created test calendar: {TEST_CALENDAR_NAME}")
        else:
            print(f"Using existing test calendar: {TEST_CALENDAR_NAME}")

    except Exception as e:
        pytest.skip(f"Unable to setup test calendar: {e}")


@pytest.fixture(autouse=True)
def cleanup_test_tasks(caldav_service):
    """Clean up test tasks after each test."""
    # Let the test run first
    yield

    try:
        # Get all tasks from test calendar
        tasks = caldav_service.get_tasks(calendar_name=TEST_CALENDAR_NAME, include_completed=True)

        # Delete any tasks created during testing
        for task in tasks:
            if task.summary and task.summary.startswith("Test Integration Task"):
                try:
                    task_delete = TaskDelete(
                        calendar_name=TEST_CALENDAR_NAME,
                        summary=task.summary,
                    )
                    caldav_service.delete_task(task_delete)
                except Exception as e:
                    print(
                        f"Warning: Could not delete test task '{task.summary}': {e}"
                    )

    except Exception as e:
        print(f"Warning: Could not clean up test tasks: {e}")


class TestCalDavTaskServiceIntegrationLineBreaks:
    """Integration tests specifically for verifying icalendar library fixes line break issues."""

    def test_task_with_long_summary_finder_functions(self, caldav_service):
        """Test that tasks with long summaries can be found correctly by finder functions.
        
        This is the critical test to verify our icalendar library fix works.
        Previously, CalDAV line folding would break find_task_by_summary.
        """
        # Create a task with a long summary that CalDAV servers might wrap
        long_summary = "Test Integration Task - This is a very long task summary that might be wrapped by CalDAV servers when they store it and could cause line break issues"
        test_description = "Testing that long summaries work with icalendar library fixes"

        # Create the task
        result = caldav_service.add_task(
            summary=long_summary,
            calendar_name=TEST_CALENDAR_NAME,
            description=test_description,
        )

        # Verify creation success
        assert "Task created" in result
        assert TEST_CALENDAR_NAME in result
        assert long_summary in result

        # Critical test: Retrieve tasks and verify finder functions work
        tasks = caldav_service.get_tasks(calendar_name=TEST_CALENDAR_NAME)

        # Find our test task using exact summary matching (this was broken before icalendar fix)
        found_task = None
        for task in tasks:
            if task.summary == long_summary:
                found_task = task
                break

        # Verify task was found with exact summary match
        assert found_task is not None, f"Task with long summary not found. Available summaries: {[t.summary for t in tasks if t.summary.startswith('Test')]}"
        assert found_task.summary == long_summary, "Summary doesn't match exactly"
        assert found_task.description == test_description
        assert found_task.calendar_name == TEST_CALENDAR_NAME

        # Verify no line break artifacts in summary
        assert "\n" not in found_task.summary, f"Found line breaks in summary: {repr(found_task.summary)}"

    def test_task_with_special_characters_and_line_breaks(self, caldav_service):
        """Test tasks with special characters and potential line break scenarios."""
        # Create task with special characters and long content
        special_summary = "Test Integration Task - Special chars: émojis 🎉, ñáéíóú @#$%"
        special_description = "Testing with special characters that might cause issues: \n\nMultiple lines\nAnd émojis 🎉"

        # Create the task
        result = caldav_service.add_task(
            summary=special_summary,
            calendar_name=TEST_CALENDAR_NAME,
            description=special_description,
        )

        # Verify creation
        assert "Task created" in result

        # Retrieve and verify exact matching works
        tasks = caldav_service.get_tasks(calendar_name=TEST_CALENDAR_NAME)
        found_task = None
        for task in tasks:
            if task.summary == special_summary:
                found_task = task
                break

        # Verify special characters are preserved correctly
        if found_task is None:
            print(f"Expected summary: {repr(special_summary)}")
            print("Available task summaries:")
            for task in tasks:
                if task.summary and "Test Integration Task" in task.summary:
                    print(f"  - {repr(task.summary)}")
        assert found_task is not None, "Task with special characters not found"
        assert found_task.summary == special_summary
        assert "émojis 🎉" in found_task.summary, "Emoji not preserved in summary"
        assert "ñáéíóú" in found_task.summary, "Special characters not preserved"

        # Verify description preserves intentional line breaks (handle CalDAV escaping)
        # CalDAV may escape newlines as \n, so normalize for comparison
        normalized_desc = found_task.description.replace('\\n', '\n') if found_task.description else ""
        assert normalized_desc == special_description, f"Description mismatch: {repr(found_task.description)} vs {repr(special_description)}"
        # Verify line breaks are present in some form
        assert '\n' in normalized_desc or '\\n' in found_task.description, "Line breaks should be preserved in description"

    def test_multiple_tasks_exact_summary_matching(self, caldav_service):
        """Test that multiple tasks can be distinguished by exact summary matching."""
        base_summary = "Test Integration Task - Similar"
        tasks_to_create = [
            f"{base_summary} One",
            f"{base_summary} Two", 
            f"{base_summary} Three with a much longer summary that might be wrapped",
        ]

        # Create multiple tasks
        for summary in tasks_to_create:
            result = caldav_service.add_task(
                summary=summary,
                calendar_name=TEST_CALENDAR_NAME,
                description=f"Description for {summary}",
            )
            assert "Task created" in result

        # Retrieve all tasks
        tasks = caldav_service.get_tasks(calendar_name=TEST_CALENDAR_NAME)

        # Verify each task can be found by exact summary match
        for expected_summary in tasks_to_create:
            found_task = None
            for task in tasks:
                if task.summary == expected_summary:
                    found_task = task
                    break
            
            assert found_task is not None, f"Could not find task with summary: {expected_summary}"
            assert found_task.summary == expected_summary, "Summary match failed"

    def test_task_editing_with_long_summary(self, caldav_service):
        """Test that task editing works with long summaries (relies on finder functions)."""
        # Create a task with long summary
        long_summary = "Test Integration Task - Edit Test With Very Long Summary That May Be Wrapped By CalDAV Server"
        
        result = caldav_service.add_task(
            summary=long_summary,
            calendar_name=TEST_CALENDAR_NAME,
            description="Original description",
            due_date="2025-12-31"
        )
        assert "Task created" in result

        # Try to edit the task's due date (this uses find_task_by_summary internally)
        try:
            edit_result = caldav_service.edit_due_date(
                summary=long_summary,
                calendar_name=TEST_CALENDAR_NAME,
                new_due_date="2025-06-15"
            )
            
            # If this succeeds, the finder function worked correctly
            assert "Updated due date" in edit_result or "due date updated" in edit_result
            assert "2025-06-15" in edit_result
            
        except ValueError as e:
            if "not found" in str(e):
                pytest.fail(f"Task editing failed because finder function couldn't locate task: {e}")
            else:
                raise

    def test_task_completion_with_long_summary(self, caldav_service):
        """Test that task completion works with long summaries."""
        # Create a task with long summary
        long_summary = "Test Integration Task - Complete Test With Very Long Summary That May Be Wrapped"
        
        result = caldav_service.add_task(
            summary=long_summary,
            calendar_name=TEST_CALENDAR_NAME,
            description="Task to be completed",
        )
        assert "Task created" in result

        # Try to complete the task (this uses find_task_by_summary internally)
        try:
            complete_result = caldav_service.complete_task(
                summary=long_summary,
                calendar_name=TEST_CALENDAR_NAME,
            )
            
            # If this succeeds, the finder function worked correctly
            assert "completed" in complete_result.lower()
            
        except ValueError as e:
            if "not found" in str(e):
                pytest.fail(f"Task completion failed because finder function couldn't locate task: {e}")
            else:
                raise

    def test_task_status_change_with_long_summary(self, caldav_service):
        """Test that task status changes work with long summaries and verify icalendar_component fix."""
        # Create a task with long summary
        long_summary = "Test Integration Task - Status Change Test With Very Long Summary That May Be Wrapped By CalDAV Server"
        
        result = caldav_service.add_task(
            summary=long_summary,
            calendar_name=TEST_CALENDAR_NAME,
            description="Task for testing status changes",
        )
        assert "Task created" in result

        # Test 1: Change status to IN-PROCESS (tests our icalendar_component fix)
        try:
            status_change = TaskStatusChange(
                summary=long_summary,
                calendar_name=TEST_CALENDAR_NAME,
                new_status="IN-PROCESS"
            )
            
            change_result = caldav_service.change_status(status_change)
            assert "status changed to 'IN-PROCESS'" in change_result
            
            # Verify the status change by retrieving tasks
            tasks = caldav_service.get_tasks(calendar_name=TEST_CALENDAR_NAME)
            found_task = None
            for task in tasks:
                if task.summary == long_summary:
                    found_task = task
                    break
            
            assert found_task is not None, "Task not found after status change to IN-PROCESS"
            assert found_task.status == "IN-PROCESS", f"Expected status IN-PROCESS, got {found_task.status}"
            
        except ValueError as e:
            if "not found" in str(e):
                pytest.fail(f"Status change to IN-PROCESS failed because finder function couldn't locate task: {e}")
            else:
                raise

        # Test 2: Change status to COMPLETED (tests existing complete() method)
        try:
            status_change = TaskStatusChange(
                summary=long_summary,
                calendar_name=TEST_CALENDAR_NAME,
                new_status="COMPLETED"
            )
            
            change_result = caldav_service.change_status(status_change)
            assert "status changed to 'COMPLETED'" in change_result
            
            # Verify the status change by retrieving tasks (including completed ones)
            tasks = caldav_service.get_tasks(calendar_name=TEST_CALENDAR_NAME, include_completed=True)
            found_task = None
            for task in tasks:
                if task.summary == long_summary:
                    found_task = task
                    break
            
            assert found_task is not None, "Task not found after status change to COMPLETED"
            assert found_task.status == "COMPLETED", f"Expected status COMPLETED, got {found_task.status}"
            assert found_task.completed is True, "Task should be marked as completed"
            
        except ValueError as e:
            if "not found" in str(e):
                pytest.fail(f"Status change to COMPLETED failed because finder function couldn't locate task: {e}")
            else:
                raise

        # Test 3: Change status back to NEEDS-ACTION (tests icalendar_component fix again)
        try:
            status_change = TaskStatusChange(
                summary=long_summary,
                calendar_name=TEST_CALENDAR_NAME,
                new_status="NEEDS-ACTION"
            )
            
            change_result = caldav_service.change_status(status_change)
            assert "status changed to 'NEEDS-ACTION'" in change_result
            
            # Verify the status change by retrieving tasks
            tasks = caldav_service.get_tasks(calendar_name=TEST_CALENDAR_NAME, include_completed=True)
            found_task = None
            for task in tasks:
                if task.summary == long_summary:
                    found_task = task
                    break
            
            assert found_task is not None, "Task not found after status change to NEEDS-ACTION"
            assert found_task.status == "NEEDS-ACTION", f"Expected status NEEDS-ACTION, got {found_task.status}"
            assert found_task.completed is False, "Task should not be marked as completed"
            
        except ValueError as e:
            if "not found" in str(e):
                pytest.fail(f"Status change to NEEDS-ACTION failed because finder function couldn't locate task: {e}")
            else:
                raise