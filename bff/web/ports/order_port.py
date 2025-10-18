"""
Port interface for Order microservice operations.

This defines the contract for order management operations
without specifying how the communication is implemented.
"""

from abc import ABC, abstractmethod

from web.schemas.order_schemas import (
    OrderCreate,
    OrderCreateResponse,
    PaginatedOrdersResponse,
)


class OrderPort(ABC):
    """
    Abstract port interface for order operations.

    Implementations of this port handle communication with the order
    microservice for order management.
    """

    @abstractmethod
    async def create_order(self, order_data: OrderCreate) -> OrderCreateResponse:
        """
        Create a new order.

        Args:
            order_data: The order information to create, including items

        Returns:
            OrderCreateResponse with the created order ID

        Raises:
            MicroserviceValidationError: If the order data is invalid
            MicroserviceConnectionError: If unable to connect to the order service
            MicroserviceHTTPError: If the order service returns an error
        """
        pass

    @abstractmethod
    async def get_orders(
        self, limit: int = 10, offset: int = 0
    ) -> PaginatedOrdersResponse:
        """
        Retrieve a paginated list of orders.

        Args:
            limit: Maximum number of orders to return
            offset: Number of orders to skip

        Returns:
            PaginatedOrdersResponse with order data

        Raises:
            MicroserviceConnectionError: If unable to connect to the order service
            MicroserviceHTTPError: If the order service returns an error
        """
        pass
