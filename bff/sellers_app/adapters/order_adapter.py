"""
Order adapter implementation for sellers app.

This adapter implements the OrderPort interface using HTTP communication
with the Order microservice.
"""

import logging
from uuid import UUID

from sellers_app.ports.order_port import OrderPort
from sellers_app.schemas.order_schemas import (
    OrderCreateInput,
    OrderCreateResponse,
)
from web.adapters.http_client import HttpClient

logger = logging.getLogger(__name__)


class OrderAdapter(OrderPort):
    """
    HTTP adapter for order microservice operations (sellers app).

    This adapter handles communication with the order microservice
    for creating orders via the sellers app.
    """

    def __init__(self, http_client: HttpClient):
        """
        Initialize the order adapter.

        Args:
            http_client: Configured HTTP client for the order service
        """
        self.client = http_client

    async def create_order(self, order_data: OrderCreateInput, seller_id: UUID) -> OrderCreateResponse:
        """
        Create a new order via sellers app.

        Transforms sellers app input to Order Service API format:
        - Adds metodo_creacion="app_vendedor"
        - Includes seller_id (required)
        - Includes visit_id if provided (optional)

        Args:
            order_data: Sellers app order input (customer_id, items, visit_id?)
            seller_id: The seller UUID (fetched from authenticated user)

        Returns:
            OrderCreateResponse with order ID

        Raises:
            MicroserviceValidationError: If order data is invalid
            MicroserviceConnectionError: If unable to connect to order service
            MicroserviceHTTPError: If order service returns an error
        """
        logger.info(f"Creating order (sellers app): customer_id={order_data.customer_id}, seller_id={seller_id}, items_count={len(order_data.items)}, visit_id={order_data.visit_id}, metodo_creacion='app_vendedor'")
        # Transform sellers app schema to Order Service API schema
        payload = {
            "customer_id": str(order_data.customer_id),
            "seller_id": str(seller_id),  # Required
            "metodo_creacion": "app_vendedor",  # Hardcoded for sellers app
            "items": [
                {"inventario_id": str(item.inventario_id), "cantidad": item.cantidad}
                for item in order_data.items
            ],
        }

        # Add visit_id if provided (optional)
        if order_data.visit_id is not None:
            payload["visit_id"] = str(order_data.visit_id)

        response_data = await self.client.post("/order/order", json=payload)

        return OrderCreateResponse(
            id=response_data["id"],
            message=response_data.get("message", "Order created successfully"),
        )
