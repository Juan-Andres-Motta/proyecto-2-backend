"""
Order adapter implementation.

This adapter implements the OrderPort interface using HTTP communication.
"""

from ..ports.order_port import OrderPort
from ..schemas.order_schemas import (
    OrderCreate,
    OrderCreateResponse,
    PaginatedOrdersResponse,
)

from .http_client import HttpClient


class OrderAdapter(OrderPort):
    """
    HTTP adapter for order microservice operations.

    This adapter implements the OrderPort interface and handles
    communication with the order microservice via HTTP.
    """

    def __init__(self, http_client: HttpClient):
        """
        Initialize the order adapter.

        Args:
            http_client: Configured HTTP client for the order service
        """
        self.client = http_client

    async def create_order(self, order_data: OrderCreate) -> OrderCreateResponse:
        """Create a new order."""
        response_data = await self.client.post(
            "/orders",
            json=order_data.model_dump(mode="json"),
        )
        return OrderCreateResponse(**response_data)

    async def get_orders(
        self, limit: int = 10, offset: int = 0
    ) -> PaginatedOrdersResponse:
        """Retrieve a paginated list of orders."""
        response_data = await self.client.get(
            "/orders",
            params={"limit": limit, "offset": offset},
        )
        return PaginatedOrdersResponse(**response_data)
