import logging
from typing import List, Tuple

from src.application.ports.warehouse_repository_port import WarehouseRepositoryPort
from src.domain.entities.warehouse import Warehouse

logger = logging.getLogger(__name__)


class ListWarehousesUseCase:
    """Use case for listing warehouses with pagination."""

    def __init__(self, repository: WarehouseRepositoryPort):
        self.repository = repository

    async def execute(
        self, limit: int = 10, offset: int = 0
    ) -> Tuple[List[Warehouse], int]:
        """List warehouses with pagination."""
        logger.info(f"Listing warehouses: limit={limit}, offset={offset}")
        logger.debug(f"Fetching warehouses with pagination parameters")

        warehouses, total = await self.repository.list_warehouses(limit=limit, offset=offset)

        logger.info(f"Warehouses retrieved successfully: count={len(warehouses)}, total={total}")
        logger.debug(f"Retrieved warehouse IDs: {[str(w.id) for w in warehouses]}")
        return warehouses, total
