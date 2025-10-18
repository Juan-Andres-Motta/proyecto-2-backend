import logging

from src.application.ports.warehouse_repository_port import WarehouseRepositoryPort
from src.domain.entities.warehouse import Warehouse

logger = logging.getLogger(__name__)


class CreateWarehouseUseCase:
    """Use case for creating a warehouse.

    No additional business validation needed.
    """

    def __init__(self, repository: WarehouseRepositoryPort):
        self.repository = repository

    async def execute(self, warehouse_data: dict) -> Warehouse:
        """Create a new warehouse."""
        logger.info(f"Creating warehouse: name={warehouse_data.get('name')}, city={warehouse_data.get('city')}")
        logger.debug(f"Warehouse data: {warehouse_data}")

        warehouse = await self.repository.create(warehouse_data)

        logger.info(f"Warehouse created successfully: id={warehouse.id}, name={warehouse.name}")
        return warehouse
