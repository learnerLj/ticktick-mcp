"""
Simplified unit tests for data models.
"""

from ticktick_mcp.models import (
    Priority,
    Project,
    SubTask,
    Task,
    TaskFilter,
    TaskStatus,
    ViewMode,
)


class TestPriority:
    """Test Priority enum."""

    def test_priority_values(self):
        """Test priority enum values."""
        assert Priority.NONE.value == 0
        assert Priority.LOW.value == 1
        assert Priority.MEDIUM.value == 3
        assert Priority.HIGH.value == 5


class TestTaskStatus:
    """Test TaskStatus enum."""

    def test_status_values(self):
        """Test status enum values."""
        assert TaskStatus.ACTIVE.value == 0
        assert TaskStatus.COMPLETED.value == 2


class TestViewMode:
    """Test ViewMode enum."""

    def test_view_mode_values(self):
        """Test view mode enum values."""
        assert ViewMode.LIST.value == "list"
        assert ViewMode.KANBAN.value == "kanban"
        assert ViewMode.TIMELINE.value == "timeline"


class TestSubTask:
    """Test SubTask model."""

    def test_subtask_creation(self):
        """Test creating a subtask."""
        subtask = SubTask(id="subtask_1", title="Test Subtask", status=0)
        assert subtask.id == "subtask_1"
        assert subtask.title == "Test Subtask"
        assert not subtask.is_completed

    def test_subtask_completion_status(self):
        """Test subtask completion status."""
        completed_subtask = SubTask(id="sub_1", title="Test", status=1)
        active_subtask = SubTask(id="sub_2", title="Test", status=0)

        assert completed_subtask.is_completed is True
        assert active_subtask.is_completed is False


class TestTask:
    """Test Task model."""

    def test_task_creation(self):
        """Test creating a task."""
        task = Task(
            id="task_1",
            title="Test Task",
            project_id="project_1",
            priority=Priority.HIGH,
            status=TaskStatus.ACTIVE,
        )
        assert task.id == "task_1"
        assert task.title == "Test Task"
        assert task.project_id == "project_1"
        assert task.priority == Priority.HIGH
        assert task.status == TaskStatus.ACTIVE

    def test_task_properties(self):
        """Test task computed properties."""
        # Test active task
        active_task = Task(id="1", title="Active", status=TaskStatus.ACTIVE)
        assert not active_task.is_completed

        # Test completed task
        completed_task = Task(id="2", title="Done", status=TaskStatus.COMPLETED)
        assert completed_task.is_completed


class TestProject:
    """Test Project model."""

    def test_project_creation(self):
        """Test creating a project."""
        project = Project(
            id="project_1",
            name="Test Project",
            color="#FF5722",
            view_mode=ViewMode.KANBAN,
            closed=False,
        )
        assert project.id == "project_1"
        assert project.name == "Test Project"
        assert project.color == "#FF5722"
        assert project.view_mode == ViewMode.KANBAN
        assert not project.closed


class TestTaskFilter:
    """Test TaskFilter model."""

    def test_filter_creation(self):
        """Test creating a task filter."""
        filter_obj = TaskFilter(
            status=TaskStatus.ACTIVE,
            priority=Priority.HIGH,
            project_id="project_1",
            query="important",
        )
        assert filter_obj.status == TaskStatus.ACTIVE
        assert filter_obj.priority == Priority.HIGH
        assert filter_obj.project_id == "project_1"
        assert filter_obj.query == "important"
