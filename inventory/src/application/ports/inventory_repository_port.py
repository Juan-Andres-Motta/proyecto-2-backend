"""Inventory repository port (interface)."""
from abc import ABC, abstractmethod
from typing import List, Optional, Tuple
from uuid import UUID

from src.domain.entities.inventory import Inventory


class InventoryRepositoryPort(ABC):
    """Port for inventory repository operations."""

    @abstractmethod
    async def create(self, inventory_data: dict) -> Inventory:
        ...  # pragma: no cover

    @abstractmethod
    async def find_by_id(self, inventory_id: UUID) -> Optional[Inventory]:
        ...  # pragma: no cover

    @abstractmethod
    async def list_inventories(
        self,
        limit: int = 10,
        offset: int = 0,
        product_id: Optional[UUID] = None,
        warehouse_id: Optional[UUID] = None,
        sku: Optional[str] = None,
    ) -> Tuple[List[Inventory], int]:
        ...  # pragma: no cover
