from typing import List, Tuple

from src.adapters.output.repositories.store_repository import StoreRepository
from src.infrastructure.database.models import Store


class ListStoresUseCase:
    def __init__(self, repository: StoreRepository):
        self.repository = repository

    async def execute(
        self, limit: int = 10, offset: int = 0
    ) -> Tuple[List[Store], int]:
        return await self.repository.list_stores(limit=limit, offset=offset)
