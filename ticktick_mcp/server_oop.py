"""Modern object-oriented MCP server for TickTick integration."""

from typing import Any

from mcp.server.fastmcp import FastMCP

from .client import ProjectService, TaskService, TickTickAPIClient
from .config import ConfigManager
from .exceptions import AuthenticationError, ConfigurationError
from .logging_config import LoggerManager
from .tools import (
    BatchCompleteTasksTool,
    BatchDeleteTasksTool,
    CreateProjectTool,
    CreateTaskTool,
    DeleteProjectTool,
    GetAllTasksTool,
    GetProjectsTool,
    GetProjectTool,
    GetTaskByIdTool,
    UpdateTaskTool,
)


class MCPToolRegistry:
    """Registry for managing MCP tools."""

    def __init__(self):
        """Initialize tool registry."""
        self.tools: dict[str, Any] = {}

    def register_tool(self, name: str, tool: Any) -> None:
        """Register a tool.

        Args:
            name: Tool name
            tool: Tool instance
        """
        self.tools[name] = tool

    def get_tool(self, name: str) -> Any | None:
        """Get a tool by name.

        Args:
            name: Tool name

        Returns:
            Tool instance or None
        """
        return self.tools.get(name)

    def list_tools(self) -> list[str]:
        """List all registered tool names.

        Returns:
            List of tool names
        """
        return list(self.tools.keys())


class TickTickMCPServer:
    """Modern object-oriented TickTick MCP server."""

    def __init__(self, config_manager: ConfigManager | None = None):
        """Initialize TickTick MCP server.

        Args:
            config_manager: Optional configuration manager
        """
        # Initialize components
        self.config_manager = config_manager or ConfigManager()
        self.logger_manager = LoggerManager()
        self.logger = self.logger_manager.setup_logging()

        # Initialize services
        self.api_client: TickTickAPIClient | None = None
        self.task_service: TaskService | None = None
        self.project_service: ProjectService | None = None

        # Initialize MCP server and tool registry
        self.mcp = FastMCP("ticktick")
        self.tool_registry = MCPToolRegistry()

        # Track initialization state
        self._initialized = False

    def initialize(self) -> bool:
        """Initialize the server and all services.

        Returns:
            True if initialization successful, False otherwise
        """
        if self._initialized:
            return True

        try:
            # Check authentication
            if not self.config_manager.is_authenticated():
                self.logger.error(
                    "No access token found. Please run 'ticktick-mcp auth' to authenticate."
                )
                return False

            # Initialize API client and services
            self.api_client = TickTickAPIClient(self.config_manager)
            self.task_service = TaskService(self.api_client)
            self.project_service = ProjectService(self.api_client)

            # Test API connectivity
            projects = self.project_service.get_all_projects()
            self.logger.info(
                f"Successfully connected to TickTick API with {len(projects)} projects"
            )

            # Register tools
            self._register_tools()

            self._initialized = True
            return True

        except ConfigurationError as e:
            self.logger.error(f"Configuration error: {e.message}")
            return False
        except AuthenticationError as e:
            self.logger.error(f"Authentication error: {e.message}")
            self.logger.error(
                "Your access token may have expired. Please run 'ticktick-mcp auth' to refresh it."
            )
            return False
        except Exception as e:
            self.logger.error(f"Failed to initialize server: {e}")
            return False

    def _register_tools(self) -> None:
        """Register all MCP tools."""
        if not self.task_service or not self.project_service:
            raise RuntimeError("Services not initialized")

        # Project tools
        project_tools = [
            ("get_projects", GetProjectsTool(self.project_service)),
            ("get_project", GetProjectTool(self.project_service)),
            ("create_project", CreateProjectTool(self.project_service)),
            ("delete_project", DeleteProjectTool(self.project_service)),
        ]

        # Task tools
        task_tools = [
            ("get_all_tasks", GetAllTasksTool(self.task_service)),
            ("get_task_by_id", GetTaskByIdTool(self.task_service)),
            ("create_task", CreateTaskTool(self.task_service)),
            ("update_task", UpdateTaskTool(self.task_service)),
            ("batch_complete_tasks", BatchCompleteTasksTool(self.task_service)),
            ("batch_delete_tasks", BatchDeleteTasksTool(self.task_service)),
        ]

        # Register all tools
        all_tools = project_tools + task_tools

        for tool_name, tool_instance in all_tools:
            self.tool_registry.register_tool(tool_name, tool_instance)

        # Register with FastMCP using direct function approach
        self._register_mcp_tools()

    def _register_mcp_tools(self) -> None:
        """Register tools with FastMCP using direct function approach."""

        # Project tools - register each one individually with proper signatures
        @self.mcp.tool(
            name="get_projects", description="Get all projects from TickTick"
        )
        async def get_projects():
            tool = self.tool_registry.get_tool("get_projects")
            return await tool.execute()

        @self.mcp.tool()
        async def get_project(project_id: str) -> str:
            """Get details about a specific project.
            
            Args:
                project_id: ID of the project to retrieve
            """
            tool = self.tool_registry.get_tool("get_project")
            return await tool.execute(project_id=project_id)

        @self.mcp.tool(
            name="create_project", description="Create a new project in TickTick"
        )
        async def create_project(
            name: str, color: str = "#F18181", view_mode: str = "list"
        ):
            tool = self.tool_registry.get_tool("create_project")
            return await tool.execute(name=name, color=color, view_mode=view_mode)

        @self.mcp.tool()
        async def delete_project(project_id: str) -> str:
            """Delete a project.
            
            Args:
                project_id: ID of the project to delete
            """
            tool = self.tool_registry.get_tool("delete_project")
            return await tool.execute(project_id=project_id)

        # Task tools
        @self.mcp.tool(
            name="get_all_tasks",
            description="Get all tasks from TickTick across all projects with optional filters",
        )
        async def get_all_tasks(
            status: str = None,
            limit: int = None,
            query: str = None,
            priority: int = None,
            project_id: str = None,
        ):
            tool = self.tool_registry.get_tool("get_all_tasks")
            return await tool.execute(
                status=status,
                limit=limit,
                query=query,
                priority=priority,
                project_id=project_id,
            )

        @self.mcp.tool(
            name="get_task_by_id",
            description="Get a task by its ID without requiring project ID",
        )
        async def get_task_by_id(task_id: str):
            tool = self.tool_registry.get_tool("get_task_by_id")
            return await tool.execute(task_id=task_id)

        @self.mcp.tool(name="create_task", description="Create a new task in TickTick")
        async def create_task(
            title: str,
            project_id: str,
            content: str = None,
            start_date: str = None,
            due_date: str = None,
            priority: int = 0,
        ):
            tool = self.tool_registry.get_tool("create_task")
            return await tool.execute(
                title=title,
                project_id=project_id,
                content=content,
                start_date=start_date,
                due_date=due_date,
                priority=priority,
            )

        @self.mcp.tool(
            name="update_task", description="Update an existing task's properties"
        )
        async def update_task(
            task_id: str,
            title: str = None,
            content: str = None,
            start_date: str = None,
            due_date: str = None,
            priority: int = None,
            project_id: str = None,
        ):
            tool = self.tool_registry.get_tool("update_task")
            return await tool.execute(
                task_id=task_id,
                title=title,
                content=content,
                start_date=start_date,
                due_date=due_date,
                priority=priority,
                project_id=project_id,
            )

        @self.mcp.tool(
            name="batch_complete_tasks",
            description="Complete one or multiple tasks by providing comma-separated task IDs",
        )
        async def batch_complete_tasks(task_ids: str):
            tool = self.tool_registry.get_tool("batch_complete_tasks")
            return await tool.execute(task_ids=task_ids)

        @self.mcp.tool(
            name="batch_delete_tasks",
            description="Delete one or multiple tasks by providing comma-separated task IDs",
        )
        async def batch_delete_tasks(task_ids: str):
            tool = self.tool_registry.get_tool("batch_delete_tasks")
            return await tool.execute(task_ids=task_ids)

        self.logger.info(f"Registered 10 MCP tools")

    def run(self, transport: str = "stdio") -> None:
        """Run the MCP server.

        Args:
            transport: Transport type (only stdio supported)
        """
        if not self._initialized:
            if not self.initialize():
                self.logger.error("Failed to initialize server")
                return

        self.logger.info("Starting TickTick MCP server")
        try:
            self.mcp.run(transport=transport)
        except KeyboardInterrupt:
            self.logger.info("Server stopped by user")
        except Exception as e:
            self.logger.error(f"Server error: {e}")
            raise

    def get_server_info(self) -> dict[str, Any]:
        """Get server information.

        Returns:
            Server information dictionary
        """
        return {
            "name": "TickTick MCP Server",
            "version": "2.0.0",
            "initialized": self._initialized,
            "tools_count": len(self.tool_registry.list_tools()),
            "tools": self.tool_registry.list_tools(),
        }


def create_server(config_manager: ConfigManager | None = None) -> TickTickMCPServer:
    """Factory function to create a TickTick MCP server.

    Args:
        config_manager: Optional configuration manager

    Returns:
        TickTickMCPServer instance
    """
    return TickTickMCPServer(config_manager)


def main() -> None:
    """Main entry point for the MCP server."""
    server = create_server()

    if not server.initialize():
        server.logger.error("Failed to initialize TickTick MCP server")
        return

    server.run()


if __name__ == "__main__":
    main()
