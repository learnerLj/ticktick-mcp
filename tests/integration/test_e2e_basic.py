"""
Basic end-to-end workflow tests.
"""

import pytest
from unittest.mock import Mock, patch


@pytest.mark.integration
class TestBasicWorkflow:
    """Test basic end-to-end workflows."""

    @patch('ticktick_mcp.server_oop.TickTickAPIClient')
    @patch('ticktick_mcp.server_oop.TaskService')
    @patch('ticktick_mcp.server_oop.ProjectService')
    def test_server_initialization_workflow(self, mock_project_service, mock_task_service, mock_api_client):
        """Test complete server initialization workflow."""
        from ticktick_mcp.server_oop import TickTickMCPServer
        
        # Mock config manager
        mock_config_manager = Mock()
        mock_config_manager.is_authenticated.return_value = True
        
        # Mock services
        mock_api_client_instance = Mock()
        mock_api_client.return_value = mock_api_client_instance
        
        mock_task_service_instance = Mock()
        mock_task_service.return_value = mock_task_service_instance
        
        mock_project_service_instance = Mock()
        mock_project_service_instance.get_all_projects.return_value = [Mock(), Mock()]
        mock_project_service.return_value = mock_project_service_instance
        
        # Test server creation and initialization
        server = TickTickMCPServer(mock_config_manager)
        
        with patch.object(server, '_register_tools'):
            result = server.initialize()
        
        assert result is True
        assert server._initialized is True
        assert server.api_client == mock_api_client_instance
        assert server.task_service == mock_task_service_instance
        assert server.project_service == mock_project_service_instance

    def test_server_initialization_not_authenticated(self):
        """Test server initialization when not authenticated."""
        from ticktick_mcp.server_oop import TickTickMCPServer
        
        mock_config_manager = Mock()
        mock_config_manager.is_authenticated.return_value = False
        
        server = TickTickMCPServer(mock_config_manager)
        result = server.initialize()
        
        assert result is False
        assert not server._initialized

    def test_config_and_client_workflow(self):
        """Test configuration and client creation workflow."""
        from ticktick_mcp.config import TickTickConfig
        from ticktick_mcp.client import TickTickAPIClient, TaskService, ProjectService
        
        # Create config
        config = TickTickConfig(
            client_id="test_id",
            client_secret="test_secret",
            access_token="test_token"
        )
        
        # Mock config manager
        mock_config_manager = Mock()
        mock_config_manager.load_config.return_value = config
        
        # Test client creation
        with patch('ticktick_mcp.client.ConfigManager', return_value=mock_config_manager):
            api_client = TickTickAPIClient()
            task_service = TaskService(api_client)
            project_service = ProjectService(api_client)
        
        assert api_client.config == config
        assert task_service.api_client == api_client
        assert project_service.api_client == api_client

    def test_tool_registry_workflow(self):
        """Test tool registry workflow."""
        from ticktick_mcp.server_oop import MCPToolRegistry
        
        registry = MCPToolRegistry()
        
        # Create mock tools
        tool1 = Mock()
        tool1.description = "Tool 1"
        tool2 = Mock()
        tool2.description = "Tool 2"
        
        # Register tools
        registry.register_tool("tool1", tool1)
        registry.register_tool("tool2", tool2)
        
        # Test retrieval
        assert registry.get_tool("tool1") == tool1
        assert registry.get_tool("tool2") == tool2
        assert registry.get_tool("nonexistent") is None
        
        # Test listing
        tools = registry.list_tools()
        assert set(tools) == {"tool1", "tool2"}