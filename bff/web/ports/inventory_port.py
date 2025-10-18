"""
Port interface for Inventory microservice operations.

This defines the contract for warehouse management operations
without specifying how the communication is implemented.
"""

from abc import ABC, abstractmethod

from web.schemas.inventory_schemas import (
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
