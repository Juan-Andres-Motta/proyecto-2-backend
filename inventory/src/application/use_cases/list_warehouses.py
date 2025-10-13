from typing import List, Tuple

from src.adapters.output.repositories.warehouse_repository import WarehouseRepository
from src.infrastructure.database.models import Warehouse


class ListWarehousesUseCase:
    def __init__(self, repository: WarehouseRepository):
        self.repository = repository

    async def execute(
        self, limit: int = 10, offset: int = 0
    ) -> Tuple[List[Warehouse], int]:
        return await self.repository.list_warehouses(limit=limit, offset=offset)
