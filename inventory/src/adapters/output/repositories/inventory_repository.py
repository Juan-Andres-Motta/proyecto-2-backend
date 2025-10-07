from typing import List, Tuple

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.models import Inventory


class InventoryRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, inventory_data: dict) -> Inventory:
        inventory = Inventory(**inventory_data)
        self.session.add(inventory)
        await self.session.commit()
        await self.session.refresh(inventory)
        return inventory

    async def list_inventories(
        self, limit: int = 10, offset: int = 0
    ) -> Tuple[List[Inventory], int]:
        # Get total count
        count_stmt = select(func.count()).select_from(Inventory)
        count_result = await self.session.execute(count_stmt)
        total = count_result.scalar()

        # Get paginated data
        stmt = select(Inventory).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        inventories = result.scalars().all()

        return inventories, total
