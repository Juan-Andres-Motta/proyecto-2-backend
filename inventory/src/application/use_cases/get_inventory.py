"""Use case for retrieving a single inventory entry by ID."""
import logging
from uuid import UUID

from src.application.ports.inventory_repository_port import InventoryRepositoryPort
from src.domain.entities.inventory import Inventory
from src.domain.exceptions import InventoryNotFoundException

logger = logging.getLogger(__name__)


class GetInventoryUseCase:
    """Use case for fetching a single inventory entry by ID.

    This endpoint is used by clients to:
    1. Browse available inventory entries
    2. Select a specific inventory entry
    3. Validate inventory exists before creating an order
    """

    def __init__(self, repository: InventoryRepositoryPort):
        self.repository = repository

    async def execute(self, inventory_id: UUID) -> Inventory:
        """Get a single inventory entry by ID.

        Args:
            inventory_id: UUID of the inventory entry

        Returns:
            Inventory entity with full details including available_quantity

        Raises:
            InventoryNotFoundException: If inventory entry not found
        """
        logger.info(f"Fetching inventory: inventory_id={inventory_id}")

        # Fetch the inventory entry
        inventory = await self.repository.find_by_id(inventory_id)

        if not inventory:
            logger.warning(f"Inventory not found: inventory_id={inventory_id}")
            raise InventoryNotFoundException(inventory_id=inventory_id)

        logger.info(
            f"Found inventory: id={inventory.id}, "
            f"total={inventory.total_quantity}, "
            f"reserved={inventory.reserved_quantity}, "
            f"available={inventory.total_quantity - inventory.reserved_quantity}"
        )

        return inventory
