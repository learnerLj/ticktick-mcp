"""
Simplified pytest configuration and shared fixtures.
"""

from unittest.mock import Mock

import pytest

from ticktick_mcp.models import Priority, Project, Task, TaskStatus, ViewMode


@pytest.fixture
def sample_task():
    """Create a sample task for testing."""
    return Task(
        id="test_task_456",
        title="Test Task",
        content="This is a test task",
        project_id="test_project_123",
        priority=Priority.MEDIUM,
        status=TaskStatus.ACTIVE,
        tags=["test", "sample"],
    )


@pytest.fixture
def sample_project():
    """Create a sample project for testing."""
    return Project(
        id="test_project_123",
        name="Test Project",
        color="#FF5722",
        view_mode=ViewMode.LIST,
        closed=False,
    )


@pytest.fixture
def sample_tasks():
    """Create a list of sample tasks for testing."""
    return [
        Task(
            id="task_1",
            title="Complete report",
            content="Finish the quarterly report",
            project_id="project_1",
            priority=Priority.HIGH,
            status=TaskStatus.ACTIVE,
            tags=["work", "urgent"],
        ),
        Task(
            id="task_2",
            title="Buy groceries",
            content="Get milk, bread, and eggs",
            project_id="project_2",
            priority=Priority.LOW,
            status=TaskStatus.ACTIVE,
            tags=["personal"],
        ),
    ]


@pytest.fixture
def sample_projects():
    """Create a list of sample projects for testing."""
    return [
        Project(
            id="work_proj",
            name="Work Project",
            color="#FF5722",
            view_mode=ViewMode.LIST,
        ),
        Project(
            id="personal_proj",
            name="Personal Project",
            color="#2196F3",
            view_mode=ViewMode.KANBAN,
        ),
    ]


@pytest.fixture
def mock_config():
    """Create a mock configuration."""
    config = Mock()
    config.client_id = "test_client_id"
    config.client_secret = "test_client_secret"
    config.access_token = "test_access_token"
    config.refresh_token = "test_refresh_token"
    config.base_url = "https://api.ticktick.com/open/v1"
    config.use_dida365 = False
    return config


@pytest.fixture
def mock_api_client():
    """Create a mock API client."""
    client = Mock()
    client.make_request = Mock()
    return client


@pytest.fixture
def task_service(mock_api_client):
    """Create a TaskService with mock API client."""
    from ticktick_mcp.client import TaskService

    return TaskService(mock_api_client)


@pytest.fixture
def project_service(mock_api_client):
    """Create a ProjectService with mock API client."""
    from ticktick_mcp.client import ProjectService

    return ProjectService(mock_api_client)


@pytest.fixture
def mock_config_manager(mock_config):
    """Create a mock config manager."""
    manager = Mock()
    manager.load_config.return_value = mock_config
    manager.is_authenticated.return_value = True
    return manager


@pytest.fixture
def mock_server(mock_config_manager):
    """Create a mock server for testing."""
    from ticktick_mcp.server_oop import TickTickMCPServer

    return TickTickMCPServer(mock_config_manager)
