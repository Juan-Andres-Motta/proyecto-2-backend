"""
Seller adapter implementation.

This adapter implements the SellerPort interface using HTTP communication.
"""

from uuid import UUID

from ..ports.seller_port import SellerPort
from ..schemas.seller_schemas import (
    PaginatedSalesPlansResponse,
    PaginatedSellersResponse,
    SalesPlanCreate,
    SalesPlanCreateResponse,
    SellerCreate,
    SellerCreateResponse,
)

from .http_client import HttpClient


class SellerAdapter(SellerPort):
    """
    HTTP adapter for seller microservice operations.

    This adapter implements the SellerPort interface and handles
    communication with the seller microservice via HTTP.
    """

    def __init__(self, http_client: HttpClient):
        """
        Initialize the seller adapter.

        Args:
            http_client: Configured HTTP client for the seller service
        """
        self.client = http_client

    async def create_seller(self, seller_data: SellerCreate) -> SellerCreateResponse:
        """Create a new seller."""
        response_data = await self.client.post(
            "/sellers",
            json=seller_data.model_dump(mode="json"),
        )
        return SellerCreateResponse(**response_data)

    async def get_sellers(
        self, limit: int = 10, offset: int = 0
    ) -> PaginatedSellersResponse:
        """Retrieve a paginated list of sellers."""
        response_data = await self.client.get(
            "/sellers",
            params={"limit": limit, "offset": offset},
        )
        return PaginatedSellersResponse(**response_data)

    async def create_sales_plan(
        self, sales_plan_data: SalesPlanCreate
    ) -> SalesPlanCreateResponse:
        """Create a new sales plan for a seller."""
        response_data = await self.client.post(
            "/sales-plans",
            json=sales_plan_data.model_dump(mode="json"),
        )
        # Seller service returns full sales plan object, extract id
        return SalesPlanCreateResponse(
            id=response_data["id"],
            message="Sales plan created successfully"
        )

    async def get_sales_plans(
        self, limit: int = 10, offset: int = 0
    ) -> PaginatedSalesPlansResponse:
        """Retrieve a paginated list of sales plans."""
        response_data = await self.client.get(
            "/sales-plans",
            params={"limit": limit, "offset": offset},
        )
        return PaginatedSalesPlansResponse(**response_data)

    async def get_seller_sales_plans(
        self, seller_id: UUID, limit: int = 10, offset: int = 0
    ) -> PaginatedSalesPlansResponse:
        """Retrieve sales plans for a specific seller."""
        response_data = await self.client.get(
            f"/sellers/{seller_id}/sales-plans",
            params={"limit": limit, "offset": offset},
        )
        return PaginatedSalesPlansResponse(**response_data)
