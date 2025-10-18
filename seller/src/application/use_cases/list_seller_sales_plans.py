import logging
from typing import List, Tuple
from uuid import UUID

from src.adapters.output.repositories.sales_plan_repository import SalesPlanRepository
from src.domain.entities.sales_plan import SalesPlan

logger = logging.getLogger(__name__)


class ListSellerSalesPlansUseCase:
    def __init__(self, repository: SalesPlanRepository):
        self.repository = repository

    async def execute(
        self, seller_id: UUID, limit: int = 10, offset: int = 0
    ) -> Tuple[List[SalesPlan], int]:
        """List sales plans for a specific seller."""
        logger.info(f"Listing sales plans for seller: seller_id={seller_id}, limit={limit}, offset={offset}")

        sales_plans, total = await self.repository.list_sales_plans_by_seller(
            seller_id=seller_id, limit=limit, offset=offset
        )

        logger.info(f"Seller sales plans retrieved successfully: seller_id={seller_id}, count={len(sales_plans)}, total={total}")
        logger.debug(f"Retrieved sales plan IDs for seller {seller_id}: {[str(sp.id) for sp in sales_plans]}")
        return sales_plans, total
