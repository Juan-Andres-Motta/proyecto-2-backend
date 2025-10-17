"""Sales plan repository port (interface)."""
from abc import ABC, abstractmethod
from typing import List, Optional, Tuple
from uuid import UUID

from src.domain.entities.sales_plan import SalesPlan


class SalesPlanRepositoryPort(ABC):
    """Port for sales plan repository operations.

    Defined by application layer needs.
    Implemented by infrastructure layer.
    """

    @abstractmethod
    async def create(self, sales_plan: SalesPlan) -> SalesPlan:
        """Create a new sales plan.

        Args:
            sales_plan: Domain entity to persist

        Returns:
            Created sales plan domain entity
        """
        ...  # pragma: no cover

    @abstractmethod
    async def find_by_seller_and_period(
        self,
        seller_id: UUID,
        sales_period: str
    ) -> Optional[SalesPlan]:
        """Find a sales plan by seller and period.

        Used to check for duplicates.

        Args:
            seller_id: UUID of the seller
            sales_period: Period string (Q{1-4}-{YEAR})

        Returns:
            SalesPlan domain entity if found, None otherwise
        """
        ...  # pragma: no cover

    @abstractmethod
    async def list_sales_plans(
        self,
        limit: int = 10,
        offset: int = 0
    ) -> Tuple[List[SalesPlan], int]:
        """List sales plans with pagination.

        Args:
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            Tuple of (list of SalesPlan entities, total count)
        """
        ...  # pragma: no cover
