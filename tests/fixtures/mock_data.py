"""
Mock data for testing.
"""

from datetime import datetime
from ticktick_mcp.models import Task, Project, Priority, TaskStatus, ViewMode


# Mock API response data
MOCK_PROJECT_RESPONSE = [
    {
        "id": "project_1",
        "name": "Work Project",
        "color": "#FF5722",
        "viewMode": "list",
        "closed": False
    },
    {
        "id": "project_2", 
        "name": "Personal Project",
        "color": "#2196F3",
        "viewMode": "kanban",
        "closed": False
    }
]

MOCK_TASK_RESPONSE = {
    "tasks": [
        {
            "id": "task_1",
            "title": "Complete report",
            "content": "Finish the quarterly report",
            "projectId": "project_1",
            "priority": 5,
            "status": 0,
            "startDate": "2024-01-01T10:00:00+0000",
            "dueDate": "2024-01-03T18:00:00+0000",
            "tags": ["work", "urgent"],
            "items": []
        },
        {
            "id": "task_2",
            "title": "Buy groceries",
            "content": "Get milk, bread, and eggs",
            "projectId": "project_2", 
            "priority": 1,
            "status": 0,
            "startDate": None,
            "dueDate": "2024-01-02T12:00:00+0000",
            "tags": ["personal"],
            "items": []
        }
    ],
    "columns": []
}

MOCK_TASK_DETAIL = {
    "id": "task_1",
    "title": "Complete report", 
    "content": "Finish the quarterly report",
    "projectId": "project_1",
    "priority": 5,
    "status": 0,
    "startDate": "2024-01-01T10:00:00+0000",
    "dueDate": "2024-01-03T18:00:00+0000",
    "tags": ["work", "urgent"],
    "items": []
}

# Test object instances
def create_sample_project():
    """Create a sample project for testing."""
    return Project(
        id="test_project_123",
        name="Test Project",
        color="#FF5722",
        view_mode=ViewMode.LIST,
        closed=False
    )

def create_sample_task():
    """Create a sample task for testing."""
    return Task(
        id="test_task_456",
        title="Test Task",
        content="This is a test task",
        project_id="test_project_123",
        priority=Priority.MEDIUM,
        status=TaskStatus.ACTIVE,
        start_date=datetime.fromisoformat("2024-01-01T10:00:00+00:00"),
        due_date=datetime.fromisoformat("2024-01-03T18:00:00+00:00"),
        tags=["test", "sample"]
    )

def create_sample_projects():
    """Create a list of sample projects for testing."""
    return [
        Project(
            id="work_proj",
            name="Work Project",
            color="#FF5722",
            view_mode=ViewMode.LIST
        ),
        Project(
            id="personal_proj", 
            name="Personal Project",
            color="#2196F3",
            view_mode=ViewMode.KANBAN
        )
    ]

def create_sample_tasks():
    """Create a list of sample tasks for testing."""
    return [
        Task(
            id="task_1",
            title="Complete report",
            content="Finish the quarterly report",
            project_id="project_1",
            priority=Priority.HIGH,
            status=TaskStatus.ACTIVE,
            tags=["work", "urgent"]
        ),
        Task(
            id="task_2", 
            title="Buy groceries",
            content="Get milk, bread, and eggs",
            project_id="project_2",
            priority=Priority.LOW,
            status=TaskStatus.ACTIVE,
            tags=["personal"]
        )
    ]