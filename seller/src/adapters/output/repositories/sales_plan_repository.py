from typing import List, Tuple

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.models import SalesPlan


class SalesPlanRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, sales_plan_data: dict) -> SalesPlan:
        sales_plan = SalesPlan(**sales_plan_data)
        self.session.add(sales_plan)
        await self.session.commit()
        await self.session.refresh(sales_plan)
        return sales_plan

    async def list_sales_plans(
        self, limit: int = 10, offset: int = 0
    ) -> Tuple[List[SalesPlan], int]:
        # Get total count
        count_stmt = select(func.count()).select_from(SalesPlan)
        count_result = await self.session.execute(count_stmt)
        total = count_result.scalar()

        # Get paginated data
        stmt = select(SalesPlan).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        sales_plans = result.scalars().all()

        return sales_plans, total
