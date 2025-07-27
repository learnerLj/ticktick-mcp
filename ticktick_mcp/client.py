"""Modern object-oriented TickTick API client."""

import base64
from typing import List, Optional, Dict, Any
import requests
from abc import ABC, abstractmethod

from .config import ConfigManager, TickTickConfig
from .exceptions import APIError, AuthenticationError, NetworkError
from .logging_config import LoggerManager
from .models import Task, Project, TaskFilter, Priority, TaskStatus, ViewMode


class BaseAPIClient(ABC):
    """Abstract base class for API clients."""

    @abstractmethod
    def make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """Make an API request."""
        pass


class HTTPClient:
    """HTTP client for making requests."""

    def __init__(self, base_url: str, default_headers: Optional[Dict[str, str]] = None):
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
        data: Optional[Dict] = None,
        headers: Optional[Dict[str, str]] = None,
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

    def __init__(self, config_manager: Optional[ConfigManager] = None):
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
                "Accept-Encoding": None,
                "User-Agent": "TickTick-MCP-Client/1.0",
            },
        )
        
        # Initialize authentication manager
        self.auth_manager = AuthenticationManager(self.config, self.config_manager)

    def make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
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
                    self.http_client.default_headers["Authorization"] = f"Bearer {self.config.access_token}"
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
                except:
                    error_msg = response.text or error_msg
                    
                raise APIError(error_msg, response.status_code)

            # Return empty dict for 204 No Content
            if response.status_code == 204 or not response.text:
                return {}

            return response.json()

        except NetworkError:
            raise
        except Exception as e:
            if isinstance(e, (AuthenticationError, APIError)):
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

    def get_all_tasks(self, task_filter: Optional[TaskFilter] = None) -> List[Task]:
        """Get all tasks with optional filtering.
        
        Args:
            task_filter: Optional filter criteria
            
        Returns:
            List of tasks
        """
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
        else:
            # Default parameters similar to original implementation
            params.append("limit=50")
        
        if params:
            endpoint += "?" + "&".join(params)

        response = self.api_client.make_request("GET", endpoint)
        
        # Handle both list and dict responses
        if isinstance(response, list):
            return [Task.from_dict(task_data) for task_data in response]
        elif isinstance(response, dict) and "data" in response:
            return [Task.from_dict(task_data) for task_data in response["data"]]
        
        return []

    def get_task_by_id(self, task_id: str) -> Task:
        """Get task by ID.
        
        Args:
            task_id: Task ID
            
        Returns:
            Task instance
        """
        response = self.api_client.make_request("GET", f"/task/{task_id}")
        return Task.from_dict(response)

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
        response = self.api_client.make_request("POST", f"/task/{task.id}", task.to_dict())
        return Task.from_dict(response)

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
        self.api_client.make_request("POST", f"/project/{project_id}/task/{task_id}/complete")
        return True

    def batch_complete_tasks(self, task_ids: List[str]) -> bool:
        """Complete multiple tasks.
        
        Args:
            task_ids: List of task IDs
            
        Returns:
            True if successful
        """
        data = {"taskIds": task_ids, "status": TaskStatus.COMPLETED.value}
        self.api_client.make_request("POST", "/task/batch/complete", data)
        return True

    def batch_delete_tasks(self, task_ids: List[str]) -> bool:
        """Delete multiple tasks.
        
        Args:
            task_ids: List of task IDs
            
        Returns:
            True if successful
        """
        data = {"taskIds": task_ids}
        self.api_client.make_request("POST", "/task/batch/delete", data)
        return True


class ProjectService:
    """Service class for project operations."""

    def __init__(self, api_client: TickTickAPIClient):
        """Initialize project service.
        
        Args:
            api_client: TickTick API client
        """
        self.api_client = api_client
        self.logger = LoggerManager().get_logger("project_service")

    def get_all_projects(self) -> List[Project]:
        """Get all projects.
        
        Returns:
            List of projects
        """
        response = self.api_client.make_request("GET", "/project")
        
        # Handle both list and dict responses
        if isinstance(response, list):
            return [Project.from_dict(project_data) for project_data in response]
        elif isinstance(response, dict) and "data" in response:
            return [Project.from_dict(project_data) for project_data in response["data"]]
        
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

    def delete_project(self, project_id: str) -> bool:
        """Delete a project.
        
        Args:
            project_id: Project ID
            
        Returns:
            True if successful
        """
        self.api_client.make_request("DELETE", f"/project/{project_id}")
        return True

    def get_project_tasks(self, project_id: str) -> List[Task]:
        """Get all tasks in a project.
        
        Args:
            project_id: Project ID
            
        Returns:
            List of tasks
        """
        response = self.api_client.make_request("GET", f"/project/{project_id}/data")
        
        tasks_data = response.get("tasks", [])
        return [Task.from_dict(task_data) for task_data in tasks_data]