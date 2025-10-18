"""
Inventory adapter implementation.

This adapter implements the InventoryPort interface using HTTP communication.
"""

from typing import Optional
from uuid import UUID

from ..ports.inventory_port import InventoryPort
from ..schemas.inventory_schemas import (
    InventoryCreate,
    InventoryCreateResponse,
    PaginatedInventoriesResponse,
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

    async def create_inventory(
        self, inventory_data: InventoryCreate
    ) -> InventoryCreateResponse:
        """Create a new inventory entry."""
        response_data = await self.client.post(
            "/inventory/inventory",
            json=inventory_data.model_dump(mode="json"),
        )
        return InventoryCreateResponse(**response_data)

    async def get_inventories(
        self,
        limit: int = 10,
        offset: int = 0,
        sku: Optional[str] = None,
        warehouse_id: Optional[UUID] = None,
    ) -> PaginatedInventoriesResponse:
        """Retrieve a paginated list of inventories with optional filters."""
        params = {"limit": limit, "offset": offset}
        if sku:
            params["sku"] = sku
        if warehouse_id:
            params["warehouse_id"] = str(warehouse_id)

        response_data = await self.client.get(
            "/inventory/inventories",
            params=params,
        )
        return PaginatedInventoriesResponse(**response_data)
