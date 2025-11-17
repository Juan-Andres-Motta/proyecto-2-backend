"""
Port interface for Inventory microservice operations (common/shared).

This defines the contract for inventory read operations accessible to all users.
"""

from abc import ABC, abstractmethod

from common.schemas import PaginatedInventoriesResponse


class InventoryPort(ABC):
    """
    Abstract port interface for common inventory operations.

    Implementations of this port handle communication with the inventory
    microservice for shared read-only inventory queries.
    """

    @abstractmethod
    async def get_inventories(
        self,
        limit: int = 10,
        offset: int = 0,
        name: str | None = None,
        sku: str | None = None,
        category: str | None = None,
    ) -> PaginatedInventoriesResponse:
        """
        Retrieve a paginated list of inventories with optional filters.

        Args:
            limit: Maximum number of inventories to return
            offset: Number of inventories to skip
            name: Optional product name filter
            sku: Optional product SKU filter
            category: Optional category filter

        Returns:
            PaginatedInventoriesResponse with validated inventory data

        Raises:
            MicroserviceConnectionError: If unable to connect to the inventory service
            MicroserviceHTTPError: If the inventory service returns an error
        """
        pass
