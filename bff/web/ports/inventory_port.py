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
    PaginatedReportsResponse,
    PaginatedWarehousesResponse,
    ReportCreateRequest,
    ReportCreateResponse,
    ReportResponse,
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

    @abstractmethod
    async def create_report(
        self, user_id: UUID, report_data: ReportCreateRequest
    ) -> ReportCreateResponse:
        """
        Create a new inventory report.

        Args:
            user_id: The ID of the user creating the report
            report_data: The report configuration

        Returns:
            ReportCreateResponse with the report ID and status

        Raises:
            MicroserviceValidationError: If the report data is invalid
            MicroserviceConnectionError: If unable to connect to the inventory service
            MicroserviceHTTPError: If the inventory service returns an error
        """
        pass

    @abstractmethod
    async def get_reports(
        self,
        user_id: UUID,
        limit: int = 10,
        offset: int = 0,
        status: Optional[str] = None,
        report_type: Optional[str] = None,
    ) -> PaginatedReportsResponse:
        """
        Retrieve a paginated list of reports for a user.

        Args:
            user_id: The ID of the user
            limit: Maximum number of reports to return
            offset: Number of reports to skip
            status: Optional status filter
            report_type: Optional report type filter

        Returns:
            PaginatedReportsResponse with report data

        Raises:
            MicroserviceConnectionError: If unable to connect to the inventory service
            MicroserviceHTTPError: If the inventory service returns an error
        """
        pass

    @abstractmethod
    async def get_report(self, user_id: UUID, report_id: UUID) -> ReportResponse:
        """
        Get a single report by ID with download URL.

        Args:
            user_id: The ID of the user
            report_id: The ID of the report

        Returns:
            ReportResponse with report details and download URL

        Raises:
            MicroserviceConnectionError: If unable to connect to the inventory service
            MicroserviceHTTPError: If the inventory service returns an error
        """
        pass
