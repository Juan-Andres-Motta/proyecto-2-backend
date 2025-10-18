"""
Port interface for Seller microservice operations.

This defines the contract for seller and sales plan management operations
without specifying how the communication is implemented.
"""

from abc import ABC, abstractmethod
from uuid import UUID

from web.schemas.seller_schemas import (
    PaginatedSalesPlansResponse,
    PaginatedSellersResponse,
    SalesPlanCreate,
    SalesPlanCreateResponse,
    SellerCreate,
    SellerCreateResponse,
)


class SellerPort(ABC):
    """
    Abstract port interface for seller operations.

    Implementations of this port handle communication with the seller
    microservice for seller and sales plan management.
    """

    @abstractmethod
    async def create_seller(self, seller_data: SellerCreate) -> SellerCreateResponse:
        """
        Create a new seller.

        Args:
            seller_data: The seller information to create

        Returns:
            SellerCreateResponse with the created seller ID

        Raises:
            MicroserviceValidationError: If the seller data is invalid
            MicroserviceConnectionError: If unable to connect to the seller service
            MicroserviceHTTPError: If the seller service returns an error
        """
        pass

    @abstractmethod
    async def get_sellers(
        self, limit: int = 10, offset: int = 0
    ) -> PaginatedSellersResponse:
        """
        Retrieve a paginated list of sellers.

        Args:
            limit: Maximum number of sellers to return
            offset: Number of sellers to skip

        Returns:
            PaginatedSellersResponse with seller data

        Raises:
            MicroserviceConnectionError: If unable to connect to the seller service
            MicroserviceHTTPError: If the seller service returns an error
        """
        pass

    @abstractmethod
    async def create_sales_plan(
        self, sales_plan_data: SalesPlanCreate
    ) -> SalesPlanCreateResponse:
        """
        Create a new sales plan for a seller.

        Args:
            sales_plan_data: The sales plan information to create

        Returns:
            SalesPlanCreateResponse with the created sales plan ID

        Raises:
            MicroserviceValidationError: If the sales plan data is invalid
            MicroserviceConnectionError: If unable to connect to the seller service
            MicroserviceHTTPError: If the seller service returns an error
        """
        pass

    @abstractmethod
    async def get_sales_plans(
        self, limit: int = 10, offset: int = 0
    ) -> PaginatedSalesPlansResponse:
        """
        Retrieve a paginated list of sales plans.

        Args:
            limit: Maximum number of sales plans to return
            offset: Number of sales plans to skip

        Returns:
            PaginatedSalesPlansResponse with sales plan data

        Raises:
            MicroserviceConnectionError: If unable to connect to the seller service
            MicroserviceHTTPError: If the seller service returns an error
        """
        pass

    @abstractmethod
    async def get_seller_sales_plans(
        self, seller_id: UUID, limit: int = 10, offset: int = 0
    ) -> PaginatedSalesPlansResponse:
        """
        Retrieve sales plans for a specific seller.

        Args:
            seller_id: The ID of the seller
            limit: Maximum number of sales plans to return
            offset: Number of sales plans to skip

        Returns:
            PaginatedSalesPlansResponse with sales plan data for the seller

        Raises:
            ResourceNotFoundError: If the seller doesn't exist
            MicroserviceConnectionError: If unable to connect to the seller service
            MicroserviceHTTPError: If the seller service returns an error
        """
        pass
