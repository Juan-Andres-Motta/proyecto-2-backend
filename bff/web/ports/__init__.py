"""
Port interfaces for hexagonal architecture.

Ports define the contracts for external service communication without
specifying implementation details.
"""

from .catalog_port import CatalogPort
from .delivery_port import DeliveryPort
from .inventory_port import InventoryPort
from .seller_port import SellerPort

__all__ = [
    "CatalogPort",
    "DeliveryPort",
    "InventoryPort",
    "SellerPort",
]
