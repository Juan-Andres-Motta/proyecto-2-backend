from typing import List, Tuple

from src.adapters.output.repositories.inventory_repository import InventoryRepository
from src.infrastructure.database.models import Inventory


class ListInventoriesUseCase:
    def __init__(self, repository: InventoryRepository):
        self.repository = repository

    async def execute(
        self, limit: int = 10, offset: int = 0
    ) -> Tuple[List[Inventory], int]:
        return await self.repository.list_inventories(limit=limit, offset=offset)
