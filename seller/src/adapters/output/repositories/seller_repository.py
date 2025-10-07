from typing import List, Tuple

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.models import Seller


class SellerRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, seller_data: dict) -> Seller:
        seller = Seller(**seller_data)
        self.session.add(seller)
        await self.session.commit()
        await self.session.refresh(seller)
        return seller

    async def list_sellers(
        self, limit: int | None = 10, offset: int = 0
    ) -> Tuple[List[Seller], int]:
        # Get total count
        count_stmt = select(func.count()).select_from(Seller)
        count_result = await self.session.execute(count_stmt)
        total = count_result.scalar()

        # Get data
        stmt = select(Seller)
        if limit is not None:
            stmt = stmt.limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        sellers = result.scalars().all()

        return sellers, total
