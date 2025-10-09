from typing import List, Tuple

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.models import Product


class ProductRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_products(
        self, limit: int = 10, offset: int = 0
    ) -> Tuple[List[Product], int]:
        # Get total count
        count_stmt = select(func.count()).select_from(Product)
        count_result = await self.session.execute(count_stmt)
        total = count_result.scalar()

        # Get paginated data
        stmt = select(Product).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        products = result.scalars().all()

        return products, total
