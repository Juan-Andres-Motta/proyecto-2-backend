from typing import List, Tuple

from src.adapters.output.repositories.order_repository import OrderRepository
from src.infrastructure.database.models import Order


class ListOrdersUseCase:
    def __init__(self, repository: OrderRepository):
        self.repository = repository

    async def execute(
        self, limit: int = 10, offset: int = 0
    ) -> Tuple[List[Order], int]:
        return await self.repository.list_orders(limit=limit, offset=offset)
