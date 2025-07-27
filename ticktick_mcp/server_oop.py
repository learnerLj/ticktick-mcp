"""Modern object-oriented MCP server for TickTick integration."""

from typing import Optional, Dict, Any, List
from mcp.server.fastmcp import FastMCP

from .client import TickTickAPIClient, TaskService, ProjectService
from .config import ConfigManager
from .exceptions import TickTickMCPError, AuthenticationError, ConfigurationError
from .logging_config import LoggerManager
from .tools import (
    # Project tools
    GetProjectsTool,
    GetProjectTool,
    CreateProjectTool,
    DeleteProjectTool,
    # Task tools
    GetAllTasksTool,
    GetTaskByIdTool,
    CreateTaskTool,
    CompleteTaskTool,
    DeleteTaskTool,
    BatchCompleteTasksTool,
    BatchDeleteTasksTool,
)


class MCPToolRegistry:
    """Registry for managing MCP tools."""

    def __init__(self):
        """Initialize tool registry."""
        self.tools: Dict[str, Any] = {}

    def register_tool(self, name: str, tool: Any) -> None:
        """Register a tool.
        
        Args:
            name: Tool name
            tool: Tool instance
        """
        self.tools[name] = tool

    def get_tool(self, name: str) -> Optional[Any]:
        """Get a tool by name.
        
        Args:
            name: Tool name
            
        Returns:
            Tool instance or None
        """
        return self.tools.get(name)

    def list_tools(self) -> List[str]:
        """List all registered tool names.
        
        Returns:
            List of tool names
        """
        return list(self.tools.keys())


class TickTickMCPServer:
    """Modern object-oriented TickTick MCP server."""

    def __init__(self, config_manager: Optional[ConfigManager] = None):
        """Initialize TickTick MCP server.
        
        Args:
            config_manager: Optional configuration manager
        """
        # Initialize components
        self.config_manager = config_manager or ConfigManager()
        self.logger_manager = LoggerManager()
        self.logger = self.logger_manager.setup_logging()
        
        # Initialize services
        self.api_client: Optional[TickTickAPIClient] = None
        self.task_service: Optional[TaskService] = None
        self.project_service: Optional[ProjectService] = None
        
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
                    "No access token found. Please run 'uv run -m ticktick_mcp.cli auth' to authenticate."
                )
                return False

            # Initialize API client and services
            self.api_client = TickTickAPIClient(self.config_manager)
            self.task_service = TaskService(self.api_client)
            self.project_service = ProjectService(self.api_client)

            # Test API connectivity
            projects = self.project_service.get_all_projects()
            self.logger.info(f"Successfully connected to TickTick API with {len(projects)} projects")

            # Register tools
            self._register_tools()

            self._initialized = True
            return True

        except ConfigurationError as e:
            self.logger.error(f"Configuration error: {e.message}")
            return False
        except AuthenticationError as e:
            self.logger.error(f"Authentication error: {e.message}")
            self.logger.error("Your access token may have expired. Please run 'uv run -m ticktick_mcp.cli auth' to refresh it.")
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
            ("complete_task", CompleteTaskTool(self.task_service)),
            ("delete_task", DeleteTaskTool(self.task_service)),
            ("batch_complete_tasks", BatchCompleteTasksTool(self.task_service)),
            ("batch_delete_tasks", BatchDeleteTasksTool(self.task_service)),
        ]

        # Register all tools
        all_tools = project_tools + task_tools
        
        for tool_name, tool_instance in all_tools:
            self.tool_registry.register_tool(tool_name, tool_instance)
            
            # Register with FastMCP
            @self.mcp.tool(name=tool_name, description=tool_instance.description)
            async def mcp_tool_wrapper(**kwargs):
                return await tool_instance.execute(**kwargs)

        self.logger.info(f"Registered {len(all_tools)} MCP tools")

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

    def get_server_info(self) -> Dict[str, Any]:
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


def create_server(config_manager: Optional[ConfigManager] = None) -> TickTickMCPServer:
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