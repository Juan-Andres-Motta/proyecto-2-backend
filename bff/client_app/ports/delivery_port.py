"""
Port interface for Delivery microservice operations (client app).

This defines the contract for fetching shipment information
without specifying how the communication is implemented.
"""

from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID

from client_app.schemas.shipment_schemas import ShipmentInfo


class DeliveryPort(ABC):
    """
    Abstract port interface for client app delivery operations.

    Implementations of this port handle communication with the delivery
    microservice for fetching shipment information.
    """

    @abstractmethod
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
        pass
