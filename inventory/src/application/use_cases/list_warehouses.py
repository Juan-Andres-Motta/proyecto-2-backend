from typing import List, Tuple

from src.application.ports.warehouse_repository_port import WarehouseRepositoryPort
from src.domain.entities.warehouse import Warehouse


class ListWarehousesUseCase:
    """Use case for listing warehouses with pagination."""

    def __init__(self, repository: WarehouseRepositoryPort):
        self.repository = repository

    async def execute(
        self, limit: int = 10, offset: int = 0
    ) -> Tuple[List[Warehouse], int]:
        """List warehouses with pagination."""
        return await self.repository.list_warehouses(limit=limit, offset=offset)
