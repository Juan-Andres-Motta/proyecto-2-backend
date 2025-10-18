"""List orders use case."""

import logging
from typing import List, Tuple

from src.application.ports import OrderRepository
from src.domain.entities import Order

logger = logging.getLogger(__name__)


class ListOrdersUseCase:
    """
    Use case for listing orders with pagination.
    """

    def __init__(self, order_repository: OrderRepository):
        self.order_repository = order_repository

    async def execute(
        self, limit: int = 10, offset: int = 0
    ) -> Tuple[List[Order], int]:
        """
        List orders with pagination.

        Args:
            limit: Maximum number of orders to return (default 10)
            offset: Number of orders to skip (default 0)

        Returns:
            Tuple of (list of orders, total count)

        Raises:
            RepositoryError: If query fails
        """
        logger.info(f"Listing orders (limit={limit}, offset={offset})")

        orders, total = await self.order_repository.find_all(limit=limit, offset=offset)

        logger.debug(f"Found {len(orders)} orders (total: {total})")
        return orders, total
