"""
Inventory adapter implementation.

This adapter implements the InventoryPort interface using HTTP communication.
"""

import logging
from typing import Optional
from uuid import UUID

from common.http_client import HttpClient

from ..ports.inventory_port import InventoryPort
from ..schemas.inventory_schemas import (
    InventoryCreate,
    InventoryCreateResponse,
    PaginatedInventoriesResponse,
    PaginatedWarehousesResponse,
    WarehouseCreate,
    WarehouseCreateResponse,
)

logger = logging.getLogger(__name__)


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
        logger.info(f"Creating warehouse: name='{warehouse_data.name}'")
        response_data = await self.client.post(
            "/warehouse",
            json=warehouse_data.model_dump(mode="json"),
        )
        return WarehouseCreateResponse(**response_data)

    async def get_warehouses(
        self, limit: int = 10, offset: int = 0
    ) -> PaginatedWarehousesResponse:
        """Retrieve a paginated list of warehouses."""
        logger.info(f"Getting warehouses: limit={limit}, offset={offset}")
        response_data = await self.client.get(
            "/warehouses",
            params={"limit": limit, "offset": offset},
        )
        return PaginatedWarehousesResponse(**response_data)

    async def create_inventory(
        self, inventory_data: InventoryCreate
    ) -> InventoryCreateResponse:
        """Create a new inventory entry."""
        logger.info(f"Creating inventory: product_id={inventory_data.product_id}, warehouse_id={inventory_data.warehouse_id}, sku='{inventory_data.product_sku}'")
        response_data = await self.client.post(
            "/inventory",
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
        logger.info(f"Getting inventories: limit={limit}, offset={offset}, sku={sku}, warehouse_id={warehouse_id}")
        params = {"limit": limit, "offset": offset}
        if sku:
            params["sku"] = sku
        if warehouse_id:
            params["warehouse_id"] = str(warehouse_id)

        response_data = await self.client.get(
            "/inventories",
            params=params,
        )
        return PaginatedInventoriesResponse(**response_data)
