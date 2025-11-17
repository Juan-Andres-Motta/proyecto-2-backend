"""
Inventory adapter implementation for common/shared functionality.

This adapter implements the common InventoryPort interface using HTTP communication.
"""

import logging

from common.http_client import HttpClient
from common.schemas import PaginatedInventoriesResponse

from ..ports.inventory_port import InventoryPort

logger = logging.getLogger(__name__)


class InventoryAdapter(InventoryPort):
    """
    HTTP adapter for inventory microservice operations (common/shared).

    This adapter implements the common InventoryPort interface and handles
    communication with the inventory microservice via HTTP for shared read operations.
    """

    def __init__(self, http_client: HttpClient):
        """
        Initialize the inventory adapter.

        Args:
            http_client: Configured HTTP client for the inventory service
        """
        self.client = http_client

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

        Fetches data from the inventory microservice and validates it against
        the PaginatedInventoriesResponse schema to ensure type safety.
        """
        logger.info(
            f"Getting inventories: limit={limit}, offset={offset}, "
            f"name={name}, sku={sku}, category={category}"
        )
        params = {"limit": limit, "offset": offset}
        if name:
            params["name"] = name
        if sku:
            params["sku"] = sku
        if category:
            params["category"] = category

        response_data = await self.client.get(
            "/inventory/inventories",
            params=params,
        )

        # Validate and parse response using Pydantic schema
        validated_response = PaginatedInventoriesResponse(**response_data)
        logger.debug(f"Successfully validated response with {len(validated_response.items)} items")

        return validated_response
