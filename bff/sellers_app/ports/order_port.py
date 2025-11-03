"""
Port interface for Order microservice operations (sellers app).

This defines the contract for order creation via sellers app
without specifying how the communication is implemented.
"""

from abc import ABC, abstractmethod
from uuid import UUID

from sellers_app.schemas.order_schemas import OrderCreateInput, OrderCreateResponse


class OrderPort(ABC):
    """
    Abstract port interface for sellers app order operations.

    Implementations of this port handle communication with the order
    microservice for creating orders via the sellers app.
    """

    @abstractmethod
    async def create_order(self, order_data: OrderCreateInput, seller_id: UUID) -> OrderCreateResponse:
        """
        Create a new order via sellers app.

        This method automatically sets metodo_creacion to 'app_vendedor'
        and requires seller_id. visit_id is optional.

        Args:
            order_data: The order information (customer_id, items, visit_id?)
            seller_id: The seller UUID (fetched from authenticated user)

        Returns:
            OrderCreateResponse with the created order ID

        Raises:
            MicroserviceValidationError: If the order data is invalid
            MicroserviceConnectionError: If unable to connect to the order service
            MicroserviceHTTPError: If the order service returns an error
        """
        pass
