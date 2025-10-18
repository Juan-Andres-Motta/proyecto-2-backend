import logging
from typing import Optional
from uuid import UUID

from src.application.ports.product_repository_port import ProductRepositoryPort
from src.domain.entities.product import Product

logger = logging.getLogger(__name__)


class GetProductUseCase:
    def __init__(self, repository: ProductRepositoryPort):
        self.repository = repository

    async def execute(self, product_id: UUID) -> Optional[Product]:
        logger.debug(f"Getting product: product_id={product_id}")
        product = await self.repository.find_by_id(product_id)

        if product:
            logger.info(f"Product found: product_id={product_id}, sku='{product.sku}'")
        else:
            logger.info(f"Product not found: product_id={product_id}")

        return product
