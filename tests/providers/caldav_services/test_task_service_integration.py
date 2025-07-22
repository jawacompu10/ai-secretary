"""
Integration tests for src.providers.caldav.task_service module.
Tests against real CalDAV server without mocking to verify icalendar library fixes.
"""

import pytest
from src.providers.caldav_provider import create_calendar_provider
from src.core.models.task import TaskDelete, TaskStatusChange, TaskQuery


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
        tasks = caldav_service.get_tasks(
            query=TaskQuery(calendar_name=TEST_CALENDAR_NAME, include_completed=True)
        )

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
        tasks = caldav_service.get_tasks(
            query=TaskQuery(calendar_name=TEST_CALENDAR_NAME)
        )

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
        tasks = caldav_service.get_tasks(
            query=TaskQuery(calendar_name=TEST_CALENDAR_NAME)
        )
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
        tasks = caldav_service.get_tasks(
            query=TaskQuery(calendar_name=TEST_CALENDAR_NAME)
        )

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
            tasks = caldav_service.get_tasks(
                query=TaskQuery(calendar_name=TEST_CALENDAR_NAME)
            )
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
            tasks = caldav_service.get_tasks(
                query=TaskQuery(calendar_name=TEST_CALENDAR_NAME, include_completed=True)
            )
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
            tasks = caldav_service.get_tasks(
                query=TaskQuery(calendar_name=TEST_CALENDAR_NAME, include_completed=True)
            )
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


class TestCalDavTaskServiceIntegrationFutureDays:
    """Integration tests for get_tasks with future_days parameter."""

    def test_get_tasks_future_days_filtering(self, caldav_service):
        """Test that future_days parameter correctly filters tasks."""
        from datetime import date, timedelta
        
        # Create tasks with different due dates
        today = date.today()
        
        tasks_to_create = [
            {
                "summary": "Test Integration Task - Future 2 days",
                "due_date": (today + timedelta(days=2)).isoformat(),
                "description": "Task due in 2 days"
            },
            {
                "summary": "Test Integration Task - Future 5 days", 
                "due_date": (today + timedelta(days=5)).isoformat(),
                "description": "Task due in 5 days"
            },
            {
                "summary": "Test Integration Task - Future 10 days",
                "due_date": (today + timedelta(days=10)).isoformat(), 
                "description": "Task due in 10 days"
            },
            {
                "summary": "Test Integration Task - Past 2 days",
                "due_date": (today - timedelta(days=2)).isoformat(),
                "description": "Task due 2 days ago"
            },
            {
                "summary": "Test Integration Task - No due date",
                "due_date": None,
                "description": "Task without due date"
            }
        ]
        
        # Create all test tasks
        for task_data in tasks_to_create:
            result = caldav_service.add_task(
                summary=task_data["summary"],
                calendar_name=TEST_CALENDAR_NAME,
                due_date=task_data["due_date"],
                description=task_data["description"]
            )
            assert "Task created" in result

        # Test future_days=7 (should include tasks due in 2 and 5 days, plus no due date task)
        tasks_future_7 = caldav_service.get_tasks(
            query=TaskQuery(calendar_name=TEST_CALENDAR_NAME, future_days=7)
        )
        
        future_7_summaries = {task.summary for task in tasks_future_7 if task.summary.startswith("Test Integration Task")}
        expected_future_7 = {
            "Test Integration Task - Future 2 days",
            "Test Integration Task - Future 5 days", 
            "Test Integration Task - No due date"
        }
        assert expected_future_7.issubset(future_7_summaries), f"Expected {expected_future_7}, got {future_7_summaries}"

        # Test future_days=3 (should include only task due in 2 days, plus no due date task)
        tasks_future_3 = caldav_service.get_tasks(
            query=TaskQuery(calendar_name=TEST_CALENDAR_NAME, future_days=3)
        )
        
        future_3_summaries = {task.summary for task in tasks_future_3 if task.summary.startswith("Test Integration Task")}
        expected_future_3 = {
            "Test Integration Task - Future 2 days",
            "Test Integration Task - No due date"
        }
        assert expected_future_3.issubset(future_3_summaries), f"Expected {expected_future_3}, got {future_3_summaries}"
        
        # Verify exclusions for future_days=3
        excluded_from_future_3 = {
            "Test Integration Task - Future 5 days",
            "Test Integration Task - Future 10 days",
            "Test Integration Task - Past 2 days"
        }
        assert excluded_from_future_3.isdisjoint(future_3_summaries), f"Should not include {excluded_from_future_3 & future_3_summaries}"

        # Test future_days=15 (should include all future tasks and no due date task)
        tasks_future_15 = caldav_service.get_tasks(
            query=TaskQuery(calendar_name=TEST_CALENDAR_NAME, future_days=15)
        )
        
        future_15_summaries = {task.summary for task in tasks_future_15 if task.summary.startswith("Test Integration Task")}
        expected_future_15 = {
            "Test Integration Task - Future 2 days",
            "Test Integration Task - Future 5 days",
            "Test Integration Task - Future 10 days",
            "Test Integration Task - No due date"
        }
        assert expected_future_15.issubset(future_15_summaries), f"Expected {expected_future_15}, got {future_15_summaries}"
        
        # Should still exclude past tasks
        assert "Test Integration Task - Past 2 days" not in future_15_summaries

    def test_get_tasks_future_days_validation(self, caldav_service):
        """Test that future_days parameter validation works correctly."""
        # Test that both past_days and future_days cannot be specified
        with pytest.raises(ValueError, match="Cannot specify both past_days and future_days filters"):
            TaskQuery(
                calendar_name=TEST_CALENDAR_NAME,
                past_days=7,
                future_days=7
            )

        # Test that invalid future_days values raise errors
        invalid_values = [0, -1, -10]
        for invalid_value in invalid_values:
            with pytest.raises(ValueError, match="Days must be a positive integer"):
                TaskQuery(
                    calendar_name=TEST_CALENDAR_NAME,
                    future_days=invalid_value
                )

    def test_get_tasks_future_days_with_completed_tasks(self, caldav_service):
        """Test future_days filtering with completed tasks."""
        from datetime import date, timedelta
        
        today = date.today()
        
        # Create a future task and complete it
        future_task_summary = "Test Integration Task - Future Completed"
        
        # Create the task
        result = caldav_service.add_task(
            summary=future_task_summary,
            calendar_name=TEST_CALENDAR_NAME,
            due_date=(today + timedelta(days=3)).isoformat(),
            description="Future task to be completed"
        )
        assert "Task created" in result
        
        # Complete the task
        complete_result = caldav_service.complete_task(
            summary=future_task_summary,
            calendar_name=TEST_CALENDAR_NAME
        )
        assert "completed" in complete_result.lower()

        # Test that future_days includes completed tasks when include_completed=True
        tasks_with_completed = caldav_service.get_tasks(
            query=TaskQuery(
                calendar_name=TEST_CALENDAR_NAME,
                future_days=7,
                include_completed=True
            )
        )
        
        completed_summaries = {task.summary for task in tasks_with_completed 
                             if task.summary == future_task_summary}
        assert future_task_summary in completed_summaries

        # Test that future_days excludes completed tasks when include_completed=False (default)
        tasks_without_completed = caldav_service.get_tasks(
            query=TaskQuery(
                calendar_name=TEST_CALENDAR_NAME,
                future_days=7,
                include_completed=False
            )
        )
        
        non_completed_summaries = {task.summary for task in tasks_without_completed}
        assert future_task_summary not in non_completed_summaries

    def test_get_tasks_future_days_edge_cases(self, caldav_service):
        """Test edge cases for future_days filtering."""
        from datetime import date, timedelta
        
        today = date.today()
        
        # Create task due today
        today_task_summary = "Test Integration Task - Due Today"
        result = caldav_service.add_task(
            summary=today_task_summary,
            calendar_name=TEST_CALENDAR_NAME,
            due_date=today.isoformat(),
            description="Task due today"
        )
        assert "Task created" in result

        # Test future_days=1 should include today's task
        tasks_future_1 = caldav_service.get_tasks(
            query=TaskQuery(calendar_name=TEST_CALENDAR_NAME, future_days=1)
        )
        
        future_1_summaries = {task.summary for task in tasks_future_1}
        assert today_task_summary in future_1_summaries

        # Create task due tomorrow
        tomorrow_task_summary = "Test Integration Task - Due Tomorrow"
        result = caldav_service.add_task(
            summary=tomorrow_task_summary,
            calendar_name=TEST_CALENDAR_NAME,
            due_date=(today + timedelta(days=1)).isoformat(),
            description="Task due tomorrow"
        )
        assert "Task created" in result

        # Test future_days=1 should NOT include tomorrow's task
        tasks_future_1_again = caldav_service.get_tasks(
            query=TaskQuery(calendar_name=TEST_CALENDAR_NAME, future_days=1)
        )
        
        future_1_summaries_again = {task.summary for task in tasks_future_1_again}
        assert today_task_summary in future_1_summaries_again
        assert tomorrow_task_summary not in future_1_summaries_again

        # Test future_days=2 should include both today and tomorrow
        tasks_future_2 = caldav_service.get_tasks(
            query=TaskQuery(calendar_name=TEST_CALENDAR_NAME, future_days=2)
        )
        
        future_2_summaries = {task.summary for task in tasks_future_2}
        assert today_task_summary in future_2_summaries
        assert tomorrow_task_summary in future_2_summaries

    def test_get_tasks_future_days_comparison_with_past_days(self, caldav_service):
        """Test that future_days and past_days work as expected opposites."""
        from datetime import date, timedelta
        
        today = date.today()
        
        # Create tasks in past, present, and future
        test_tasks = [
            {
                "summary": "Test Integration Task - Compare Past",
                "due_date": (today - timedelta(days=3)).isoformat(),
                "description": "Task for comparison"
            },
            {
                "summary": "Test Integration Task - Compare Present", 
                "due_date": today.isoformat(),
                "description": "Task for comparison"
            },
            {
                "summary": "Test Integration Task - Compare Future",
                "due_date": (today + timedelta(days=3)).isoformat(),
                "description": "Task for comparison"
            }
        ]
        
        # Create all test tasks
        for task_data in test_tasks:
            result = caldav_service.add_task(
                summary=task_data["summary"],
                calendar_name=TEST_CALENDAR_NAME,
                due_date=task_data["due_date"],
                description=task_data["description"]
            )
            assert "Task created" in result

        # Get past 7 days
        tasks_past = caldav_service.get_tasks(
            query=TaskQuery(calendar_name=TEST_CALENDAR_NAME, past_days=7)
        )
        past_summaries = {task.summary for task in tasks_past if "Compare" in task.summary}

        # Get future 7 days  
        tasks_future = caldav_service.get_tasks(
            query=TaskQuery(calendar_name=TEST_CALENDAR_NAME, future_days=7)
        )
        future_summaries = {task.summary for task in tasks_future if "Compare" in task.summary}

        # Past should include past and present
        expected_past = {
            "Test Integration Task - Compare Past",
            "Test Integration Task - Compare Present"
        }
        assert expected_past.issubset(past_summaries)
        assert "Test Integration Task - Compare Future" not in past_summaries

        # Future should include present and future
        expected_future = {
            "Test Integration Task - Compare Present", 
            "Test Integration Task - Compare Future"
        }
        assert expected_future.issubset(future_summaries)
        assert "Test Integration Task - Compare Past" not in future_summaries

        # Both should include present task (today)
        assert "Test Integration Task - Compare Present" in past_summaries
        assert "Test Integration Task - Compare Present" in future_summaries