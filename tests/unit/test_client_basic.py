"""
Basic client tests.
"""

import pytest
from unittest.mock import Mock
from ticktick_mcp.exceptions import NetworkError


class TestHTTPClient:
    """Test HTTPClient basic functionality."""

    def test_http_client_creation(self):
        """Test HTTP client creation."""
        from ticktick_mcp.client import HTTPClient
        
        client = HTTPClient("https://api.example.com")
        assert client.base_url == "https://api.example.com"

    def test_http_client_strips_trailing_slash(self):
        """Test that trailing slash is stripped."""
        from ticktick_mcp.client import HTTPClient
        
        client = HTTPClient("https://api.example.com/")
        assert client.base_url == "https://api.example.com"

    def test_http_client_with_headers(self):
        """Test HTTP client with custom headers."""
        from ticktick_mcp.client import HTTPClient
        
        headers = {"Authorization": "Bearer token"}
        client = HTTPClient("https://api.example.com", headers)
        assert client.default_headers == headers


class TestAuthenticationManager:
    """Test AuthenticationManager basic functionality."""

    def test_auth_manager_creation(self):
        """Test authentication manager creation."""
        from ticktick_mcp.client import AuthenticationManager
        
        mock_config = Mock()
        mock_config_manager = Mock()
        
        auth_manager = AuthenticationManager(mock_config, mock_config_manager)
        assert auth_manager.config == mock_config
        assert auth_manager.config_manager == mock_config_manager

    def test_refresh_token_no_refresh_token(self):
        """Test token refresh without refresh token."""
        from ticktick_mcp.client import AuthenticationManager
        
        mock_config = Mock()
        mock_config.refresh_token = None
        mock_config_manager = Mock()
        
        auth_manager = AuthenticationManager(mock_config, mock_config_manager)
        result = auth_manager.refresh_access_token()
        
        assert result is False


class TestTickTickAPIClient:
    """Test TickTickAPIClient basic functionality."""

    def test_api_client_creation_with_config_manager(self):
        """Test API client creation with custom config manager."""
        from ticktick_mcp.client import TickTickAPIClient
        from ticktick_mcp.config import TickTickConfig
        
        mock_config_manager = Mock()
        mock_config = TickTickConfig(
            client_id="test_id",
            client_secret="test_secret",
            access_token="test_token"
        )
        mock_config_manager.load_config.return_value = mock_config
        
        client = TickTickAPIClient(mock_config_manager)
        assert client.config_manager == mock_config_manager
        assert client.config == mock_config


class TestTaskService:
    """Test TaskService basic functionality."""

    def test_task_service_creation(self):
        """Test TaskService creation."""
        from ticktick_mcp.client import TaskService
        
        mock_api_client = Mock()
        service = TaskService(mock_api_client)
        assert service.api_client == mock_api_client


class TestProjectService:
    """Test ProjectService basic functionality."""

    def test_project_service_creation(self):
        """Test ProjectService creation."""
        from ticktick_mcp.client import ProjectService
        
        mock_api_client = Mock()
        service = ProjectService(mock_api_client)
        assert service.api_client == mock_api_client