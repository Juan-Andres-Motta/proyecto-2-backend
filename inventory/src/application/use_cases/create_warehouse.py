from src.adapters.output.repositories.warehouse_repository import WarehouseRepository
from src.infrastructure.database.models import Warehouse


class CreateWarehouseUseCase:
    def __init__(self, repository: WarehouseRepository):
        self.repository = repository

    async def execute(self, warehouse_data: dict) -> Warehouse:
        return await self.repository.create(warehouse_data)
