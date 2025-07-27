"""
Basic server integration tests.
"""

import pytest
from unittest.mock import Mock


class TestMCPToolRegistry:
    """Test MCPToolRegistry class."""

    def test_init(self):
        """Test registry initialization."""
        from ticktick_mcp.server_oop import MCPToolRegistry
        
        registry = MCPToolRegistry()
        assert registry.tools == {}

    def test_register_tool(self):
        """Test tool registration."""
        from ticktick_mcp.server_oop import MCPToolRegistry
        
        registry = MCPToolRegistry()
        mock_tool = Mock()
        
        registry.register_tool("test_tool", mock_tool)
        
        assert registry.tools["test_tool"] == mock_tool

    def test_get_tool_exists(self):
        """Test getting existing tool."""
        from ticktick_mcp.server_oop import MCPToolRegistry
        
        registry = MCPToolRegistry()
        mock_tool = Mock()
        registry.register_tool("test_tool", mock_tool)
        
        result = registry.get_tool("test_tool")
        
        assert result == mock_tool

    def test_get_tool_not_exists(self):
        """Test getting non-existent tool."""
        from ticktick_mcp.server_oop import MCPToolRegistry
        
        registry = MCPToolRegistry()
        
        result = registry.get_tool("nonexistent")
        
        assert result is None

    def test_list_tools(self):
        """Test listing all tools."""
        from ticktick_mcp.server_oop import MCPToolRegistry
        
        registry = MCPToolRegistry()
        registry.register_tool("tool1", Mock())
        registry.register_tool("tool2", Mock())
        
        tools = registry.list_tools()
        
        assert set(tools) == {"tool1", "tool2"}


@pytest.mark.integration
class TestTickTickMCPServerBasic:
    """Basic TickTick MCP server tests."""

    def test_server_creation(self):
        """Test server can be created."""
        from ticktick_mcp.server_oop import TickTickMCPServer
        
        mock_config_manager = Mock()
        server = TickTickMCPServer(mock_config_manager)
        
        assert server.config_manager == mock_config_manager
        assert server.api_client is None
        assert server.task_service is None
        assert server.project_service is None
        assert not server._initialized

    def test_server_info_not_initialized(self):
        """Test getting server info when not initialized."""
        from ticktick_mcp.server_oop import TickTickMCPServer
        
        mock_config_manager = Mock()
        server = TickTickMCPServer(mock_config_manager)
        
        info = server.get_server_info()
        
        assert info["initialized"] is False
        assert info["tools_count"] == 0