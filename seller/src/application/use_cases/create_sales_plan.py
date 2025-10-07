from src.adapters.output.repositories.sales_plan_repository import SalesPlanRepository
from src.infrastructure.database.models import SalesPlan


class CreateSalesPlanUseCase:
    def __init__(self, repository: SalesPlanRepository):
        self.repository = repository

    async def execute(self, sales_plan_data: dict) -> SalesPlan:
        return await self.repository.create(sales_plan_data)
