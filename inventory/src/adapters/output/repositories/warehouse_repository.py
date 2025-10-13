from typing import List, Tuple

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.models import Warehouse


class WarehouseRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, warehouse_data: dict) -> Warehouse:
        warehouse = Warehouse(**warehouse_data)
        self.session.add(warehouse)
        await self.session.commit()
        await self.session.refresh(warehouse)
        return warehouse

    async def list_warehouses(
        self, limit: int = 10, offset: int = 0
    ) -> Tuple[List[Warehouse], int]:
        # Get total count
        count_stmt = select(func.count()).select_from(Warehouse)
        count_result = await self.session.execute(count_stmt)
        total = count_result.scalar()

        # Get paginated data
        stmt = select(Warehouse).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        warehouses = result.scalars().all()

        return warehouses, total
