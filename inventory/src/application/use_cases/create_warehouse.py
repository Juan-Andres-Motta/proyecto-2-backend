from src.application.ports.warehouse_repository_port import WarehouseRepositoryPort
from src.domain.entities.warehouse import Warehouse


class CreateWarehouseUseCase:
    """Use case for creating a warehouse.

    No additional business validation needed.
    """

    def __init__(self, repository: WarehouseRepositoryPort):
        self.repository = repository

    async def execute(self, warehouse_data: dict) -> Warehouse:
        """Create a new warehouse."""
        return await self.repository.create(warehouse_data)
