"""
Delivery adapter implementation for client app.

This adapter implements the DeliveryPort interface using HTTP communication
with the Delivery microservice.
"""

import logging
from typing import Optional
from uuid import UUID

from client_app.ports.delivery_port import DeliveryPort
from client_app.schemas.shipment_schemas import ShipmentInfo
from common.http_client import HttpClient
from common.exceptions import MicroserviceHTTPError

logger = logging.getLogger(__name__)


class DeliveryAdapter(DeliveryPort):
    """
    HTTP adapter for delivery microservice operations (client app).

    This adapter handles communication with the delivery microservice
    for fetching shipment information.
    """

    def __init__(self, http_client: HttpClient):
        """
        Initialize the delivery adapter.

        Args:
            http_client: Configured HTTP client for the delivery service
        """
        self.client = http_client

    async def get_shipment_by_order(self, order_id: UUID) -> Optional[ShipmentInfo]:
        """
        Get shipment information for a specific order.

        Args:
            order_id: The order UUID to look up shipment for

        Returns:
            ShipmentInfo if a shipment exists for the order, None otherwise

        Raises:
            MicroserviceConnectionError: If unable to connect to delivery service
            MicroserviceHTTPError: If delivery service returns an unexpected error
        """
        logger.info(f"Fetching shipment for order {order_id}")

        try:
            response_data = await self.client.get(f"/delivery/orders/{order_id}/shipment")
            return ShipmentInfo(**response_data)

        except MicroserviceHTTPError as e:
            # Handle 404 as None (no shipment yet for this order)
            if e.status_code == 404:
                logger.debug(f"No shipment found for order {order_id}")
                return None
            # Re-raise other HTTP errors
            raise
