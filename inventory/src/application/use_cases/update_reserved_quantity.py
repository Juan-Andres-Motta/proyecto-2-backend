"""Use case for updating inventory reserved quantity."""

import logging
from uuid import UUID

from src.application.ports.inventory_repository_port import InventoryRepositoryPort
from src.domain.entities.inventory import Inventory

logger = logging.getLogger(__name__)


class UpdateReservedQuantityUseCase:
    """Use case for updating reserved quantity on inventory."""

    def __init__(self, repository: InventoryRepositoryPort):
        self.repository = repository

    async def execute(self, inventory_id: UUID, quantity_delta: int) -> Inventory:
        """
        Update reserved quantity by delta.

        Args:
            inventory_id: ID of inventory to update
            quantity_delta: Amount to change reservation by (positive = reserve, negative = release)

        Returns:
            Updated inventory domain entity
        """
        logger.info(
            f"UC: Updating reserved quantity: inventory_id={inventory_id}, quantity_delta={quantity_delta}"
        )

        inventory = await self.repository.update_reserved_quantity(
            inventory_id, quantity_delta
        )

        logger.info(
            f"UC: Successfully updated: new_reserved={inventory.reserved_quantity}, available={inventory.available_quantity()}"
        )

        return inventory
