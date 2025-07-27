"""
Basic configuration tests.
"""

import pytest
from ticktick_mcp.config import TickTickConfig
from ticktick_mcp.exceptions import ConfigurationError


class TestTickTickConfig:
    """Test TickTickConfig dataclass."""

    def test_config_creation(self):
        """Test creating a valid configuration."""
        config = TickTickConfig(
            client_id="test_id",
            client_secret="test_secret"
        )
        
        assert config.client_id == "test_id"
        assert config.client_secret == "test_secret"
        assert config.base_url == "https://api.ticktick.com/open/v1"
        assert config.use_dida365 is False

    def test_config_dida365_mode(self):
        """Test configuration in Dida365 mode."""
        config = TickTickConfig(
            client_id="test_id",
            client_secret="test_secret",
            use_dida365=True
        )
        
        assert config.use_dida365 is True
        assert config.base_url == "https://api.dida365.com/open/v1"
        assert config.auth_url == "https://dida365.com/oauth/authorize"

    def test_config_missing_client_id(self):
        """Test configuration validation with missing client_id."""
        with pytest.raises(ConfigurationError, match="TICKTICK_CLIENT_ID is required"):
            TickTickConfig(
                client_id="",
                client_secret="test_secret"
            )

    def test_config_missing_client_secret(self):
        """Test configuration validation with missing client_secret."""
        with pytest.raises(ConfigurationError, match="TICKTICK_CLIENT_SECRET is required"):
            TickTickConfig(
                client_id="test_id",
                client_secret=""
            )


class TestConfigManager:
    """Test ConfigManager basic functionality."""

    def test_config_manager_creation(self):
        """Test that ConfigManager can be created."""
        from ticktick_mcp.config import ConfigManager
        
        manager = ConfigManager()
        assert manager is not None

    def test_config_manager_with_env_file(self):
        """Test ConfigManager with custom env file."""
        from ticktick_mcp.config import ConfigManager
        
        manager = ConfigManager(env_file="/custom/path/.env")
        assert manager is not None