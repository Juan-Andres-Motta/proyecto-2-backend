"""
Port interface for Order microservice operations (client app).

This defines the contract for order creation via client app
without specifying how the communication is implemented.
"""

from abc import ABC, abstractmethod

from client_app.schemas.order_schemas import OrderCreateInput, OrderCreateResponse


class OrderPort(ABC):
    """
    Abstract port interface for client app order operations.

    Implementations of this port handle communication with the order
    microservice for creating orders via the client app.
    """

    @abstractmethod
    async def create_order(self, order_data: OrderCreateInput) -> OrderCreateResponse:
        """
        Create a new order via client app.

        This method automatically sets metodo_creacion to 'app_cliente'
        and ensures no seller_id or visit_id are included.

        Args:
            order_data: The order information (customer_id, items)

        Returns:
            OrderCreateResponse with the created order ID

        Raises:
            MicroserviceValidationError: If the order data is invalid
            MicroserviceConnectionError: If unable to connect to the order service
            MicroserviceHTTPError: If the order service returns an error
        """
        pass
