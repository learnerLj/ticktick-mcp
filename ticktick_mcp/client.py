"""Modern object-oriented TickTick API client."""

import base64
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Any

import requests

from .config import ConfigManager, TickTickConfig
from .exceptions import APIError, AuthenticationError, NetworkError
from .logging_config import LoggerManager
from .models import Project, Task, TaskFilter, TaskStatus


class BaseAPIClient(ABC):
    """Abstract base class for API clients."""

    @abstractmethod
    def make_request(
        self, method: str, endpoint: str, data: dict | None = None
    ) -> dict[str, Any]:
        """Make an API request."""
        pass


class HTTPClient:
    """HTTP client for making requests."""

    def __init__(self, base_url: str, default_headers: dict[str, str] | None = None):
        """Initialize HTTP client.

        Args:
            base_url: Base URL for API requests
            default_headers: Default headers to include in requests
        """
        self.base_url = base_url.rstrip("/")
        self.default_headers = default_headers or {}
        self.session = requests.Session()

    def request(
        self,
        method: str,
        endpoint: str,
        data: dict | None = None,
        headers: dict[str, str] | None = None,
        timeout: int = 30,
    ) -> requests.Response:
        """Make HTTP request.

        Args:
            method: HTTP method
            endpoint: API endpoint
            data: Request data
            headers: Additional headers
            timeout: Request timeout

        Returns:
            Response object

        Raises:
            NetworkError: If request fails
        """
        url = f"{self.base_url}{endpoint}"

        # Merge headers
        request_headers = {**self.default_headers}
        if headers:
            request_headers.update(headers)

        try:
            response = self.session.request(
                method=method,
                url=url,
                json=data if method in ("POST", "PUT", "PATCH") else None,
                headers=request_headers,
                timeout=timeout,
            )
            return response
        except requests.exceptions.RequestException as e:
            raise NetworkError(f"Network request failed: {str(e)}") from e


class AuthenticationManager:
    """Manages OAuth2 authentication for TickTick API."""

    def __init__(self, config: TickTickConfig, config_manager: ConfigManager):
        """Initialize authentication manager.

        Args:
            config: TickTick configuration
            config_manager: Configuration manager for saving tokens
        """
        self.config = config
        self.config_manager = config_manager
        self.logger = LoggerManager().get_logger("auth")

    def refresh_access_token(self) -> bool:
        """Refresh the access token using refresh token.

        Returns:
            True if successful, False otherwise
        """
        if not self.config.refresh_token:
            self.logger.warning("No refresh token available")
            return False

        # Prepare token request
        token_data = {
            "grant_type": "refresh_token",
            "refresh_token": self.config.refresh_token,
        }

        # Create Basic Auth header
        auth_str = f"{self.config.client_id}:{self.config.client_secret}"
        auth_bytes = auth_str.encode("ascii")
        auth_b64 = base64.b64encode(auth_bytes).decode("ascii")

        headers = {
            "Authorization": f"Basic {auth_b64}",
            "Content-Type": "application/x-www-form-urlencoded",
        }

        try:
            response = requests.post(
                self.config.token_url,
                data=token_data,
                headers=headers,
                timeout=30,
            )
            response.raise_for_status()

            tokens = response.json()
            access_token = tokens.get("access_token")
            refresh_token = tokens.get("refresh_token")

            if access_token:
                # Update config
                self.config.access_token = access_token
                if refresh_token:
                    self.config.refresh_token = refresh_token

                # Save tokens
                self.config_manager.save_tokens(access_token, refresh_token)
                self.logger.info("Access token refreshed successfully")
                return True

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to refresh token: {e}")

        return False


class TickTickAPIClient(BaseAPIClient):
    """Modern TickTick API client with OOP design."""

    def __init__(self, config_manager: ConfigManager | None = None):
        """Initialize TickTick API client.

        Args:
            config_manager: Configuration manager instance
        """
        self.config_manager = config_manager or ConfigManager()
        self.config = self.config_manager.load_config()
        self.logger = LoggerManager().get_logger("api_client")

        # Initialize HTTP client
        self.http_client = HTTPClient(
            base_url=self.config.base_url,
            default_headers={
                "Authorization": f"Bearer {self.config.access_token}",
                "Content-Type": "application/json",
                "User-Agent": "TickTick-MCP-Client/1.0",
            },
        )

        # Initialize authentication manager
        self.auth_manager = AuthenticationManager(self.config, self.config_manager)

    def make_request(
        self, method: str, endpoint: str, data: dict | None = None
    ) -> dict[str, Any] | list[Any] | Any:
        """Make API request with automatic token refresh.

        Args:
            method: HTTP method
            endpoint: API endpoint
            data: Request data

        Returns:
            API response data

        Raises:
            AuthenticationError: If authentication fails
            APIError: If API returns an error
        """
        if not self.config.access_token:
            raise AuthenticationError("No access token available")

        try:
            response = self.http_client.request(method, endpoint, data)

            # Handle 401 - try to refresh token
            if response.status_code == 401:
                self.logger.info("Access token expired, attempting refresh")

                if self.auth_manager.refresh_access_token():
                    # Update HTTP client headers with new token
                    self.http_client.default_headers["Authorization"] = (
                        f"Bearer {self.config.access_token}"
                    )
                    # Retry request
                    response = self.http_client.request(method, endpoint, data)
                else:
                    raise AuthenticationError("Failed to refresh access token")

            # Handle other HTTP errors
            if not response.ok:
                error_msg = f"API request failed: {response.status_code}"
                try:
                    error_data = response.json()
                    if "error" in error_data:
                        error_msg = error_data["error"]
                except (ValueError, TypeError):
                    error_msg = response.text or error_msg

                raise APIError(error_msg, response.status_code)

            # Return empty dict for 204 No Content
            if response.status_code == 204 or not response.text:
                return {}

            result = response.json()
            # Return the actual result - can be dict, list, or other JSON types
            return result

        except NetworkError:
            raise
        except Exception as e:
            if isinstance(e, AuthenticationError | APIError):
                raise
            raise APIError(f"Unexpected error: {str(e)}") from e


class TaskService:
    """Service class for task operations."""

    def __init__(self, api_client: TickTickAPIClient):
        """Initialize task service.

        Args:
            api_client: TickTick API client
        """
        self.api_client = api_client
        self.logger = LoggerManager().get_logger("task_service")

    def get_all_tasks(self, task_filter: TaskFilter | None = None) -> list[Task]:
        """Get all tasks across all projects.

        Since Dida365 API doesn't support global task retrieval directly,
        this method iterates through all projects and collects their tasks.

        Args:
            task_filter: Optional filter criteria

        Returns:
            List of tasks from all projects
        """
        all_tasks = []

        try:
            # Get all projects first
            projects_data = self.api_client.make_request("GET", "/project")

            # Handle case where API returns list directly or wrapped in a dict
            if isinstance(projects_data, list):
                projects = projects_data
            else:
                # Assume it's a dict with the projects list under some key
                projects = projects_data.get("projects", [])

            # Add the special "inbox" project for tasks without a project
            project_ids = [
                project.get("id") for project in projects if project.get("id")
            ]

            # Try to add inbox with different possible IDs
            possible_inbox_ids = ["inbox", "inbox1017224327"]
            for inbox_id in possible_inbox_ids:
                if inbox_id not in project_ids:  # Avoid duplicates
                    project_ids.append(inbox_id)

            # Iterate through each project to get its tasks
            for project_id in project_ids:
                try:
                    # Get tasks for this specific project
                    project_tasks = self.get_project_tasks(project_id)

                    # Apply filtering if specified
                    if task_filter:
                        filtered_tasks = []
                        for task in project_tasks:
                            # Apply status filter
                            if task_filter.status and task.status != task_filter.status:
                                continue
                            # Apply priority filter
                            if (
                                task_filter.priority
                                and task.priority != task_filter.priority
                            ):
                                continue
                            # Apply project filter
                            if (
                                task_filter.project_id
                                and task.project_id != task_filter.project_id
                            ):
                                continue
                            # Apply query filter (search in title and content)
                            if task_filter.query:
                                query_lower = task_filter.query.lower()
                                if query_lower not in task.title.lower() and (
                                    not task.content
                                    or query_lower not in task.content.lower()
                                ):
                                    continue
                            filtered_tasks.append(task)
                        all_tasks.extend(filtered_tasks)
                    else:
                        all_tasks.extend(project_tasks)

                except Exception as e:
                    # Log the error but continue with other projects
                    # Don't treat individual project failures as total failure
                    self.logger.debug(f"Skipping project {project_id}: {e}")
                    continue

            # Apply limit if specified in filter
            if task_filter and task_filter.limit:
                all_tasks = all_tasks[: task_filter.limit]

            return all_tasks

        except Exception as e:
            # Only fallback for critical errors, not individual project failures
            if "projects" in str(e).lower() or "permission" in str(e).lower():
                self.logger.warning(
                    f"Project access failed: {e}. Trying direct API call..."
                )

                endpoint = "/task"
                params = []

                if task_filter:
                    if task_filter.status:
                        params.append(f"status={task_filter.status.value}")
                    if task_filter.limit:
                        params.append(f"limit={task_filter.limit}")
                    if task_filter.priority:
                        params.append(f"priority={task_filter.priority.value}")
                    if task_filter.project_id:
                        params.append(f"projectId={task_filter.project_id}")
                    if task_filter.query:
                        params.append(f"q={task_filter.query}")
                # Note: No default limit - let API return all tasks unless user specifies a limit

                if params:
                    endpoint += "?" + "&".join(params)

                response = self.api_client.make_request("GET", endpoint)

                # Handle both list and dict responses
                if isinstance(response, list):
                    return [Task.from_dict(task_data) for task_data in response]
                elif isinstance(response, dict) and "data" in response:
                    return [Task.from_dict(task_data) for task_data in response["data"]]

                return []
            else:
                # Re-raise non-critical errors
                raise e

    def get_task_by_id(self, task_id: str) -> Task:
        """Get task by ID.

        Since Dida365 doesn't support direct task access by ID,
        this method searches through all tasks to find the matching one.

        Args:
            task_id: Task ID

        Returns:
            Task instance

        Raises:
            Exception: If task not found
        """
        # Get all tasks and search for the matching ID
        all_tasks = self.get_all_tasks()

        for task in all_tasks:
            if task.id == task_id:
                return task

        raise Exception(f"Task with ID {task_id} not found")

    def get_project_tasks(self, project_id: str) -> list[Task]:
        """Get all tasks in a project.

        Args:
            project_id: Project ID

        Returns:
            List of tasks in the project
        """
        response = self.api_client.make_request("GET", f"/project/{project_id}/data")

        tasks_data = response.get("tasks", [])
        return [Task.from_dict(task_data) for task_data in tasks_data]

    def create_task(self, task: Task) -> Task:
        """Create a new task.

        Args:
            task: Task to create

        Returns:
            Created task
        """
        response = self.api_client.make_request("POST", "/task", task.to_dict())
        return Task.from_dict(response)

    def update_task(self, task: Task) -> Task:
        """Update an existing task.

        Args:
            task: Task to update

        Returns:
            Updated task
        """
        try:
            # Use the correct API format based on jacepark12/ticktick-mcp implementation
            # The API expects: id, projectId, and other fields
            task_data = {
                "id": task.id,
                "projectId": task.project_id,  # Use projectId not project_id
            }

            # Add optional fields if they exist
            if task.title:
                task_data["title"] = task.title
            if task.content:
                task_data["content"] = task.content
            if task.priority:
                task_data["priority"] = task.priority.value
            if task.start_date:
                task_data["startDate"] = task.start_date
            if task.due_date:
                task_data["dueDate"] = task.due_date

            response = self.api_client.make_request(
                "POST", f"/task/{task.id}", task_data
            )

            # If response is empty (successful update), return the updated task
            if not response or response == {}:
                # Return the task with updated data
                return task
            else:
                return Task.from_dict(response)

        except Exception as e:
            self.logger.warning(
                f"Direct task update failed: {e}. Using fallback method."
            )

            # Fallback: Since direct update may not work, we'll recreate the task
            # Note: This will change the task ID
            try:
                # First try to delete the old task if we can find its project
                if task.project_id:
                    try:
                        self.delete_task(task.project_id, task.id)
                    except Exception:
                        pass  # Ignore delete errors

                # Create new task with updated data
                new_task = self.create_task(task)
                self.logger.info(f"Task updated via recreation. New ID: {new_task.id}")
                return new_task

            except Exception as fallback_error:
                raise Exception(
                    f"Both direct update and fallback failed: {str(e)}, {str(fallback_error)}"
                ) from fallback_error

    def delete_task(self, project_id: str, task_id: str) -> bool:
        """Delete a task.

        Args:
            project_id: Project ID
            task_id: Task ID

        Returns:
            True if successful
        """
        self.api_client.make_request("DELETE", f"/project/{project_id}/task/{task_id}")
        return True

    def complete_task(self, project_id: str, task_id: str) -> bool:
        """Mark task as complete.

        Args:
            project_id: Project ID
            task_id: Task ID

        Returns:
            True if successful
        """
        self.api_client.make_request(
            "POST", f"/project/{project_id}/task/{task_id}/complete"
        )
        return True

    async def batch_complete_tasks(self, task_ids: list[str]) -> bool:
        """Complete multiple tasks.

        Since Dida365 doesn't support batch operations,
        this method completes tasks one by one with delays to avoid rate limiting.

        Args:
            task_ids: List of task IDs

        Returns:
            True if successful
        """
        import asyncio
        
        success_count = 0
        for i, task_id in enumerate(task_ids):
            try:
                # Add delay between API calls to avoid rate limiting (except for first task)
                if i > 0:
                    await asyncio.sleep(1.0)  # Increased to 1.0s for consistency
                
                # Get task to find its project
                task = self.get_task_by_id(task_id)
                # Complete the task
                if task.project_id:
                    self.complete_task(task.project_id, task_id)
                else:
                    # Skip tasks without project_id
                    self.logger.warning(f"Task {task_id} has no project_id, skipping")
                    continue
                success_count += 1
                
                # Log progress for multiple tasks
                if len(task_ids) > 1:
                    self.logger.info(f"Completed task {i+1}/{len(task_ids)}: {task_id}")
                    
            except Exception as e:
                self.logger.warning(f"Failed to complete task {task_id}: {e}")

        if success_count == 0:
            raise Exception("Failed to complete any tasks")
        elif success_count < len(task_ids):
            self.logger.warning(f"Only completed {success_count}/{len(task_ids)} tasks")

        return True

    async def batch_delete_tasks(self, task_ids: list[str]) -> bool:
        """Delete multiple tasks.

        Since Dida365 doesn't support batch operations,
        this method deletes tasks one by one with delays to avoid rate limiting.
        Note: Completed tasks cannot be deleted and will be skipped.

        Args:
            task_ids: List of task IDs

        Returns:
            True if successful
        """
        import asyncio
        
        success_count = 0
        failed_tasks = []
        completed_tasks = []
        not_found_tasks = []

        for i, task_id in enumerate(task_ids):
            try:
                # Add delay between API calls to avoid rate limiting (except for first task)
                if i > 0:
                    await asyncio.sleep(1.0)  # Increased to 1.0s for consistency
                
                # Get task to find its project and check status
                task = self.get_task_by_id(task_id)

                # Check if task is completed
                if task.status == TaskStatus.COMPLETED:
                    completed_tasks.append(task_id)
                    self.logger.info(
                        f"Skipping completed task {task_id} - completed tasks cannot be deleted"
                    )
                    continue

                # Delete the task
                if task.project_id:
                    self.delete_task(task.project_id, task_id)
                else:
                    # Skip tasks without project_id
                    self.logger.warning(f"Task {task_id} has no project_id, skipping")
                    continue
                success_count += 1
                
                # Log progress for multiple tasks
                if len(task_ids) > 1:
                    self.logger.info(f"Deleted task {i+1}/{len(task_ids)}: {task_id}")

            except Exception as e:
                if "not found" in str(e).lower():
                    not_found_tasks.append(task_id)
                    self.logger.info(
                        f"Task {task_id} not found - likely already deleted or completed"
                    )
                else:
                    failed_tasks.append(task_id)
                    self.logger.warning(f"Failed to delete task {task_id}: {e}")

        # Provide detailed results
        results = []
        if success_count > 0:
            results.append(f"Successfully deleted {success_count} tasks")
        if completed_tasks:
            results.append(
                f"Skipped {len(completed_tasks)} completed tasks (cannot delete)"
            )
        if not_found_tasks:
            results.append(
                f"Skipped {len(not_found_tasks)} tasks that were not found (likely completed/deleted)"
            )
        if failed_tasks:
            results.append(f"Failed to delete {len(failed_tasks)} tasks")

        # Consider the operation successful if we had some success or valid skips
        if success_count == 0 and not completed_tasks and not not_found_tasks:
            raise Exception("Failed to delete any tasks")

        return True

    def get_overdue_tasks(self) -> list[Task]:
        """Get all overdue tasks.

        Returns:
            List of overdue tasks
        """
        all_tasks = self.get_all_tasks()
        today = datetime.now().date()

        overdue_tasks = []
        for task in all_tasks:
            if task.due_date and task.status != TaskStatus.COMPLETED:
                # Parse task due date
                if isinstance(task.due_date, str):
                    try:
                        # Handle ISO format: 2024-01-15T00:00:00+0000
                        task_date = datetime.fromisoformat(
                            task.due_date.replace("Z", "+00:00")
                        ).date()
                        if task_date < today:
                            overdue_tasks.append(task)
                    except ValueError:
                        # If parsing fails, skip this task
                        self.logger.warning(
                            f"Failed to parse due date for task {task.id}: {task.due_date}"
                        )
                        continue
                elif hasattr(task.due_date, "date"):
                    # If it's already a datetime object
                    if task.due_date.date() < today:
                        overdue_tasks.append(task)

        return overdue_tasks

    def get_today_tasks(self) -> list[Task]:
        """Get all tasks due today.

        Returns:
            List of tasks due today
        """
        all_tasks = self.get_all_tasks()
        today = datetime.now().date()

        today_tasks = []
        for task in all_tasks:
            if task.due_date and task.status != TaskStatus.COMPLETED:
                # Parse task due date
                if isinstance(task.due_date, str):
                    try:
                        # Handle ISO format: 2024-01-15T00:00:00+0000
                        task_date = datetime.fromisoformat(
                            task.due_date.replace("Z", "+00:00")
                        ).date()
                        if task_date == today:
                            today_tasks.append(task)
                    except ValueError:
                        # If parsing fails, skip this task
                        self.logger.warning(
                            f"Failed to parse due date for task {task.id}: {task.due_date}"
                        )
                        continue
                elif hasattr(task.due_date, "date"):
                    # If it's already a datetime object
                    if task.due_date.date() == today:
                        today_tasks.append(task)

        return today_tasks

    def get_next_7_days_tasks(self) -> list[Task]:
        """Get all tasks due in the next 7 days (including today).

        Returns:
            List of tasks due in next 7 days
        """
        all_tasks = self.get_all_tasks()
        today = datetime.now().date()
        next_week = today + timedelta(days=7)

        next_7_days_tasks = []
        for task in all_tasks:
            if task.due_date and task.status != TaskStatus.COMPLETED:
                # Parse task due date
                if isinstance(task.due_date, str):
                    try:
                        # Handle ISO format: 2024-01-15T00:00:00+0000
                        task_date = datetime.fromisoformat(
                            task.due_date.replace("Z", "+00:00")
                        ).date()
                        if today <= task_date <= next_week:
                            next_7_days_tasks.append(task)
                    except ValueError:
                        # If parsing fails, skip this task
                        self.logger.warning(
                            f"Failed to parse due date for task {task.id}: {task.due_date}"
                        )
                        continue
                elif hasattr(task.due_date, "date"):
                    # If it's already a datetime object
                    if today <= task.due_date.date() <= next_week:
                        next_7_days_tasks.append(task)

        return next_7_days_tasks


class ProjectService:
    """Service class for project operations."""

    def __init__(self, api_client: TickTickAPIClient):
        """Initialize project service.

        Args:
            api_client: TickTick API client
        """
        self.api_client = api_client
        self.logger = LoggerManager().get_logger("project_service")

    def get_all_projects(self) -> list[Project]:
        """Get all projects.

        Returns:
            List of projects
        """
        response = self.api_client.make_request("GET", "/project")

        # Handle both list and dict responses
        if isinstance(response, list):
            return [Project.from_dict(project_data) for project_data in response]
        elif isinstance(response, dict) and "data" in response:
            return [
                Project.from_dict(project_data) for project_data in response["data"]
            ]

        return []

    def get_project_by_id(self, project_id: str) -> Project:
        """Get project by ID.

        Args:
            project_id: Project ID

        Returns:
            Project instance
        """
        response = self.api_client.make_request("GET", f"/project/{project_id}")
        return Project.from_dict(response)

    def create_project(self, project: Project) -> Project:
        """Create a new project.

        Args:
            project: Project to create

        Returns:
            Created project
        """
        response = self.api_client.make_request("POST", "/project", project.to_dict())
        return Project.from_dict(response)

    def update_project(
        self,
        project_id: str,
        name: str = None,
        color: str = None,
        view_mode: str = None,
        kind: str = None,
    ) -> Project:
        """Update an existing project.

        Args:
            project_id: Project ID
            name: Project name (optional)
            color: Project color (optional)
            view_mode: View mode (optional)
            kind: Project kind (optional)

        Returns:
            Updated project
        """
        # Build update data
        update_data = {}
        if name is not None:
            update_data["name"] = name
        if color is not None:
            update_data["color"] = color
        if view_mode is not None:
            update_data["viewMode"] = view_mode
        if kind is not None:
            update_data["kind"] = kind

        response = self.api_client.update_project(
            project_id=project_id,
            name=name,
            color=color,
            view_mode=view_mode,
            kind=kind,
        )
        return Project.from_dict(response)

    def delete_project(self, project_id: str) -> bool:
        """Delete a project.

        Args:
            project_id: Project ID

        Returns:
            True if successful
        """
        self.api_client.make_request("DELETE", f"/project/{project_id}")
        return True

    def get_project_tasks(self, project_id: str) -> list[Task]:
        """Get all tasks in a project.

        Args:
            project_id: Project ID

        Returns:
            List of tasks
        """
        response = self.api_client.make_request("GET", f"/project/{project_id}/data")

        tasks_data = response.get("tasks", [])
        return [Task.from_dict(task_data) for task_data in tasks_data]
