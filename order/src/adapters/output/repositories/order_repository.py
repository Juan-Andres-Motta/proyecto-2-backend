from typing import List, Tuple

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.infrastructure.database.models import Order, OrderItem


class OrderRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, order_data: dict, items_data: list) -> Order:
        # Create order
        order = Order(**order_data)
        self.session.add(order)
        await self.session.flush()  # Get order.id

        # Create order items
        for item_data in items_data:
            item_data["order_id"] = order.id
            item = OrderItem(**item_data)
            self.session.add(item)

        await self.session.commit()

        # Reload the order with items
        stmt = select(Order).options(selectinload(Order.items)).where(Order.id == order.id)
        result = await self.session.execute(stmt)
        order = result.scalar_one()

        return order

    async def list_orders(
        self, limit: int = 10, offset: int = 0
    ) -> Tuple[List[Order], int]:
        # Get total count
        count_stmt = select(func.count()).select_from(Order)
        count_result = await self.session.execute(count_stmt)
        total = count_result.scalar()

        # Get paginated data with items loaded
        stmt = (
            select(Order).options(selectinload(Order.items)).limit(limit).offset(offset)
        )
        result = await self.session.execute(stmt)
        orders = result.scalars().all()

        return orders, total
