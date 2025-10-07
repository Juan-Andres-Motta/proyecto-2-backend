from src.adapters.output.repositories.store_repository import StoreRepository
from src.infrastructure.database.models import Store


class CreateStoreUseCase:
    def __init__(self, repository: StoreRepository):
        self.repository = repository

    async def execute(self, store_data: dict) -> Store:
        return await self.repository.create(store_data)
