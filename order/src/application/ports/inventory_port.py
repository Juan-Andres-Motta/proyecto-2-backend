"""Inventory port for simple inventory validation."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from uuid import UUID


@dataclass
class InventoryInfo:
    """
    Inventory information for a specific inventory entry.

    Contains all denormalized data needed to create an order item
    without FEFO allocation logic.
    """

    id: UUID
    warehouse_id: UUID

    # Stock information
    available_quantity: int

    # Denormalized product data
    product_name: str
    product_sku: str
    product_price: Decimal  # Base price (before 30% markup)
    product_category: str

    # Denormalized warehouse data
    warehouse_name: str
    warehouse_city: str
    warehouse_country: str

    # Batch traceability
    batch_number: str
    expiration_date: date


class InventoryPort(ABC):
    """
    Abstract port for inventory operations.

    Simple validation approach: client provides inventario_id,
    Order Service validates stock availability.
    """

    @abstractmethod
    async def get_inventory(self, inventory_id: UUID) -> InventoryInfo:
        """
        Get inventory information by ID.

        Args:
            inventory_id: The inventory UUID

        Returns:
            InventoryInfo with available_quantity and denormalized data

        Raises:
            InventoryNotFoundError: If inventory ID does not exist
            ServiceConnectionError: If unable to reach Inventory Service
        """
        pass

    @abstractmethod
    async def reserve_inventory(self, inventory_id: UUID, quantity: int) -> dict:
        """
        Reserve inventory units.

        Args:
            inventory_id: ID of inventory to reserve
            quantity: Amount to reserve

        Returns:
            Updated inventory data

        Raises:
            InsufficientInventoryError: Not enough stock
            InventoryNotFoundError: Inventory doesn't exist
        """
        ...  # pragma: no cover
