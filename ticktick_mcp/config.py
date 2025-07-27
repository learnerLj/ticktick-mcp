"""Configuration management for TickTick MCP server."""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

from .exceptions import ConfigurationError


@dataclass
class TickTickConfig:
    """Configuration settings for TickTick MCP server."""

    client_id: str
    client_secret: str
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    base_url: str = "https://api.ticktick.com/open/v1"
    token_url: str = "https://ticktick.com/oauth/token"
    redirect_uri: str = "http://localhost:8080/callback"

    def __post_init__(self):
        """Validate configuration after initialization."""
        if not self.client_id:
            raise ConfigurationError("TICKTICK_CLIENT_ID is required")
        if not self.client_secret:
            raise ConfigurationError("TICKTICK_CLIENT_SECRET is required")


class ConfigManager:
    """Manages configuration loading and validation."""

    def __init__(self, env_file: Optional[str] = None):
        """Initialize configuration manager.
        
        Args:
            env_file: Path to .env file. If None, uses default in user's home directory
        """
        if env_file:
            self.env_file = Path(env_file)
        else:
            # Use user's home directory for config
            config_dir = Path.home() / ".config" / "ticktick-mcp"
            config_dir.mkdir(parents=True, exist_ok=True)
            self.env_file = config_dir / ".env"
        self._config: Optional[TickTickConfig] = None

    def load_config(self) -> TickTickConfig:
        """Load configuration from environment variables.
        
        Returns:
            TickTickConfig instance
            
        Raises:
            ConfigurationError: If required configuration is missing
        """
        if self._config is None:
            # Load environment variables
            load_dotenv(self.env_file)
            
            # Create configuration from environment
            self._config = TickTickConfig(
                client_id=os.getenv("TICKTICK_CLIENT_ID", ""),
                client_secret=os.getenv("TICKTICK_CLIENT_SECRET", ""),
                access_token=os.getenv("TICKTICK_ACCESS_TOKEN"),
                refresh_token=os.getenv("TICKTICK_REFRESH_TOKEN"),
                base_url=os.getenv("TICKTICK_BASE_URL", "https://api.ticktick.com/open/v1"),
                token_url=os.getenv("TICKTICK_TOKEN_URL", "https://ticktick.com/oauth/token"),
                redirect_uri=os.getenv("TICKTICK_REDIRECT_URI", "http://localhost:8080/callback"),
            )
        
        return self._config

    def save_tokens(self, access_token: str, refresh_token: str = None) -> None:
        """Save tokens to environment file.
        
        Args:
            access_token: OAuth2 access token
            refresh_token: Optional OAuth2 refresh token
        """
        # Update in-memory config
        if self._config:
            self._config.access_token = access_token
            if refresh_token:
                self._config.refresh_token = refresh_token

        # Load existing .env content
        env_content = {}
        if self.env_file.exists():
            with open(self.env_file) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        env_content[key] = value

        # Update tokens
        env_content["TICKTICK_ACCESS_TOKEN"] = access_token
        if refresh_token:
            env_content["TICKTICK_REFRESH_TOKEN"] = refresh_token

        # Write back to file
        with open(self.env_file, "w") as f:
            for key, value in env_content.items():
                f.write(f"{key}={value}\n")

    def is_authenticated(self) -> bool:
        """Check if user is authenticated.
        
        Returns:
            True if access token is available
        """
        try:
            config = self.load_config()
            return bool(config.access_token)
        except ConfigurationError:
            return False

    def reset_config(self) -> None:
        """Reset cached configuration."""
        self._config = None