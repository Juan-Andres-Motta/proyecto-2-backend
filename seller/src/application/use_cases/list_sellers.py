import logging
from typing import List, Tuple

from src.adapters.output.repositories.seller_repository import SellerRepository
from src.infrastructure.database.models import Seller

logger = logging.getLogger(__name__)


class ListSellersUseCase:
    def __init__(self, repository: SellerRepository):
        self.repository = repository

    async def execute(
        self, limit: int | None = 10, offset: int = 0
    ) -> Tuple[List[Seller], int]:
        logger.info(f"Listing sellers: limit={limit}, offset={offset}")

        sellers, total = await self.repository.list_sellers(limit=limit, offset=offset)

        logger.info(f"Sellers retrieved successfully: count={len(sellers)}, total={total}")
        logger.debug(f"Retrieved seller IDs: {[str(s.id) for s in sellers]}")
        return sellers, total
