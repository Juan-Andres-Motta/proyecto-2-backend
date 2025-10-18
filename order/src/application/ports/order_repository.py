"""Order repository port (abstract interface)."""

from abc import ABC, abstractmethod
from typing import List, Tuple
from uuid import UUID

from src.domain.entities import Order


class OrderRepository(ABC):
    """
    Abstract repository interface for Order persistence.

    Implementations handle the persistence layer details (e.g., PostgreSQL, MongoDB).
    """

    @abstractmethod
    async def save(self, order: Order) -> Order:
        """
        Save an order (insert or update).

        Args:
            order: The order entity to save

        Returns:
            The saved order entity

        Raises:
            RepositoryError: If save operation fails
        """
        pass

    @abstractmethod
    async def find_by_id(self, order_id: UUID) -> Order | None:
        """
        Find an order by ID.

        Args:
            order_id: The order UUID

        Returns:
            The order entity if found, None otherwise

        Raises:
            RepositoryError: If query fails
        """
        pass

    @abstractmethod
    async def find_all(
        self, limit: int = 10, offset: int = 0
    ) -> Tuple[List[Order], int]:
        """
        Find all orders with pagination.

        Args:
            limit: Maximum number of orders to return
            offset: Number of orders to skip

        Returns:
            Tuple of (list of orders, total count)

        Raises:
            RepositoryError: If query fails
        """
        pass
