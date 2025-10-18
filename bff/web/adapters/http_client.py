"""
HTTP client abstraction - Re-export from common module.

DEPRECATED: Import HttpClient from common.http_client instead.
This module exists for backwards compatibility.
"""

# Re-export from common module
from common.http_client import HttpClient

__all__ = ["HttpClient"]
