"""
Seller adapter implementation.

This adapter implements the SellerPort interface using HTTP communication.
"""

import logging
from uuid import UUID

from common.http_client import HttpClient

from ..ports.seller_port import SellerPort
from ..schemas.seller_schemas import (
    PaginatedSalesPlansResponse,
    PaginatedSellersResponse,
    SalesPlanCreate,
    SalesPlanCreateResponse,
    SellerCreate,
    SellerCreateResponse,
)

logger = logging.getLogger(__name__)


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
        logger.info(f"Creating seller: name='{seller_data.name}', email='{seller_data.email}'")
        response_data = await self.client.post(
            "/seller/sellers",
            json=seller_data.model_dump(mode="json"),
        )
        return SellerCreateResponse(**response_data)

    async def get_sellers(
        self, limit: int = 10, offset: int = 0
    ) -> PaginatedSellersResponse:
        """Retrieve a paginated list of sellers."""
        logger.info(f"Getting sellers: limit={limit}, offset={offset}")
        response_data = await self.client.get(
            "/seller/sellers",
            params={"limit": limit, "offset": offset},
        )
        return PaginatedSellersResponse(**response_data)

    async def create_sales_plan(
        self, sales_plan_data: SalesPlanCreate
    ) -> SalesPlanCreateResponse:
        """Create a new sales plan for a seller."""
        logger.info(f"Creating sales plan: seller_id={sales_plan_data.seller_id}, sales_period={sales_plan_data.sales_period}, goal={sales_plan_data.goal}")
        response_data = await self.client.post(
            "/seller/sales-plans",
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
        logger.info(f"Getting sales plans: limit={limit}, offset={offset}")
        response_data = await self.client.get(
            "/seller/sales-plans",
            params={"limit": limit, "offset": offset},
        )
        return PaginatedSalesPlansResponse(**response_data)

    async def get_seller_sales_plans(
        self, seller_id: UUID, limit: int = 10, offset: int = 0
    ) -> PaginatedSalesPlansResponse:
        """Retrieve sales plans for a specific seller."""
        logger.info(f"Getting seller sales plans: seller_id={seller_id}, limit={limit}, offset={offset}")
        response_data = await self.client.get(
            f"/seller/sellers/{seller_id}/sales-plans",
            params={"limit": limit, "offset": offset},
        )
        return PaginatedSalesPlansResponse(**response_data)
