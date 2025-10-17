"""List sales plans use case."""
from typing import List, Tuple

from src.application.ports.sales_plan_repository_port import SalesPlanRepositoryPort
from src.domain.entities.sales_plan import SalesPlan


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
        return await self.repository.list_sales_plans(limit=limit, offset=offset)
