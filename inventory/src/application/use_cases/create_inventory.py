from src.adapters.output.repositories.inventory_repository import InventoryRepository
from src.infrastructure.database.models import Inventory


class CreateInventoryUseCase:
    def __init__(self, repository: InventoryRepository):
        self.repository = repository

    async def execute(self, inventory_data: dict) -> Inventory:
        return await self.repository.create(inventory_data)
