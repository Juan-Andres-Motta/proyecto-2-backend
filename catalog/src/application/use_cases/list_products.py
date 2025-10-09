from typing import List, Tuple

from src.adapters.output.repositories.product_repository import ProductRepository
from src.infrastructure.database.models import Product


class ListProductsUseCase:
    def __init__(self, repository: ProductRepository):
        self.repository = repository

    async def execute(
        self, limit: int = 10, offset: int = 0
    ) -> Tuple[List[Product], int]:
        return await self.repository.list_products(limit=limit, offset=offset)