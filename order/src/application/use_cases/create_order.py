from src.adapters.output.repositories.order_repository import OrderRepository
from src.infrastructure.database.models import Order


class CreateOrderUseCase:
    def __init__(self, repository: OrderRepository):
        self.repository = repository

    async def execute(self, order_data: dict, items_data: list) -> Order:
        return await self.repository.create(order_data, items_data)
