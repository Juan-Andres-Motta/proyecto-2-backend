"""
Port interface for Inventory microservice operations.

This defines the contract for warehouse management operations
without specifying how the communication is implemented.
"""

from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID

from web.schemas.inventory_schemas import (
    InventoryCreate,
    InventoryCreateResponse,
    PaginatedInventoriesResponse,
    PaginatedWarehousesResponse,
    WarehouseCreate,
    WarehouseCreateResponse,
)


class InventoryPort(ABC):
    """
    Abstract port interface for inventory operations.

    Implementations of this port handle communication with the inventory
    microservice for warehouse management.
    """

    @abstractmethod
    async def create_warehouse(
        self, warehouse_data: WarehouseCreate
    ) -> WarehouseCreateResponse:
        """
        Create a new warehouse.

        Args:
            warehouse_data: The warehouse information to create

        Returns:
            WarehouseCreateResponse with the created warehouse ID

        Raises:
            MicroserviceValidationError: If the warehouse data is invalid
            MicroserviceConnectionError: If unable to connect to the inventory service
            MicroserviceHTTPError: If the inventory service returns an error
        """
        pass

    @abstractmethod
    async def get_warehouses(
        self, limit: int = 10, offset: int = 0
    ) -> PaginatedWarehousesResponse:
        """
        Retrieve a paginated list of warehouses.

        Args:
            limit: Maximum number of warehouses to return
            offset: Number of warehouses to skip

        Returns:
            PaginatedWarehousesResponse with warehouse data

        Raises:
            MicroserviceConnectionError: If unable to connect to the inventory service
            MicroserviceHTTPError: If the inventory service returns an error
        """
        pass

    @abstractmethod
    async def create_inventory(
        self, inventory_data: InventoryCreate
    ) -> InventoryCreateResponse:
        """
        Create a new inventory entry.

        Args:
            inventory_data: The inventory information to create (includes denormalized fields)

        Returns:
            InventoryCreateResponse with the created inventory ID

        Raises:
            MicroserviceValidationError: If the inventory data is invalid
            MicroserviceConnectionError: If unable to connect to the inventory service
            MicroserviceHTTPError: If the inventory service returns an error
        """
        pass

    @abstractmethod
    async def get_inventories(
        self,
        limit: int = 10,
        offset: int = 0,
        sku: Optional[str] = None,
        warehouse_id: Optional[UUID] = None,
    ) -> PaginatedInventoriesResponse:
        """
        Retrieve a paginated list of inventories with optional filters.

        Args:
            limit: Maximum number of inventories to return
            offset: Number of inventories to skip
            sku: Optional product SKU filter
            warehouse_id: Optional warehouse ID filter

        Returns:
            PaginatedInventoriesResponse with inventory data

        Raises:
            MicroserviceConnectionError: If unable to connect to the inventory service
            MicroserviceHTTPError: If the inventory service returns an error
        """
        pass
