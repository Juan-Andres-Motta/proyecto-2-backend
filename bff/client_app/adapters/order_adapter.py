"""
Order adapter implementation for client app.

This adapter implements the OrderPort interface using HTTP communication
with the Order microservice.
"""

from typing import List

from client_app.ports.order_port import OrderPort
from client_app.schemas.order_schemas import (
    OrderCreateInput,
    OrderCreateResponse,
    OrderItemInput,
)
from web.adapters.http_client import HttpClient


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

    async def create_order(self, order_data: OrderCreateInput) -> OrderCreateResponse:
        """
        Create a new order via client app.

        Transforms client app input to Order Service API format:
        - Adds metodo_creacion="app_cliente"
        - Ensures seller_id and visit_id are not included

        Args:
            order_data: Client app order input

        Returns:
            OrderCreateResponse with order ID

        Raises:
            MicroserviceValidationError: If order data is invalid
            MicroserviceConnectionError: If unable to connect to order service
            MicroserviceHTTPError: If order service returns an error
        """
        # Transform client app schema to Order Service API schema
        payload = {
            "customer_id": str(order_data.customer_id),
            "metodo_creacion": "app_cliente",  # Hardcoded for client app
            "items": [
                {"producto_id": str(item.producto_id), "cantidad": item.cantidad}
                for item in order_data.items
            ],
            # No seller_id or visit_id for client app orders
        }

        response_data = await self.client.post("/order", json=payload)

        return OrderCreateResponse(
            id=response_data["id"], message=response_data.get("message", "Order created successfully")
        )
