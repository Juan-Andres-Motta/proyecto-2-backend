"""
Order adapter implementation for sellers app.

This adapter implements the OrderPort interface using HTTP communication
with the Order microservice.
"""

from sellers_app.ports.order_port import OrderPort
from sellers_app.schemas.order_schemas import (
    OrderCreateInput,
    OrderCreateResponse,
)
from web.adapters.http_client import HttpClient


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

    async def create_order(self, order_data: OrderCreateInput) -> OrderCreateResponse:
        """
        Create a new order via sellers app.

        Transforms sellers app input to Order Service API format:
        - Adds metodo_creacion="app_vendedor"
        - Includes seller_id (required)
        - Includes visit_id if provided (optional)

        Args:
            order_data: Sellers app order input

        Returns:
            OrderCreateResponse with order ID

        Raises:
            MicroserviceValidationError: If order data is invalid
            MicroserviceConnectionError: If unable to connect to order service
            MicroserviceHTTPError: If order service returns an error
        """
        # Transform sellers app schema to Order Service API schema
        payload = {
            "customer_id": str(order_data.customer_id),
            "seller_id": str(order_data.seller_id),  # Required
            "metodo_creacion": "app_vendedor",  # Hardcoded for sellers app
            "items": [
                {"producto_id": str(item.producto_id), "cantidad": item.cantidad}
                for item in order_data.items
            ],
        }

        # Add visit_id if provided (optional)
        if order_data.visit_id is not None:
            payload["visit_id"] = str(order_data.visit_id)

        response_data = await self.client.post("/order", json=payload)

        return OrderCreateResponse(
            id=response_data["id"],
            message=response_data.get("message", "Order created successfully"),
        )
