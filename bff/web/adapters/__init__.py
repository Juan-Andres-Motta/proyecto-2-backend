"""
Adapter implementations for hexagonal architecture.

Adapters implement the port interfaces and handle the actual communication
with external services.
"""

from .catalog_adapter import CatalogAdapter
from .http_client import HttpClient
from .inventory_adapter import InventoryAdapter
from .seller_adapter import SellerAdapter

__all__ = [
    "HttpClient",
    "CatalogAdapter",
    "SellerAdapter",
    "InventoryAdapter",
]
