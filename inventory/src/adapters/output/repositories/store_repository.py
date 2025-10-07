from typing import List, Tuple

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.models import Store


class StoreRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, store_data: dict) -> Store:
        store = Store(**store_data)
        self.session.add(store)
        await self.session.commit()
        await self.session.refresh(store)
        return store

    async def list_stores(
        self, limit: int = 10, offset: int = 0
    ) -> Tuple[List[Store], int]:
        # Get total count
        count_stmt = select(func.count()).select_from(Store)
        count_result = await self.session.execute(count_stmt)
        total = count_result.scalar()

        # Get paginated data
        stmt = select(Store).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        stores = result.scalars().all()

        return stores, total
