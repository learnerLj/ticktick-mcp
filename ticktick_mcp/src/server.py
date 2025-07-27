"""Main server module - compatibility layer for new OOP design."""

# Import the new OOP server implementation
from ..server_oop import main

# Re-export main function for backward compatibility
__all__ = ["main"]