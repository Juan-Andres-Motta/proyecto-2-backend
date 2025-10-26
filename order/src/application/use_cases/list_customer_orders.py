"""List customer orders use case."""

import logging
from typing import List, Tuple
from uuid import UUID

from src.application.ports import OrderRepository
from src.domain.entities import Order

logger = logging.getLogger(__name__)


class ListCustomerOrdersUseCase:
    """
    Use case for listing orders for a specific customer with pagination.
    """

    def __init__(self, order_repository: OrderRepository):
        self.order_repository = order_repository

    async def execute(
        self, customer_id: UUID, limit: int = 10, offset: int = 0
    ) -> Tuple[List[Order], int]:
        """
        List orders for a specific customer with pagination.

        Args:
            customer_id: UUID of the customer
            limit: Maximum number of orders to return (default 10)
            offset: Number of orders to skip (default 0)

        Returns:
            Tuple of (list of orders, total count)

        Raises:
            RepositoryError: If query fails
        """
        logger.info(f"Listing orders for customer {customer_id} (limit={limit}, offset={offset})")

        orders, total = await self.order_repository.find_by_customer(
            customer_id=customer_id, limit=limit, offset=offset
        )

        logger.debug(f"Found {len(orders)} orders for customer {customer_id} (total: {total})")
        return orders, total
