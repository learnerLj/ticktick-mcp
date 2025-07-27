"""
Basic integration tests for core API functionality.
"""

from unittest.mock import Mock, patch

import pytest


@pytest.mark.integration
class TestBasicAPIIntegration:
    """Basic API integration tests."""

    def test_project_service_creation(self):
        """Test that ProjectService can be created."""
        from ticktick_mcp.client import ProjectService

        mock_client = Mock()
        service = ProjectService(mock_client)
        assert service.api_client == mock_client

    def test_task_service_creation(self):
        """Test that TaskService can be created."""
        from ticktick_mcp.client import TaskService

        mock_client = Mock()
        service = TaskService(mock_client)
        assert service.api_client == mock_client

    @patch("ticktick_mcp.client.ConfigManager")
    def test_api_client_creation(self, mock_config_manager_class):
        """Test that TickTickAPIClient can be created."""
        from ticktick_mcp.client import TickTickAPIClient

        mock_config_manager = Mock()
        mock_config = Mock()
        mock_config.access_token = "test_token"
        mock_config.base_url = "https://api.test.com"
        mock_config_manager.load_config.return_value = mock_config
        mock_config_manager_class.return_value = mock_config_manager

        client = TickTickAPIClient()
        assert client.config == mock_config

    def test_http_client_creation(self):
        """Test that HTTPClient can be created."""
        from ticktick_mcp.client import HTTPClient

        client = HTTPClient("https://api.test.com")
        assert client.base_url == "https://api.test.com"

    def test_authentication_manager_creation(self):
        """Test that AuthenticationManager can be created."""
        from ticktick_mcp.client import AuthenticationManager

        mock_config = Mock()
        mock_config_manager = Mock()
        auth_manager = AuthenticationManager(mock_config, mock_config_manager)
        assert auth_manager.config == mock_config
        assert auth_manager.config_manager == mock_config_manager
