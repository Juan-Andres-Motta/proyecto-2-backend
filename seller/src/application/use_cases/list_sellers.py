from typing import List, Tuple

from src.adapters.output.repositories.seller_repository import SellerRepository
from src.infrastructure.database.models import Seller


class ListSellersUseCase:
    def __init__(self, repository: SellerRepository):
        self.repository = repository

    async def execute(
        self, limit: int | None = 10, offset: int = 0
    ) -> Tuple[List[Seller], int]:
        return await self.repository.list_sellers(limit=limit, offset=offset)
