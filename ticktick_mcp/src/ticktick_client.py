import base64
import logging
import os
from pathlib import Path

import requests
from dotenv import load_dotenv

# Set up logging
logger = logging.getLogger(__name__)


class TickTickClient:
    """
    Client for the TickTick API using OAuth2 authentication.
    """

    def __init__(self):
        load_dotenv()
        self.client_id = os.getenv("TICKTICK_CLIENT_ID")
        self.client_secret = os.getenv("TICKTICK_CLIENT_SECRET")
        self.access_token = os.getenv("TICKTICK_ACCESS_TOKEN")
        self.refresh_token = os.getenv("TICKTICK_REFRESH_TOKEN")

        if not self.access_token:
            raise ValueError(
                "TICKTICK_ACCESS_TOKEN environment variable is not set. "
                "Please run 'ticktick-mcp auth' to set up your credentials."
            )

        self.base_url = (
            os.getenv("TICKTICK_BASE_URL") or "https://api.ticktick.com/open/v1"
        )
        self.token_url = (
            os.getenv("TICKTICK_TOKEN_URL") or "https://ticktick.com/oauth/token"
        )
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "Accept-Encoding": None,
            "User-Agent": "curl/8.7.1",
        }

    def _refresh_access_token(self) -> bool:
        """
        Refresh the access token using the refresh token.

        Returns:
            True if successful, False otherwise
        """
        if not self.refresh_token:
            logger.warning("No refresh token available. Cannot refresh access token.")
            return False

        if not self.client_id or not self.client_secret:
            logger.warning(
                "Client ID or Client Secret missing. Cannot refresh access token."
            )
            return False

        # Prepare the token request
        token_data = {
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token,
        }

        # Prepare Basic Auth credentials
        auth_str = f"{self.client_id}:{self.client_secret}"
        auth_bytes = auth_str.encode("ascii")
        auth_b64 = base64.b64encode(auth_bytes).decode("ascii")

        headers = {
            "Authorization": f"Basic {auth_b64}",
            "Content-Type": "application/x-www-form-urlencoded",
        }

        try:
            # Send the token request
            response = requests.post(self.token_url, data=token_data, headers=headers)
            response.raise_for_status()

            # Parse the response
            tokens = response.json()

            # Update the tokens
            self.access_token = tokens.get("access_token")
            if "refresh_token" in tokens:
                self.refresh_token = tokens.get("refresh_token")

            # Update the headers
            self.headers["Authorization"] = f"Bearer {self.access_token}"

            # Save the tokens to the .env file
            self._save_tokens_to_env(tokens)

            logger.info("Access token refreshed successfully.")
            return True

        except requests.exceptions.RequestException as e:
            logger.error(f"Error refreshing access token: {e}")
            return False

    def _save_tokens_to_env(self, tokens: dict[str, str]) -> None:
        """
        Save the tokens to the .env file.

        Args:
            tokens: A dictionary containing the access_token and optionally refresh_token
        """
        # Load existing .env file content
        env_path = Path(".env")
        env_content = {}

        if env_path.exists():
            with open(env_path) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        env_content[key] = value

        # Update with new tokens
        env_content["TICKTICK_ACCESS_TOKEN"] = tokens.get("access_token", "")
        if "refresh_token" in tokens:
            env_content["TICKTICK_REFRESH_TOKEN"] = tokens.get("refresh_token", "")

        # Make sure client credentials are saved as well
        if self.client_id and "TICKTICK_CLIENT_ID" not in env_content:
            env_content["TICKTICK_CLIENT_ID"] = self.client_id
        if self.client_secret and "TICKTICK_CLIENT_SECRET" not in env_content:
            env_content["TICKTICK_CLIENT_SECRET"] = self.client_secret

        # Write back to .env file
        with open(env_path, "w") as f:
            for key, value in env_content.items():
                f.write(f"{key}={value}\n")

        logger.debug("Tokens saved to .env file")

    def _make_request(self, method: str, endpoint: str, data=None) -> dict:
        """
        Makes a request to the TickTick API.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint (without base URL)
            data: Request data (for POST, PUT)

        Returns:
            API response as a dictionary
        """
        url = f"{self.base_url}{endpoint}"

        try:
            # Make the request
            if method == "GET":
                response = requests.get(url, headers=self.headers)
            elif method == "POST":
                response = requests.post(url, headers=self.headers, json=data)
            elif method == "DELETE":
                response = requests.delete(url, headers=self.headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            # Check if the request was unauthorized (401)
            if response.status_code == 401:
                logger.info("Access token expired. Attempting to refresh...")

                # Try to refresh the access token
                if self._refresh_access_token():
                    # Retry the request with the new token
                    if method == "GET":
                        response = requests.get(url, headers=self.headers)
                    elif method == "POST":
                        response = requests.post(url, headers=self.headers, json=data)
                    elif method == "DELETE":
                        response = requests.delete(url, headers=self.headers)

            # Raise an exception for 4xx/5xx status codes
            response.raise_for_status()

            # Return empty dict for 204 No Content
            if response.status_code == 204 or response.text == "":
                return {}

            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            return {"error": str(e)}

    # Project methods
    def get_projects(self) -> list[dict]:
        """Gets all projects for the user."""
        return self._make_request("GET", "/project")

    def get_project(self, project_id: str) -> dict:
        """Gets a specific project by ID."""
        return self._make_request("GET", f"/project/{project_id}")

    def get_project_with_data(self, project_id: str) -> dict:
        """Gets project with tasks and columns."""
        return self._make_request("GET", f"/project/{project_id}/data")

    def create_project(
        self,
        name: str,
        color: str = "#F18181",
        view_mode: str = "list",
        kind: str = "TASK",
    ) -> dict:
        """Creates a new project."""
        data = {"name": name, "color": color, "viewMode": view_mode, "kind": kind}
        return self._make_request("POST", "/project", data)

    def update_project(
        self,
        project_id: str,
        name: str = None,
        color: str = None,
        view_mode: str = None,
        kind: str = None,
    ) -> dict:
        """Updates an existing project."""
        data = {}
        if name:
            data["name"] = name
        if color:
            data["color"] = color
        if view_mode:
            data["viewMode"] = view_mode
        if kind:
            data["kind"] = kind

        return self._make_request("POST", f"/project/{project_id}", data)

    def delete_project(self, project_id: str) -> dict:
        """Deletes a project."""
        return self._make_request("DELETE", f"/project/{project_id}")

    # Task methods
    def get_task(self, project_id: str, task_id: str) -> dict:
        """Gets a specific task by project ID and task ID."""
        return self._make_request("GET", f"/project/{project_id}/task/{task_id}")

    def create_task(
        self,
        title: str,
        project_id: str,
        content: str = None,
        start_date: str = None,
        due_date: str = None,
        priority: int = 0,
        is_all_day: bool = False,
    ) -> dict:
        """Creates a new task."""
        data = {"title": title, "projectId": project_id}

        if content:
            data["content"] = content
        if start_date:
            data["startDate"] = start_date
        if due_date:
            data["dueDate"] = due_date
        if priority is not None:
            data["priority"] = priority
        if is_all_day is not None:
            data["isAllDay"] = is_all_day

        return self._make_request("POST", "/task", data)

    def update_task(
        self,
        task_id: str,
        project_id: str,
        title: str = None,
        content: str = None,
        priority: int = None,
        start_date: str = None,
        due_date: str = None,
    ) -> dict:
        """Updates an existing task."""
        data = {"id": task_id, "projectId": project_id}

        if title:
            data["title"] = title
        if content:
            data["content"] = content
        if priority is not None:
            data["priority"] = priority
        if start_date:
            data["startDate"] = start_date
        if due_date:
            data["dueDate"] = due_date

        return self._make_request("POST", f"/task/{task_id}", data)

    def complete_task(self, project_id: str, task_id: str) -> dict:
        """Marks a task as complete."""
        return self._make_request(
            "POST", f"/project/{project_id}/task/{task_id}/complete"
        )

    def delete_task(self, project_id: str, task_id: str) -> dict:
        """Deletes a task."""
        return self._make_request("DELETE", f"/project/{project_id}/task/{task_id}")

    # Global task methods
    def get_all_tasks(self, status: str = None, limit: int = 50) -> dict:
        """
        Gets all tasks for the user across all projects.

        Args:
            status: Task status filter ('active', 'completed', None for all)
            limit: Maximum number of tasks to return (default 50)
        """
        endpoint = "/task"
        params = []

        if status == "active":
            params.append("status=0")
        elif status == "completed":
            params.append("status=2")

        if limit:
            params.append(f"limit={limit}")

        if params:
            endpoint += "?" + "&".join(params)

        return self._make_request("GET", endpoint)

    def search_tasks(
        self,
        query: str = None,
        project_id: str = None,
        priority: int = None,
        status: str = None,
        start_date: str = None,
        end_date: str = None,
    ) -> dict:
        """
        Search tasks with various filters.

        Args:
            query: Search query string
            project_id: Filter by project ID
            priority: Filter by priority (0-5)
            status: Filter by status ('active', 'completed')
            start_date: Filter tasks starting from this date (ISO format)
            end_date: Filter tasks ending before this date (ISO format)
        """
        endpoint = "/task/search"
        params = []

        if query:
            params.append(f"q={query}")
        if project_id:
            params.append(f"projectId={project_id}")
        if priority is not None:
            params.append(f"priority={priority}")
        if status == "active":
            params.append("status=0")
        elif status == "completed":
            params.append("status=2")
        if start_date:
            params.append(f"startDate={start_date}")
        if end_date:
            params.append(f"endDate={end_date}")

        if params:
            endpoint += "?" + "&".join(params)

        return self._make_request("GET", endpoint)

    def get_task_by_id(self, task_id: str) -> dict:
        """Gets a task by its ID without requiring project ID."""
        return self._make_request("GET", f"/task/{task_id}")

    def get_tasks_by_date(
        self, date_from: str = None, date_to: str = None, date_type: str = "due"
    ) -> dict:
        """
        Gets tasks by date range.

        Args:
            date_from: Start date (ISO format)
            date_to: End date (ISO format)
            date_type: Type of date to filter by ('due', 'start', 'created')
        """
        endpoint = "/task"
        params = []

        if date_from:
            params.append(f"{date_type}DateFrom={date_from}")
        if date_to:
            params.append(f"{date_type}DateTo={date_to}")

        if params:
            endpoint += "?" + "&".join(params)

        return self._make_request("GET", endpoint)

    # Batch operation methods
    def batch_complete_tasks(self, task_ids: list[str]) -> dict:
        """Batch complete multiple tasks."""
        data = {"taskIds": task_ids, "status": 2}
        return self._make_request("POST", "/task/batch/complete", data)

    def batch_delete_tasks(self, task_ids: list[str]) -> dict:
        """Batch delete multiple tasks."""
        data = {"taskIds": task_ids}
        return self._make_request("POST", "/task/batch/delete", data)

    def batch_update_tasks(self, task_updates: list[dict]) -> dict:
        """
        Batch update multiple tasks.

        Args:
            task_updates: List of task update objects, each containing 'id' and update fields
        """
        data = {"tasks": task_updates}
        return self._make_request("POST", "/task/batch/update", data)

    def move_task(self, task_id: str, target_project_id: str) -> dict:
        """Move a task to a different project."""
        data = {"projectId": target_project_id}
        return self._make_request("POST", f"/task/{task_id}/move", data)

    def duplicate_task(self, task_id: str, modifications: dict = None) -> dict:
        """
        Duplicate a task with optional modifications.

        Args:
            task_id: ID of the task to duplicate
            modifications: Dictionary of fields to modify in the duplicated task
        """
        # First get the original task
        original_task = self.get_task_by_id(task_id)
        if "error" in original_task:
            return original_task

        # Create new task data based on original
        new_task_data = {
            "title": original_task.get("title", "Copy of task"),
            "content": original_task.get("content"),
            "projectId": original_task.get("projectId"),
            "priority": original_task.get("priority", 0),
            "startDate": original_task.get("startDate"),
            "dueDate": original_task.get("dueDate"),
            "isAllDay": original_task.get("isAllDay", False),
        }

        # Apply modifications if provided
        if modifications:
            new_task_data.update(modifications)

        return self._make_request("POST", "/task", new_task_data)

    def add_subtask(self, parent_task_id: str, subtask_data: dict) -> dict:
        """
        Add a subtask to an existing task.

        Args:
            parent_task_id: ID of the parent task
            subtask_data: Data for the new subtask
        """
        data = {"parentTaskId": parent_task_id, **subtask_data}
        return self._make_request("POST", "/subtask", data)

    def create_recurring_task(self, task_data: dict, recurrence_pattern: str) -> dict:
        """
        Create a recurring task.

        Args:
            task_data: Basic task data
            recurrence_pattern: Recurrence pattern (daily, weekly, monthly, etc.)
        """
        data = {**task_data, "recurrence": recurrence_pattern}
        return self._make_request("POST", "/task", data)
