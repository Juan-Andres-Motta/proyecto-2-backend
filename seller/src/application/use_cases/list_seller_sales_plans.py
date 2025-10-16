from typing import List, Tuple
from uuid import UUID

from src.adapters.output.repositories.sales_plan_repository import SalesPlanRepository
from src.infrastructure.database.models import SalesPlan


class ListSellerSalesPlansUseCase:
    def __init__(self, repository: SalesPlanRepository):
        self.repository = repository

    async def execute(
        self, seller_id: UUID, limit: int = 10, offset: int = 0
    ) -> Tuple[List[SalesPlan], int]:
        return await self.repository.list_sales_plans_by_seller(
            seller_id=seller_id, limit=limit, offset=offset
        )
