from typing import List

from src.adapters.output.repositories.product_repository import ProductRepository
from src.infrastructure.database.models import Product


class CreateProductsUseCase:
    def __init__(self, repository: ProductRepository):
        self.repository = repository

    async def execute(self, products_data: List[dict]) -> List[Product]:
        """
        Create multiple products in a batch with transaction support.

        Args:
            products_data: List of dictionaries containing product data

        Returns:
            List of created Product objects

        Raises:
            Exception: If any product creation fails (all creations are rolled back)
        """
        return await self.repository.batch_create(products_data)
