"""
Mock configuration objects for testing.
"""

from ticktick_mcp.config import TickTickConfig


def create_mock_config():
    """Create a mock TickTick configuration for testing."""
    return TickTickConfig(
        client_id="test_client_id",
        client_secret="test_client_secret",
        access_token="test_access_token",
        refresh_token="test_refresh_token",
        api_base_url="https://ticktick.com/api/v2",
        oauth_base_url="https://ticktick.com/oauth",
    )


def create_dida_config():
    """Create a mock Dida365 configuration for testing."""
    return TickTickConfig(
        client_id="dida_client_id",
        client_secret="dida_client_secret",
        access_token="dida_access_token",
        refresh_token="dida_refresh_token",
        api_base_url="https://dida365.com/api/v2",
        oauth_base_url="https://dida365.com/oauth",
    )


def create_config_without_tokens():
    """Create a configuration without tokens (for authentication testing)."""
    return TickTickConfig(
        client_id="test_client_id",
        client_secret="test_client_secret",
        access_token=None,
        refresh_token=None,
        api_base_url="https://ticktick.com/api/v2",
        oauth_base_url="https://ticktick.com/oauth",
    )
