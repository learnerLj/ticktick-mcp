"""Logging configuration for TickTick MCP server."""

import logging
import sys


class LoggerManager:
    """Manages logging configuration for the application."""

    def __init__(self, name: str = "ticktick_mcp"):
        """Initialize logger manager.

        Args:
            name: Logger name
        """
        self.name = name
        self._logger: logging.Logger | None = None

    def setup_logging(
        self,
        level: int = logging.INFO,
        format_string: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        include_console: bool = True,
        log_file: str | None = None,
    ) -> logging.Logger:
        """Setup logging configuration.

        Args:
            level: Logging level
            format_string: Log message format
            include_console: Whether to include console handler
            log_file: Optional log file path

        Returns:
            Configured logger instance
        """
        if self._logger is None:
            # Create logger
            self._logger = logging.getLogger(self.name)
            self._logger.setLevel(level)

            # Clear any existing handlers
            self._logger.handlers.clear()

            # Create formatter
            formatter = logging.Formatter(format_string)

            # Add console handler (use stderr for MCP compatibility)
            if include_console:
                console_handler = logging.StreamHandler(sys.stderr)
                console_handler.setLevel(level)
                console_handler.setFormatter(formatter)
                self._logger.addHandler(console_handler)

            # Add file handler if specified
            if log_file:
                file_handler = logging.FileHandler(log_file)
                file_handler.setLevel(level)
                file_handler.setFormatter(formatter)
                self._logger.addHandler(file_handler)

            # Prevent propagation to root logger
            self._logger.propagate = False

        return self._logger

    def get_logger(self, name: str | None = None) -> logging.Logger:
        """Get logger instance.

        Args:
            name: Optional logger name, uses default if None

        Returns:
            Logger instance
        """
        if name:
            return logging.getLogger(f"{self.name}.{name}")

        if self._logger is None:
            return self.setup_logging()

        return self._logger

    def set_level(self, level: int) -> None:
        """Set logging level.

        Args:
            level: New logging level
        """
        if self._logger:
            self._logger.setLevel(level)
            for handler in self._logger.handlers:
                handler.setLevel(level)
