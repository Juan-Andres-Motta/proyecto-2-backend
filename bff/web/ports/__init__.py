"""
Port interfaces for hexagonal architecture.

Ports define the contracts for external service communication without
specifying implementation details.
"""

from .catalog_port import CatalogPort
from .inventory_port import InventoryPort
from .order_port import OrderPort
from .seller_port import SellerPort

__all__ = [
    "CatalogPort",
    "SellerPort",
    "InventoryPort",
    "OrderPort",
]
