from typing import List, Tuple

from src.adapters.output.repositories.sales_plan_repository import SalesPlanRepository
from src.infrastructure.database.models import SalesPlan


class ListSalesPlansUseCase:
    def __init__(self, repository: SalesPlanRepository):
        self.repository = repository

    async def execute(
        self, limit: int = 10, offset: int = 0
    ) -> Tuple[List[SalesPlan], int]:
        return await self.repository.list_sales_plans(limit=limit, offset=offset)
