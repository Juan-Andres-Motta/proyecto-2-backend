"""Warehouse repository port (interface)."""
from abc import ABC, abstractmethod
from typing import List, Optional, Tuple
from uuid import UUID

from src.domain.entities.warehouse import Warehouse


class WarehouseRepositoryPort(ABC):
    """Port for warehouse repository operations."""

    @abstractmethod
    async def create(self, warehouse_data: dict) -> Warehouse:
        ...  # pragma: no cover

    @abstractmethod
    async def find_by_id(self, warehouse_id: UUID) -> Optional[Warehouse]:
        ...  # pragma: no cover

    @abstractmethod
    async def list_warehouses(
        self, limit: int = 10, offset: int = 0
    ) -> Tuple[List[Warehouse], int]:
        ...  # pragma: no cover
