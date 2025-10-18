import logging

from src.adapters.output.repositories.seller_repository import SellerRepository
from src.infrastructure.database.models import Seller

logger = logging.getLogger(__name__)


class CreateSellerUseCase:
    def __init__(self, repository: SellerRepository):
        self.repository = repository

    async def execute(self, seller_data: dict) -> Seller:
        logger.info(f"Creating seller: name={seller_data.get('name')}, email={seller_data.get('email')}")
        logger.debug(f"Full seller data: {seller_data}")

        seller = await self.repository.create(seller_data)

        logger.info(f"Seller created successfully: id={seller.id}, name={seller.name}")
        return seller
