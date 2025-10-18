"""Get order by ID use case."""

import logging
from uuid import UUID

from src.application.ports import OrderRepository
from src.domain.entities import Order

logger = logging.getLogger(__name__)


class GetOrderByIdUseCase:
    """
    Use case for retrieving a single order by ID.
    """

    def __init__(self, order_repository: OrderRepository):
        self.order_repository = order_repository

    async def execute(self, order_id: UUID) -> Order | None:
        """
        Get an order by its ID.

        Args:
            order_id: The order UUID

        Returns:
            Order entity if found, None otherwise

        Raises:
            RepositoryError: If query fails
        """
        logger.info(f"Fetching order {order_id}")

        order = await self.order_repository.find_by_id(order_id)

        if order:
            logger.debug(f"Order {order_id} found")
        else:
            logger.warning(f"Order {order_id} not found")

        return order
