from typing import List, Optional, Tuple
from uuid import UUID

from src.application.ports.inventory_repository_port import InventoryRepositoryPort
from src.domain.entities.inventory import Inventory


class ListInventoriesUseCase:
    """Use case for listing inventories with pagination and filters."""

    def __init__(self, repository: InventoryRepositoryPort):
        self.repository = repository

    async def execute(
        self,
        limit: int = 10,
        offset: int = 0,
        product_id: Optional[UUID] = None,
        warehouse_id: Optional[UUID] = None,
        sku: Optional[str] = None,
    ) -> Tuple[List[Inventory], int]:
        """List inventories with pagination and filters."""
        return await self.repository.list_inventories(
            limit=limit,
            offset=offset,
            product_id=product_id,
            warehouse_id=warehouse_id,
            sku=sku,
        )
