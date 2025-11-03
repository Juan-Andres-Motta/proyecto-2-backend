"""
Order adapter implementation for client app.

This adapter implements the OrderPort interface using HTTP communication
with the Order microservice.
"""

import logging
from typing import List
from uuid import UUID

from client_app.ports.order_port import OrderPort
from client_app.schemas.order_schemas import (
    OrderCreateInput,
    OrderCreateResponse,
    OrderItemInput,
    PaginatedOrdersResponse,
)
from web.adapters.http_client import HttpClient

logger = logging.getLogger(__name__)


class OrderAdapter(OrderPort):
    """
    HTTP adapter for order microservice operations (client app).

    This adapter handles communication with the order microservice
    for creating orders via the client app.
    """

    def __init__(self, http_client: HttpClient):
        """
        Initialize the order adapter.

        Args:
            http_client: Configured HTTP client for the order service
        """
        self.client = http_client

    async def create_order(self, order_data: OrderCreateInput, customer_id: UUID) -> OrderCreateResponse:
        """
        Create a new order via client app.

        Transforms client app input to Order Service API format:
        - Adds metodo_creacion="app_cliente"
        - Ensures seller_id and visit_id are not included

        Args:
            order_data: Client app order input (items only)
            customer_id: The customer UUID (fetched from authenticated user)

        Returns:
            OrderCreateResponse with order ID

        Raises:
            MicroserviceValidationError: If order data is invalid
            MicroserviceConnectionError: If unable to connect to order service
            MicroserviceHTTPError: If order service returns an error
        """
        logger.info(f"Creating order (client app): customer_id={customer_id}, items_count={len(order_data.items)}, metodo_creacion='app_cliente'")
        # Transform client app schema to Order Service API schema
        payload = {
            "customer_id": str(customer_id),
            "metodo_creacion": "app_cliente",  # Hardcoded for client app
            "items": [
                {"producto_id": str(item.producto_id), "cantidad": item.cantidad}
                for item in order_data.items
            ],
            # No seller_id or visit_id for client app orders
        }

        response_data = await self.client.post("/order/order", json=payload)

        return OrderCreateResponse(
            id=response_data["id"], message=response_data.get("message", "Order created successfully")
        )

    async def list_customer_orders(
        self, customer_id: UUID, limit: int = 10, offset: int = 0
    ) -> PaginatedOrdersResponse:
        """
        List orders for a specific customer.

        Args:
            customer_id: Customer UUID
            limit: Maximum number of orders to return
            offset: Number of orders to skip

        Returns:
            PaginatedOrdersResponse with customer's orders

        Raises:
            MicroserviceConnectionError: If unable to connect to order service
            MicroserviceHTTPError: If order service returns an error
        """
        logger.info(f"Listing orders for customer {customer_id} (limit={limit}, offset={offset})")

        params = {"limit": limit, "offset": offset}

        response_data = await self.client.get(
            f"/order/customers/{customer_id}/orders", params=params
        )

        return PaginatedOrdersResponse(**response_data)
