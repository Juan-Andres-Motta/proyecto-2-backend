"""
Inventory adapter implementation.

This adapter implements the InventoryPort interface using HTTP communication.
"""

from ..ports.inventory_port import InventoryPort
from ..schemas.inventory_schemas import (
    PaginatedWarehousesResponse,
    WarehouseCreate,
    WarehouseCreateResponse,
)

from .http_client import HttpClient


class InventoryAdapter(InventoryPort):
    """
    HTTP adapter for inventory microservice operations.

    This adapter implements the InventoryPort interface and handles
    communication with the inventory microservice via HTTP.
    """

    def __init__(self, http_client: HttpClient):
        """
        Initialize the inventory adapter.

        Args:
            http_client: Configured HTTP client for the inventory service
        """
        self.client = http_client

    async def create_warehouse(
        self, warehouse_data: WarehouseCreate
    ) -> WarehouseCreateResponse:
        """Create a new warehouse."""
        response_data = await self.client.post(
            "/inventory/warehouse",
            json=warehouse_data.model_dump(mode="json"),
        )
        return WarehouseCreateResponse(**response_data)

    async def get_warehouses(
        self, limit: int = 10, offset: int = 0
    ) -> PaginatedWarehousesResponse:
        """Retrieve a paginated list of warehouses."""
        response_data = await self.client.get(
            "/inventory/warehouses",
            params={"limit": limit, "offset": offset},
        )
        return PaginatedWarehousesResponse(**response_data)
