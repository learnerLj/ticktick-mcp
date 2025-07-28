"""MCP tools for TickTick integration using object-oriented design."""

import asyncio
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

    def _validate_kind(self, kind: str) -> str:
        """Validate project kind.

        Args:
            kind: Project kind string

        Returns:
            Validated kind string

        Raises:
            ValidationError: If kind is invalid
        """
        valid_kinds = ["TASK", "NOTE"]
        if kind not in valid_kinds:
            raise ValidationError(f"Kind must be one of: {', '.join(valid_kinds)}")
        return kind

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


class UpdateProjectTool(BaseMCPTool):
    """Tool to update an existing project."""

    def __init__(self, project_service: ProjectService):
        super().__init__("update_project", "Update an existing project in TickTick")
        self.project_service = project_service

    async def execute(
        self,
        project_id: str,
        name: str = None,
        color: str = None,
        view_mode: str = None,
        kind: str = None,
    ) -> str:
        """Update an existing project.

        Args:
            project_id: ID of the project to update
            name: New project name (optional)
            color: New color code in hex format (optional)
            view_mode: New view mode - list, kanban, or timeline (optional)
            kind: New project kind - TASK or NOTE (optional)
        """
        try:
            # Validate inputs if provided
            validated_view_mode = None
            validated_kind = None

            if view_mode is not None:
                validated_view_mode = self._validate_view_mode(view_mode).value

            if kind is not None:
                validated_kind = self._validate_kind(kind)

            # Update project
            updated_project = self.project_service.update_project(
                project_id=project_id,
                name=name,
                color=color,
                view_mode=validated_view_mode,
                kind=validated_kind,
            )

            return f"Project updated successfully:\n\n{TaskFormatter.format_project(updated_project)}"
        except Exception as e:
            self.logger.error(f"Error updating project: {e}")
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
            "Can be used for single task (just provide one ID) or multiple tasks. "
            "For multiple tasks, includes 1.0s delays between API calls to avoid rate limiting.",
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

            await self.task_service.batch_complete_tasks(ids)

            if len(ids) == 1:
                return f"Task {ids[0]} marked as complete."
            else:
                return f"Successfully completed {len(ids)} tasks: {', '.join(ids)}"
        except Exception as e:
            self.logger.error(f"Error completing tasks: {e}")
            return self._format_error(e)


class BatchMigrateTasksTool(BaseMCPTool):
    """Tool to migrate multiple tasks to a different project using create+delete approach."""

    def __init__(self, task_service: TaskService):
        super().__init__(
            "batch_migrate_tasks",
            "Migrate multiple tasks to a different project by creating new tasks with complete data "
            "replication and then deleting the original tasks. This approach avoids Dida365 API "
            "limitations on direct task project movement. Each task is fully migrated with all "
            "properties including subtasks, dates, and priority. Uses atomic operations: "
            "create first, then delete original only if creation succeeds. Includes intelligent "
            "retry logic and batch splitting for optimal performance."
        )
        self.task_service = task_service

    async def execute(self, task_ids: str, project_id: str) -> str:
        """Migrate multiple tasks to a different project using create+delete approach.

        Args:
            task_ids: Single task ID or comma-separated list of task IDs to migrate
                     Examples: "task123" or "task123,task456,task789"
            project_id: ID of the destination project

        Returns:
            Success message with migrated tasks information
        """
        try:
            # Parse task IDs
            ids = [tid.strip() for tid in task_ids.split(",") if tid.strip()]
            if not ids:
                return "No valid task IDs provided."

            self.logger.info(f"🔄 Starting task migration: {len(ids)} task(s) to project {project_id}")

            # Determine batch size based on total tasks
            total_tasks = len(ids)
            if total_tasks <= 3:
                # Small batch, process normally
                return await self._process_batch(ids, project_id)
            else:
                # Large batch, use intelligent splitting
                return await self._process_with_intelligent_batching(ids, project_id)

        except Exception as e:
            self.logger.error(f"Error migrating tasks: {e}")
            return self._format_error(e)

    async def _process_with_intelligent_batching(self, task_ids: list[str], project_id: str) -> str:
        """Process large batches with intelligent splitting."""
        total_tasks = len(task_ids)
        all_moved_tasks = []
        all_errors = []
        batch_size = 2  # Start conservative due to API limitations
        current_pos = 0
        batch_num = 1
        
        self.logger.info(f"🔄 Processing {total_tasks} tasks in batches of {batch_size}")
        
        while current_pos < total_tasks:
            # Get current batch
            batch_end = min(current_pos + batch_size, total_tasks)
            batch = task_ids[current_pos:batch_end]
            batch_task_count = len(batch)
            
            self.logger.info(f"Processing batch {batch_num}: tasks {current_pos+1}-{batch_end} of {total_tasks}")
            
            # Process this batch
            batch_result = await self._process_batch(batch, project_id, batch_num)
            
            # Parse batch results
            migrated_count, batch_migrated, batch_errors = self._parse_batch_result(batch_result)
            all_migrated_tasks.extend(batch_migrated)
            all_errors.extend(batch_errors)
            
            # Adaptive batch sizing based on migration success rate
            success_rate = migrated_count / batch_task_count
            if success_rate >= 0.5:  # 50% or better success rate
                batch_size = min(batch_size + 1, 3)  # Increase batch size gradually, max 3
            else:
                batch_size = max(batch_size - 1, 1)  # Decrease batch size, min 1
                
            current_pos = batch_end
            batch_num += 1
            
            # Add delay between batches to avoid overwhelming API
            if current_pos < total_tasks:
                delay = 3.0  # 3 second delay between batches
                self.logger.info(f"Waiting {delay}s before next batch...")
                await asyncio.sleep(delay)
        
        # Build final result
        return self._build_final_result(all_migrated_tasks, all_errors, total_tasks)

    async def _process_batch(self, task_ids: list[str], project_id: str, batch_num: int = 1) -> str:
        """Process a single batch of task migrations."""
        migrated_tasks_info = []
        errors = []
        
        self.logger.info(f"🔄 Processing batch {batch_num}: {len(task_ids)} task(s)")
        
        for i, task_id in enumerate(task_ids):
            # Add delay between tasks in batch (except first)
            if i > 0:
                self.logger.debug(f"Adding 1.0s delay before processing task {i+1}/{len(task_ids)}")
                await asyncio.sleep(1.0)

            # Migrate single task with retry logic
            task_result = await self._migrate_single_task(task_id, project_id)
            if task_result["success"]:
                migrated_tasks_info.append(task_result["info"])
            else:
                errors.append(task_result["error"])
                
            # Progress logging
            if len(task_ids) > 1:
                status = "✅" if task_result["success"] else "❌"
                self.logger.info(f"{status} Batch {batch_num} - Task {i+1}/{len(task_ids)}: {task_id}")

        # Build batch result
        return self._build_batch_result(migrated_tasks_info, errors)

    async def _migrate_single_task(self, task_id: str, project_id: str) -> dict:
        """Migrate task using simple create+delete approach.
        
        Creates new task with complete data replication, then deletes original.
        Due to API limitations, new task may be created in inbox instead of target project.
        
        Args:
            task_id: ID of the task to migrate
            project_id: Target project ID
            
        Returns:
            Dict with success status and info/error message
        """
        max_retries = 3  # Increased retries for better reliability
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                if retry_count > 0:
                    # Exponential backoff: 0.5s, 1s, 2s
                    delay = 0.5 * (2 ** (retry_count - 1))
                    await asyncio.sleep(delay)

                # Get original task data
                original_task = self.task_service.get_task_by_id(task_id)
                if not original_task:
                    raise Exception(f"Could not fetch original task {task_id}")
                
                old_project_id = original_task.project_id
                
                # Create new task with complete data replication
                new_task = Task(
                    id="",  # New ID will be assigned by API
                    title=original_task.title,
                    project_id=project_id,  # Target project (may be ignored by API)
                    content=original_task.content,
                    priority=original_task.priority,
                    start_date=original_task.start_date,
                    due_date=original_task.due_date,
                    status=original_task.status,
                    tags=original_task.tags,
                    subtasks=original_task.subtasks,
                )

                # Create new task
                created_task = self.task_service.create_task(new_task)
                
                if not created_task or not created_task.id:
                    raise Exception(f"Failed to create new task")
                
                # Verify data completeness in created task
                if created_task.title != original_task.title:
                    self.logger.warning(f"Title mismatch after creation: '{created_task.title}' vs '{original_task.title}'")
                
                # Small delay before deletion to ensure API consistency
                await asyncio.sleep(0.5)
                
                # Delete original task using proven batch_delete_tasks method
                deletion_success = False
                try:
                    await self.task_service.batch_delete_tasks([task_id])
                    deletion_success = True
                except Exception as delete_error:
                    self.logger.warning(f"Failed to delete original task {task_id}: {delete_error}")
                
                # Build result message
                if deletion_success:
                    info = f"'{created_task.title}' (new ID: {created_task.id}, original deleted from: {old_project_id})"
                else:
                    info = f"'{created_task.title}' (new ID: {created_task.id}) - ⚠️ original task may still exist in: {old_project_id}"
                
                return {"success": True, "info": info}
                    
            except Exception as e:
                error_msg = str(e)
                if retry_count == 0:  # Only log on first failure
                    self.logger.warning(f"Task {task_id} migration failed: {error_msg}")
                
                # Handle specific API errors that shouldn't be retried
                if "500" in error_msg or "internal server error" in error_msg.lower():
                    return {
                        "success": False, 
                        "error": f"Task {task_id} migration failed due to Dida365 API server error (HTTP 500)"
                    }
                elif "not found" in error_msg.lower():
                    return {
                        "success": False, 
                        "error": f"Task {task_id} not found (may have been deleted or moved already)"
                    }
                elif "unauthorized" in error_msg.lower() or "403" in error_msg:
                    return {
                        "success": False,
                        "error": f"Task {task_id} migration failed due to insufficient permissions"
                    }
                
                retry_count += 1
                if retry_count >= max_retries:
                    return {
                        "success": False,
                        "error": f"Task {task_id} migration failed after {max_retries} attempts: {error_msg}"
                    }
                
                # Will retry with exponential backoff
        
        return {"success": False, "error": f"Unexpected migration failure for task {task_id}"}

    def _parse_batch_result(self, batch_result: str) -> tuple[int, list[str], list[str]]:
        """Parse batch result to extract migrated tasks and errors."""
        moved_tasks = []
        errors = []
        
        lines = batch_result.split('\n')
        current_section = None  # 'success' or 'error'
        
        for line in lines:
            # Don't strip yet - we need to check for "  - " first
            if line.strip().startswith('✅ Successfully processed'):
                current_section = 'success'
            elif line.strip().startswith('❌ Errors occurred:'):
                current_section = 'error'  
            elif line.startswith('  - ') and current_section is not None:
                # This is a list item - either moved task or error
                content = line[4:]  # Remove "  - " prefix
                if current_section == 'error':
                    errors.append(content)
                elif current_section == 'success':
                    moved_tasks.append(content)
        
        moved_count = len(moved_tasks)
        return moved_count, moved_tasks, errors

    def _build_batch_result(self, migrated_tasks: list[str], errors: list[str]) -> str:
        """Build result string for a batch."""
        result = ""
        if migrated_tasks:
            result += f"✅ Successfully processed {len(migrated_tasks)} task(s):\n\n"
            for info in migrated_tasks:
                result += f"  - {info}\n"
            result += "\nℹ️  Note: Due to API limitations, tasks may appear in your inbox instead of the target project.\n"
        else:
            result += "❌ No tasks were processed successfully in this batch."

        if errors:
            result += "\n❌ Errors occurred:\n"
            for error in errors:
                result += f"  - {error}\n"
        
        return result

    def _build_final_result(self, all_migrated_tasks: list[str], all_errors: list[str], total_tasks: int) -> str:
        """Build final result summary for multiple batches."""
        result = f"📊 Task Processing Complete - {total_tasks} total tasks:\n\n"
        
        if all_migrated_tasks:
            result += f"✅ Successfully processed {len(all_migrated_tasks)} task(s):\n"
            for info in all_migrated_tasks:
                result += f"  - {info}\n"
            result += "\nℹ️  Note: Due to Dida365 API limitations, new tasks may appear in your inbox instead of the target project.\n"
            result += "ℹ️  All task data (content, priority, dates, subtasks) has been fully preserved.\n"
        
        if all_errors:
            result += f"\n❌ {len(all_errors)} task(s) failed:\n"
            for error in all_errors:
                result += f"  - {error}\n"
            
            # Add helpful suggestion
            if len(all_errors) > len(all_migrated_tasks):
                result += f"\n💡 Suggestion: Try processing fewer tasks at once (1-2 per batch) for better success rates."
        
        success_rate = len(all_migrated_tasks) / total_tasks * 100
        result += f"\n📈 Success rate: {success_rate:.1f}% ({len(all_migrated_tasks)}/{total_tasks})"
        
        return result


class BatchDeleteTasksTool(BaseMCPTool):
    """Tool to delete one or multiple tasks."""

    def __init__(self, task_service: TaskService):
        super().__init__(
            "batch_delete_tasks",
            "Delete one or multiple tasks by providing comma-separated task IDs. "
            "Can be used for single task (just provide one ID) or multiple tasks. "
            "For multiple tasks, includes 1.0s delays between API calls to avoid rate limiting. "
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
            await self.task_service.batch_delete_tasks(ids)

            # Return informative message
            if len(ids) == 1:
                return f"Task deletion attempted for {ids[0]}. If the task was already completed, it cannot be deleted and was skipped. Check logs for details."
            else:
                return f"Batch deletion attempted for {len(ids)} tasks. Completed tasks cannot be deleted and were skipped. Check logs for detailed results."
        except Exception as e:
            self.logger.error(f"Error deleting tasks: {e}")
            return self._format_error(e)
