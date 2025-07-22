"""
Unit tests for src.providers.caldav_services.task_service module.
Tests the get_tasks method with future_days parameter using mocks.
"""

import pytest
from unittest.mock import Mock, patch
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo
from pydantic import ValidationError

from src.providers.caldav_services.task_service import CalDavTaskService
from src.core.models import Task, TaskQuery


@pytest.fixture
def mock_caldav_base():
    """Create a mock CalDAV base instance."""
    mock_base = Mock()
    mock_base.calendars = []
    return mock_base


@pytest.fixture
def task_service(mock_caldav_base):
    """Create a CalDavTaskService instance with mocked base."""
    return CalDavTaskService(mock_caldav_base)


@pytest.fixture
def mock_calendar():
    """Create a mock calendar with test todos."""
    mock_cal = Mock()
    mock_cal.name = "Test Calendar"
    return mock_cal


@pytest.fixture
def sample_tasks():
    """Create sample tasks with different due dates."""
    today = datetime.now(ZoneInfo("UTC")).date()
    
    return [
        # Past tasks
        Task(
            summary="Past Task 1",
            description="Task from 3 days ago",
            due_on=today - timedelta(days=3),
            completed=False,
            status="NEEDS-ACTION",
            calendar_name="Test Calendar"
        ),
        Task(
            summary="Past Task 2", 
            description="Task from 1 day ago",
            due_on=today - timedelta(days=1),
            completed=False,
            status="NEEDS-ACTION",
            calendar_name="Test Calendar"
        ),
        
        # Today's tasks
        Task(
            summary="Today Task",
            description="Task due today",
            due_on=today,
            completed=False,
            status="NEEDS-ACTION",
            calendar_name="Test Calendar"
        ),
        
        # Future tasks
        Task(
            summary="Future Task 1",
            description="Task due in 2 days",
            due_on=today + timedelta(days=2),
            completed=False,
            status="NEEDS-ACTION",
            calendar_name="Test Calendar"
        ),
        Task(
            summary="Future Task 2",
            description="Task due in 5 days",
            due_on=today + timedelta(days=5),
            completed=False,
            status="NEEDS-ACTION",
            calendar_name="Test Calendar"
        ),
        Task(
            summary="Future Task 3",
            description="Task due in 10 days",
            due_on=today + timedelta(days=10),
            completed=False,
            status="NEEDS-ACTION",
            calendar_name="Test Calendar"
        ),
        
        # Task without due date
        Task(
            summary="No Due Date Task",
            description="Task without due date",
            due_on=None,
            completed=False,
            status="NEEDS-ACTION",
            calendar_name="Test Calendar"
        ),
    ]


class TestGetTasksWithFutureDays:
    """Tests for get_tasks method with future_days parameter."""

    def test_get_tasks_future_days_1(self, task_service, mock_calendar, sample_tasks):
        """Test getting tasks for future 1 day (today only)."""
        # Setup mock
        task_service.caldav_base.calendars = [mock_calendar]
        
        # Create mock todos that return our sample tasks
        mock_todos = []
        for task in sample_tasks:
            mock_todo = Mock()
            with patch('src.core.models.Task.from_todo', return_value=task):
                mock_todos.append(mock_todo)
        
        mock_calendar.todos.return_value = mock_todos
        
        # Mock Task.from_todo to return our sample tasks
        with patch('src.core.models.Task.from_todo', side_effect=sample_tasks):
            # Call method
            query = TaskQuery(future_days=1)
            result = task_service.get_tasks(query)
            
            # Should include today's task and task without due date
            expected_summaries = {"Today Task", "No Due Date Task"}
            actual_summaries = {task.summary for task in result}
            assert actual_summaries == expected_summaries

    def test_get_tasks_future_days_7(self, task_service, mock_calendar, sample_tasks):
        """Test getting tasks for future 7 days."""
        # Setup mock
        task_service.caldav_base.calendars = [mock_calendar]
        
        mock_todos = []
        for task in sample_tasks:
            mock_todo = Mock()
            mock_todos.append(mock_todo)
        
        mock_calendar.todos.return_value = mock_todos
        
        # Mock Task.from_todo to return our sample tasks
        with patch('src.core.models.Task.from_todo', side_effect=sample_tasks):
            # Call method
            query = TaskQuery(future_days=7)
            result = task_service.get_tasks(query)
            
            # Should include today's task, tasks due in 2 and 5 days, and task without due date
            expected_summaries = {"Today Task", "Future Task 1", "Future Task 2", "No Due Date Task"}
            actual_summaries = {task.summary for task in result}
            assert actual_summaries == expected_summaries

    def test_get_tasks_future_days_15(self, task_service, mock_calendar, sample_tasks):
        """Test getting tasks for future 15 days."""
        # Setup mock
        task_service.caldav_base.calendars = [mock_calendar]
        
        mock_todos = []
        for task in sample_tasks:
            mock_todo = Mock()
            mock_todos.append(mock_todo)
        
        mock_calendar.todos.return_value = mock_todos
        
        # Mock Task.from_todo to return our sample tasks
        with patch('src.core.models.Task.from_todo', side_effect=sample_tasks):
            # Call method
            query = TaskQuery(future_days=15)
            result = task_service.get_tasks(query)
            
            # Should include all future tasks (including today and 10 days out) and task without due date
            expected_summaries = {"Today Task", "Future Task 1", "Future Task 2", "Future Task 3", "No Due Date Task"}
            actual_summaries = {task.summary for task in result}
            assert actual_summaries == expected_summaries

    def test_get_tasks_future_days_excludes_past_tasks(self, task_service, mock_calendar, sample_tasks):
        """Test that future_days filter excludes past tasks."""
        # Setup mock
        task_service.caldav_base.calendars = [mock_calendar]
        
        mock_todos = []
        for task in sample_tasks:
            mock_todo = Mock()
            mock_todos.append(mock_todo)
        
        mock_calendar.todos.return_value = mock_todos
        
        # Mock Task.from_todo to return our sample tasks
        with patch('src.core.models.Task.from_todo', side_effect=sample_tasks):
            # Call method
            query = TaskQuery(future_days=7)
            result = task_service.get_tasks(query)
            
            # Should NOT include past tasks
            excluded_summaries = {"Past Task 1", "Past Task 2"}
            actual_summaries = {task.summary for task in result}
            assert excluded_summaries.isdisjoint(actual_summaries)

    def test_get_tasks_both_past_and_future_days_raises_error(self, task_service):
        """Test that specifying both past_days and future_days raises ValueError."""
        with pytest.raises(ValueError, match="Cannot specify both past_days and future_days filters"):
            query = TaskQuery(past_days=7, future_days=7)

    def test_get_tasks_future_days_invalid_integer_input(self, task_service):
        """Test that invalid integer future_days input raises ValueError."""
        invalid_integer_inputs = [0, -1, -10]
        
        for invalid_input in invalid_integer_inputs:
            with pytest.raises(ValueError, match="Days must be a positive integer"):
                query = TaskQuery(future_days=invalid_input)
    
    def test_get_tasks_future_days_invalid_type_input(self, task_service):
        """Test that non-integer future_days input raises ValueError."""
        invalid_type_inputs = ["invalid", 1.5]
        
        for invalid_input in invalid_type_inputs:
            with pytest.raises(ValueError):  # Pydantic type validation error
                query = TaskQuery(future_days=invalid_input)

    def test_get_tasks_future_days_with_calendar_filter(self, task_service, sample_tasks):
        """Test getting future tasks filtered by calendar name."""
        # Create two mock calendars
        mock_cal1 = Mock()
        mock_cal1.name = "Work Calendar"
        mock_cal2 = Mock()
        mock_cal2.name = "Personal Calendar"
        
        # Setup task service with both calendars
        task_service.caldav_base.calendars = [mock_cal1, mock_cal2]
        
        # Create tasks for work calendar only
        work_tasks = [task for task in sample_tasks if "Future" in task.summary]
        for task in work_tasks:
            task.calendar_name = "Work Calendar"
        
        mock_todos = []
        for task in work_tasks:
            mock_todo = Mock()
            mock_todos.append(mock_todo)
        
        mock_cal1.todos.return_value = mock_todos
        mock_cal2.todos.return_value = []  # No tasks in personal calendar
        
        # Mock find_calendar_by_name to return work calendar
        with patch('src.utils.entity_finder_utils.find_calendar_by_name', return_value=mock_cal1):
            with patch('src.core.models.Task.from_todo', side_effect=work_tasks):
                # Call method with calendar filter
                query = TaskQuery(future_days=7, calendar_name="Work Calendar")
                result = task_service.get_tasks(query)
                
                # Should only include work calendar tasks
                assert all(task.calendar_name == "Work Calendar" for task in result)
                expected_summaries = {"Future Task 1", "Future Task 2"}
                actual_summaries = {task.summary for task in result}
                assert actual_summaries == expected_summaries

    def test_get_tasks_future_days_includes_tasks_without_due_date(self, task_service, mock_calendar):
        """Test that future_days filter includes tasks without due dates."""
        # Create tasks without due dates
        tasks_without_due_date = [
            Task(
                summary="No Due Date Task 1",
                description="Task without due date",
                due_on=None,
                completed=False,
                status="NEEDS-ACTION",
                calendar_name="Test Calendar"
            ),
            Task(
                summary="No Due Date Task 2",
                description="Another task without due date",
                due_on=None,
                completed=False,
                status="NEEDS-ACTION",
                calendar_name="Test Calendar"
            ),
        ]
        
        # Setup mock
        task_service.caldav_base.calendars = [mock_calendar]
        
        mock_todos = []
        for task in tasks_without_due_date:
            mock_todo = Mock()
            mock_todos.append(mock_todo)
        
        mock_calendar.todos.return_value = mock_todos
        
        # Mock Task.from_todo to return our tasks
        with patch('src.core.models.Task.from_todo', side_effect=tasks_without_due_date):
            # Call method
            query = TaskQuery(future_days=7)
            result = task_service.get_tasks(query)
            
            # Should include all tasks without due dates
            expected_summaries = {"No Due Date Task 1", "No Due Date Task 2"}
            actual_summaries = {task.summary for task in result}
            assert actual_summaries == expected_summaries

    def test_get_tasks_future_days_with_completed_tasks(self, task_service, mock_calendar):
        """Test getting future tasks including completed ones."""
        today = datetime.now(ZoneInfo("UTC")).date()
        
        # Create a mix of completed and non-completed future tasks
        future_tasks = [
            Task(
                summary="Future Completed Task",
                description="Completed task due in future",
                due_on=today + timedelta(days=3),
                completed=True,
                status="COMPLETED",
                calendar_name="Test Calendar"
            ),
            Task(
                summary="Future Active Task",
                description="Active task due in future",
                due_on=today + timedelta(days=3),
                completed=False,
                status="NEEDS-ACTION",
                calendar_name="Test Calendar"
            ),
        ]
        
        # Setup mock
        task_service.caldav_base.calendars = [mock_calendar]
        
        mock_todos = []
        for task in future_tasks:
            mock_todo = Mock()
            mock_todos.append(mock_todo)
        
        mock_calendar.todos.return_value = mock_todos
        
        # Mock Task.from_todo to return our tasks
        with patch('src.core.models.Task.from_todo', side_effect=future_tasks):
            # Test with include_completed=True
            query = TaskQuery(future_days=7, include_completed=True)
            result = task_service.get_tasks(query)
            
            # Should include both completed and active tasks
            expected_summaries = {"Future Completed Task", "Future Active Task"}
            actual_summaries = {task.summary for task in result}
            assert actual_summaries == expected_summaries

    @patch('src.providers.caldav_services.task_service.calculate_future_days_range')
    def test_get_tasks_future_days_calls_calculate_function(self, mock_calculate, task_service, mock_calendar):
        """Test that get_tasks calls calculate_future_days_range with correct parameter."""
        # Setup mock
        today = datetime.now(ZoneInfo("UTC")).date()
        mock_calculate.return_value = (today, today + timedelta(days=6))
        task_service.caldav_base.calendars = [mock_calendar]
        mock_calendar.todos.return_value = []
        
        # Call method
        query = TaskQuery(future_days=7)
        task_service.get_tasks(query)
        
        # Verify calculate_future_days_range was called with correct parameter
        mock_calculate.assert_called_once_with(7)

    def test_get_tasks_no_date_filter_includes_all_tasks(self, task_service, mock_calendar, sample_tasks):
        """Test that when no date filter is specified, all tasks are returned."""
        # Setup mock
        task_service.caldav_base.calendars = [mock_calendar]
        
        mock_todos = []
        for task in sample_tasks:
            mock_todo = Mock()
            mock_todos.append(mock_todo)
        
        mock_calendar.todos.return_value = mock_todos
        
        # Mock Task.from_todo to return our sample tasks
        with patch('src.core.models.Task.from_todo', side_effect=sample_tasks):
            # Call method without any date filter
            query = TaskQuery()
            result = task_service.get_tasks(query)
            
            # Should include all tasks (past, present, future, and no due date)
            expected_count = len(sample_tasks)
            assert len(result) == expected_count
            
            all_summaries = {task.summary for task in sample_tasks}
            actual_summaries = {task.summary for task in result}
            assert actual_summaries == all_summaries


class TestGetTasksDateFilterValidation:
    """Tests for date filter validation in get_tasks method."""

    def test_mutual_exclusion_past_and_future_days(self, task_service):
        """Test that past_days and future_days cannot be used together."""
        with pytest.raises(ValueError, match="Cannot specify both past_days and future_days filters"):
            query = TaskQuery(past_days=5, future_days=5)

    def test_allows_past_days_only(self, task_service, mock_calendar):
        """Test that past_days can be used alone."""
        task_service.caldav_base.calendars = [mock_calendar]
        mock_calendar.todos.return_value = []
        
        # Should not raise an error
        query = TaskQuery(past_days=7)
        result = task_service.get_tasks(query)
        assert isinstance(result, list)

    def test_allows_future_days_only(self, task_service, mock_calendar):
        """Test that future_days can be used alone."""
        task_service.caldav_base.calendars = [mock_calendar]
        mock_calendar.todos.return_value = []
        
        # Should not raise an error
        query = TaskQuery(future_days=7)
        result = task_service.get_tasks(query)
        assert isinstance(result, list)

    def test_allows_no_date_filter(self, task_service, mock_calendar):
        """Test that no date filter is allowed."""
        task_service.caldav_base.calendars = [mock_calendar]
        mock_calendar.todos.return_value = []
        
        # Should not raise an error
        query = TaskQuery()
        result = task_service.get_tasks(query)
        assert isinstance(result, list)

    def test_future_days_zero_raises_error(self, task_service):
        """Test that future_days=0 raises ValueError."""
        with pytest.raises(ValueError, match="Days must be a positive integer"):
            query = TaskQuery(future_days=0)

    def test_future_days_negative_raises_error(self, task_service):
        """Test that negative future_days raises ValueError."""
        with pytest.raises(ValueError, match="Days must be a positive integer"):
            query = TaskQuery(future_days=-5)

    def test_future_days_non_integer_raises_error(self, task_service):
        """Test that non-integer future_days raises ValidationError."""
        with pytest.raises(ValidationError):  # Pydantic type validation error
            query = TaskQuery(future_days="invalid")