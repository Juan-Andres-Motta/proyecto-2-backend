import logging
from typing import List, Tuple

from src.application.ports.product_repository_port import ProductRepositoryPort
from src.domain.entities.product import Product

logger = logging.getLogger(__name__)


class ListProductsUseCase:
    def __init__(self, repository: ProductRepositoryPort):
        self.repository = repository

    async def execute(
        self, limit: int = 10, offset: int = 0
    ) -> Tuple[List[Product], int]:
        logger.debug(f"Listing products: limit={limit}, offset={offset}")
        products, total = await self.repository.list_products(limit=limit, offset=offset)
        logger.info(f"Retrieved {len(products)} products (total={total})")
        return products, total
