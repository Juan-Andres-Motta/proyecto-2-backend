from typing import List, Tuple

from src.adapters.output.repositories.provider_repository import ProviderRepository
from src.infrastructure.database.models import Provider


class ListProvidersUseCase:
    def __init__(self, repository: ProviderRepository):
        self.repository = repository

    async def execute(
        self, limit: int = 10, offset: int = 0
    ) -> Tuple[List[Provider], int]:
        return await self.repository.list_providers(limit=limit, offset=offset)
