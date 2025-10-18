"""
Adapter implementations for hexagonal architecture.

Adapters implement the port interfaces and handle the actual communication
with external services.
"""

from .catalog_adapter import CatalogAdapter
from .inventory_adapter import InventoryAdapter
from .seller_adapter import SellerAdapter

__all__ = [
    "CatalogAdapter",
    "SellerAdapter",
    "InventoryAdapter",
]
