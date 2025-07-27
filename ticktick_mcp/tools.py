"""MCP tools for TickTick integration using object-oriented design."""

from abc import ABC, abstractmethod
from datetime import datetime

from .client import ProjectService, TaskService
from .exceptions import TickTickMCPError, ValidationError
from .logging_config import LoggerManager
from .models import Priority, Project, Task, TaskFilter, TaskStatus, ViewMode


class BaseMCPTool(ABC):
    """Abstract base class for MCP tools."""

    def __init__(self, name: str, description: str):
        """Initialize base MCP tool.

        Args:
            name: Tool name
            description: Tool description
        """
        self.name = name
        self.description = description
        self.logger = LoggerManager().get_logger(f"tool.{name}")

    @abstractmethod
    async def execute(self, **kwargs) -> str:
        """Execute the tool with given parameters.

        Returns:
            Formatted result string
        """
        pass

    def _validate_priority(self, priority: int) -> Priority:
        """Validate and convert priority value.

        Args:
            priority: Priority value

        Returns:
            Priority enum

        Raises:
            ValidationError: If priority is invalid
        """
        if priority not in [0, 1, 3, 5]:
            raise ValidationError(
                "Priority must be 0 (None), 1 (Low), 3 (Medium), or 5 (High)"
            )
        return Priority(priority)

    def _validate_view_mode(self, view_mode: str) -> ViewMode:
        """Validate view mode.

        Args:
            view_mode: View mode string

        Returns:
            ViewMode enum

        Raises:
            ValidationError: If view mode is invalid
        """
        try:
            return ViewMode(view_mode)
        except ValueError as e:
            raise ValidationError(
                "View mode must be one of: list, kanban, timeline"
            ) from e

    def _validate_date_format(self, date_str: str, field_name: str) -> None:
        """Validate ISO date format.

        Args:
            date_str: Date string to validate
            field_name: Field name for error messages

        Raises:
            ValidationError: If date format is invalid
        """
        try:
            datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except ValueError as e:
            raise ValidationError(
                f"Invalid {field_name} format. Use ISO format: YYYY-MM-DDThh:mm:ss+0000"
            ) from e

    def _format_error(self, error: Exception) -> str:
        """Format error message for user display.

        Args:
            error: Exception to format

        Returns:
            Formatted error message
        """
        if isinstance(error, TickTickMCPError):
            return f"Error: {error.message}"
        return f"Unexpected error: {str(error)}"


class TaskFormatter:
    """Utility class for formatting task display."""

    @staticmethod
    def format_task(task: Task) -> str:
        """Format a task for display.

        Args:
            task: Task to format

        Returns:
            Formatted task string
        """
        formatted = f"ID: {task.id}\n"
        formatted += f"Title: {task.title}\n"
        formatted += f"Project ID: {task.project_id or 'None'}\n"

        # Add dates
        if task.start_date:
            formatted += f"Start Date: {task.start_date}\n"
        if task.due_date:
            formatted += f"Due Date: {task.due_date}\n"

        # Add priority and status
        formatted += f"Priority: {task.priority_name}\n"
        status_name = "Completed" if task.is_completed else "Active"
        formatted += f"Status: {status_name}\n"

        # Add content
        if task.content:
            formatted += f"\nContent:\n{task.content}\n"

        # Add subtasks
        if task.subtasks:
            formatted += f"\nSubtasks ({len(task.subtasks)}):\n"
            for i, subtask in enumerate(task.subtasks, 1):
                status = "✓" if subtask.is_completed else "□"
                formatted += f"{i}. [{status}] {subtask.title}\n"

        return formatted

    @staticmethod
    def format_project(project: Project) -> str:
        """Format a project for display.

        Args:
            project: Project to format

        Returns:
            Formatted project string
        """
        formatted = f"Name: {project.name}\n"
        formatted += f"ID: {project.id}\n"
        formatted += f"Color: {project.color}\n"
        formatted += f"View Mode: {project.view_mode.value}\n"
        formatted += f"Closed: {'Yes' if project.closed else 'No'}\n"
        formatted += f"Kind: {project.kind}\n"
        return formatted


# Project Tools


class GetProjectsTool(BaseMCPTool):
    """Tool to get all projects."""

    def __init__(self, project_service: ProjectService):
        super().__init__("get_projects", "Get all projects from TickTick")
        self.project_service = project_service

    async def execute(self) -> str:
        """Get all projects."""
        try:
            projects = self.project_service.get_all_projects()

            if not projects:
                return "No projects found."

            result = f"Found {len(projects)} projects:\n\n"
            for i, project in enumerate(projects, 1):
                result += f"Project {i}:\n{TaskFormatter.format_project(project)}\n"

            return result
        except Exception as e:
            self.logger.error(f"Error getting projects: {e}")
            return self._format_error(e)


class GetProjectTool(BaseMCPTool):
    """Tool to get a specific project."""

    def __init__(self, project_service: ProjectService):
        super().__init__("get_project", "Get details about a specific project")
        self.project_service = project_service

    async def execute(self, project_id: str) -> str:
        """Get project details.

        Args:
            project_id: ID of the project
        """
        try:
            project = self.project_service.get_project_by_id(project_id)
            return TaskFormatter.format_project(project)
        except Exception as e:
            self.logger.error(f"Error getting project {project_id}: {e}")
            return self._format_error(e)


class CreateProjectTool(BaseMCPTool):
    """Tool to create a new project."""

    def __init__(self, project_service: ProjectService):
        super().__init__("create_project", "Create a new project in TickTick")
        self.project_service = project_service

    async def execute(
        self, name: str, color: str = "#F18181", view_mode: str = "list"
    ) -> str:
        """Create a new project.

        Args:
            name: Project name
            color: Color code (hex format)
            view_mode: View mode (list, kanban, timeline)
        """
        try:
            # Validate inputs
            view_mode_enum = self._validate_view_mode(view_mode)

            # Create project
            project = Project(
                id="",  # Will be set by API
                name=name,
                color=color,
                view_mode=view_mode_enum,
            )

            created_project = self.project_service.create_project(project)
            return f"Project created successfully:\n\n{TaskFormatter.format_project(created_project)}"
        except Exception as e:
            self.logger.error(f"Error creating project: {e}")
            return self._format_error(e)


class DeleteProjectTool(BaseMCPTool):
    """Tool to delete a project."""

    def __init__(self, project_service: ProjectService):
        super().__init__("delete_project", "Delete a project")
        self.project_service = project_service

    async def execute(self, project_id: str) -> str:
        """Delete a project.

        Args:
            project_id: ID of the project
        """
        try:
            self.project_service.delete_project(project_id)
            return f"Project {project_id} deleted successfully."
        except Exception as e:
            self.logger.error(f"Error deleting project {project_id}: {e}")
            return self._format_error(e)


# Task Tools


class GetAllTasksTool(BaseMCPTool):
    """Tool to get all tasks with filtering."""

    def __init__(self, task_service: TaskService):
        super().__init__(
            "get_all_tasks",
            "Get all tasks from TickTick across all projects with optional filters. "
            "Supports filtering by status, priority, project, and search query. "
            "Can also get special collections like inbox tasks using project_id='inbox'.",
        )
        self.task_service = task_service

    async def execute(
        self,
        status: str | None = None,
        limit: int | None = None,
        query: str | None = None,
        priority: int | None = None,
        project_id: str | None = None,
    ) -> str:
        """Get all tasks with optional filtering.

        Args:
            status: Filter by task status ('active', 'completed', or None for all)
            limit: Maximum number of tasks to return (optional, no limit by default)
            query: Search query string to match in task title/content
            priority: Filter by priority level (0: None, 1: Low, 3: Medium, 5: High)
            project_id: Filter by specific project ID. Special values:
                       - 'inbox': Get tasks not assigned to any project
                       - Regular project ID: Get tasks from specific project

        Note: For date-based filtering (today, overdue, next 7 days), the AI should:
        1. Get all active tasks with this tool
        2. Use client-side date filtering on the results based on due_date field
        """
        try:
            # Validate priority if provided
            priority_enum = None
            if priority is not None:
                priority_enum = self._validate_priority(priority)

            # Convert status to enum
            status_enum = None
            if status == "active":
                status_enum = TaskStatus.ACTIVE
            elif status == "completed":
                status_enum = TaskStatus.COMPLETED

            # Create filter
            task_filter = TaskFilter(
                status=status_enum,
                priority=priority_enum,
                project_id=project_id,
                query=query,
                limit=limit,
            )

            tasks = self.task_service.get_all_tasks(task_filter)

            if not tasks:
                return "No tasks found matching the criteria."

            # Build description
            filters = []
            if status:
                filters.append(f"status: {status}")
            if query:
                filters.append(f"query: '{query}'")
            if priority is not None:
                priority_names = {0: "None", 1: "Low", 3: "Medium", 5: "High"}
                filters.append(f"priority: {priority_names[priority]}")
            if project_id:
                filters.append(f"project: {project_id}")

            filter_text = " with filters: " + ", ".join(filters) if filters else ""
            result = f"Found {len(tasks)} tasks{filter_text}:\n\n"

            for i, task in enumerate(tasks, 1):
                result += f"Task {i}:\n{TaskFormatter.format_task(task)}\n"

            return result
        except Exception as e:
            self.logger.error(f"Error getting tasks: {e}")
            return self._format_error(e)


class GetTaskByIdTool(BaseMCPTool):
    """Tool to get a task by ID."""

    def __init__(self, task_service: TaskService):
        super().__init__(
            "get_task_by_id", "Get a task by its ID without requiring project ID"
        )
        self.task_service = task_service

    async def execute(self, task_id: str) -> str:
        """Get task by ID.

        Args:
            task_id: ID of the task to retrieve
        """
        try:
            task = self.task_service.get_task_by_id(task_id)
            return TaskFormatter.format_task(task)
        except Exception as e:
            self.logger.error(f"Error getting task {task_id}: {e}")
            return self._format_error(e)


class CreateTaskTool(BaseMCPTool):
    """Tool to create a new task."""

    def __init__(self, task_service: TaskService):
        super().__init__("create_task", "Create a new task in TickTick")
        self.task_service = task_service

    async def execute(
        self,
        title: str,
        project_id: str,
        content: str | None = None,
        start_date: str | None = None,
        due_date: str | None = None,
        priority: int = 0,
    ) -> str:
        """Create a new task.

        Args:
            title: Task title
            project_id: ID of the project to add the task to
            content: Task description/content
            start_date: Start date in ISO format YYYY-MM-DDThh:mm:ss+0000
            due_date: Due date in ISO format YYYY-MM-DDThh:mm:ss+0000
            priority: Priority level (0: None, 1: Low, 3: Medium, 5: High)
        """
        try:
            # Validate inputs
            priority_enum = self._validate_priority(priority)

            if start_date:
                self._validate_date_format(start_date, "start_date")
            if due_date:
                self._validate_date_format(due_date, "due_date")

            # Create task
            task = Task(
                id="",  # Will be set by API
                title=title,
                project_id=project_id,
                content=content,
                priority=priority_enum,
                start_date=start_date,
                due_date=due_date,
            )

            created_task = self.task_service.create_task(task)
            return f"Task created successfully:\n\n{TaskFormatter.format_task(created_task)}"
        except Exception as e:
            self.logger.error(f"Error creating task: {e}")
            return self._format_error(e)


class UpdateTaskTool(BaseMCPTool):
    """Tool to update an existing task."""

    def __init__(self, task_service: TaskService):
        super().__init__("update_task", "Update an existing task's properties")
        self.task_service = task_service

    async def execute(
        self,
        task_id: str,
        title: str | None = None,
        content: str | None = None,
        start_date: str | None = None,
        due_date: str | None = None,
        priority: int | None = None,
        project_id: str | None = None,
    ) -> str:
        """Update an existing task.

        Args:
            task_id: ID of the task to update
            title: New task title (optional)
            content: New task description/content (optional)
            start_date: New start date in ISO format YYYY-MM-DDThh:mm:ss+0000 (optional)
            due_date: New due date in ISO format YYYY-MM-DDThh:mm:ss+0000 (optional)
            priority: New priority level (0: None, 1: Low, 3: Medium, 5: High) (optional)
            project_id: New project ID to move task to (optional)
        """
        try:
            # First get the existing task
            existing_task = self.task_service.get_task_by_id(task_id)

            # Validate inputs if provided
            priority_enum = existing_task.priority
            if priority is not None:
                priority_enum = self._validate_priority(priority)

            if start_date:
                self._validate_date_format(start_date, "start_date")
            if due_date:
                self._validate_date_format(due_date, "due_date")

            # Create updated task with new values (keep existing if not provided)
            updated_task = Task(
                id=task_id,
                title=title if title is not None else existing_task.title,
                project_id=(
                    project_id if project_id is not None else existing_task.project_id
                ),
                content=content if content is not None else existing_task.content,
                priority=priority_enum,
                start_date=(
                    start_date if start_date is not None else existing_task.start_date
                ),
                due_date=due_date if due_date is not None else existing_task.due_date,
                status=existing_task.status,  # Keep existing status
                tags=existing_task.tags,  # Keep existing tags
                subtasks=existing_task.subtasks,  # Keep existing subtasks
            )

            result_task = self.task_service.update_task(updated_task)
            return f"Task updated successfully:\n\n{TaskFormatter.format_task(result_task)}"
        except Exception as e:
            self.logger.error(f"Error updating task {task_id}: {e}")
            return self._format_error(e)


class BatchCompleteTasksTool(BaseMCPTool):
    """Tool to complete one or multiple tasks."""

    def __init__(self, task_service: TaskService):
        super().__init__(
            "batch_complete_tasks",
            "Complete one or multiple tasks by providing comma-separated task IDs. "
            "Can be used for single task (just provide one ID) or multiple tasks.",
        )
        self.task_service = task_service

    async def execute(self, task_ids: str) -> str:
        """Complete one or multiple tasks.

        Args:
            task_ids: Single task ID or comma-separated list of task IDs to complete
                     Examples: "task123" or "task123,task456,task789"
        """
        try:
            # Parse task IDs
            ids = [tid.strip() for tid in task_ids.split(",") if tid.strip()]
            if not ids:
                return "No valid task IDs provided."

            self.task_service.batch_complete_tasks(ids)

            if len(ids) == 1:
                return f"Task {ids[0]} marked as complete."
            else:
                return f"Successfully completed {len(ids)} tasks: {', '.join(ids)}"
        except Exception as e:
            self.logger.error(f"Error completing tasks: {e}")
            return self._format_error(e)


class BatchDeleteTasksTool(BaseMCPTool):
    """Tool to delete one or multiple tasks."""

    def __init__(self, task_service: TaskService):
        super().__init__(
            "batch_delete_tasks",
            "Delete one or multiple tasks by providing comma-separated task IDs. "
            "Can be used for single task (just provide one ID) or multiple tasks. "
            "Note: Only active (incomplete) tasks can be deleted. Completed tasks cannot be deleted.",
        )
        self.task_service = task_service

    async def execute(self, task_ids: str) -> str:
        """Delete one or multiple tasks.

        Args:
            task_ids: Single task ID or comma-separated list of task IDs to delete
                     Examples: "task123" or "task123,task456,task789"
                     Note: Only active (incomplete) tasks can be deleted
        """
        try:
            # Parse task IDs
            ids = [tid.strip() for tid in task_ids.split(",") if tid.strip()]
            if not ids:
                return "No valid task IDs provided."

            # Execute batch delete and capture results
            self.task_service.batch_delete_tasks(ids)

            # Return informative message
            if len(ids) == 1:
                return f"Task deletion attempted for {ids[0]}. If the task was already completed, it cannot be deleted and was skipped. Check logs for details."
            else:
                return f"Batch deletion attempted for {len(ids)} tasks. Completed tasks cannot be deleted and were skipped. Check logs for detailed results."
        except Exception as e:
            self.logger.error(f"Error deleting tasks: {e}")
            return self._format_error(e)
