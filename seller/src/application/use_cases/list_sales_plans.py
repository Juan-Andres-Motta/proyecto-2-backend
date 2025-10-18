"""List sales plans use case."""
import logging
from typing import List, Tuple

from src.application.ports.sales_plan_repository_port import SalesPlanRepositoryPort
from src.domain.entities.sales_plan import SalesPlan

logger = logging.getLogger(__name__)


class ListSalesPlansUseCase:
    """Use case for listing sales plans with pagination."""

    def __init__(self, repository: SalesPlanRepositoryPort):
        """Initialize with repository port (dependency injection).

        Args:
            repository: Port for sales plan queries
        """
        self.repository = repository

    async def execute(
        self,
        limit: int = 10,
        offset: int = 0
    ) -> Tuple[List[SalesPlan], int]:
        """List sales plans with pagination.

        Args:
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            Tuple of (list of SalesPlan domain entities, total count)
            Each SalesPlan has seller eager-loaded and status calculated
        """
        logger.info(f"Listing sales plans: limit={limit}, offset={offset}")

        sales_plans, total = await self.repository.list_sales_plans(limit=limit, offset=offset)

        logger.info(f"Sales plans retrieved successfully: count={len(sales_plans)}, total={total}")
        logger.debug(f"Retrieved sales plan IDs: {[str(sp.id) for sp in sales_plans]}")
        return sales_plans, total
