"""Custom exceptions for TickTick MCP server."""


class TickTickMCPError(Exception):
    """Base exception for all TickTick MCP errors."""

    def __init__(self, message: str, code: str = None):
        super().__init__(message)
        self.message = message
        self.code = code


class AuthenticationError(TickTickMCPError):
    """Raised when authentication fails."""

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, "AUTH_ERROR")


class APIError(TickTickMCPError):
    """Raised when TickTick API returns an error."""

    def __init__(self, message: str, status_code: int = None):
        super().__init__(message, "API_ERROR")
        self.status_code = status_code


class ConfigurationError(TickTickMCPError):
    """Raised when configuration is invalid or missing."""

    def __init__(self, message: str = "Configuration error"):
        super().__init__(message, "CONFIG_ERROR")


class ValidationError(TickTickMCPError):
    """Raised when input validation fails."""

    def __init__(self, message: str = "Validation error"):
        super().__init__(message, "VALIDATION_ERROR")


class NetworkError(TickTickMCPError):
    """Raised when network operations fail."""

    def __init__(self, message: str = "Network error"):
        super().__init__(message, "NETWORK_ERROR")