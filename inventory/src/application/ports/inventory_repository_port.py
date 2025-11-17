"""Inventory repository port (interface)."""

from abc import ABC, abstractmethod
from typing import List, Optional, Tuple
from uuid import UUID

from src.domain.entities.inventory import Inventory


class InventoryRepositoryPort(ABC):
    """Port for inventory repository operations."""

    @abstractmethod
    async def create(self, inventory_data: dict) -> Inventory: ...  # pragma: no cover

    @abstractmethod
    async def find_by_id(
        self, inventory_id: UUID
    ) -> Optional[Inventory]: ...  # pragma: no cover

    @abstractmethod
    async def list_inventories(
        self,
        limit: int = 10,
        offset: int = 0,
        product_id: Optional[UUID] = None,
        warehouse_id: Optional[UUID] = None,
        sku: Optional[str] = None,
        category: Optional[str] = None,
        name: Optional[str] = None,
    ) -> Tuple[List[Inventory], int]: ...  # pragma: no cover

    @abstractmethod
    async def update_reserved_quantity(
        self, inventory_id: UUID, quantity_delta: int
    ) -> Inventory:
        """
        Update reserved quantity atomically with row-level locking.

        Args:
            inventory_id: ID of inventory to update
            quantity_delta: Amount to change reserved_quantity by

        Returns:
            Updated inventory domain entity

        Raises:
            InventoryNotFoundException: If inventory doesn't exist
            InsufficientInventoryException: If insufficient available quantity
            InvalidReservationReleaseException: If trying to release more than reserved
        """
        ...  # pragma: no cover
