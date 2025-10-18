from typing import List, Tuple

from src.application.ports.product_repository_port import ProductRepositoryPort
from src.domain.entities.product import Product


class ListProductsUseCase:
    def __init__(self, repository: ProductRepositoryPort):
        self.repository = repository

    async def execute(
        self, limit: int = 10, offset: int = 0
    ) -> Tuple[List[Product], int]:
        return await self.repository.list_products(limit=limit, offset=offset)
