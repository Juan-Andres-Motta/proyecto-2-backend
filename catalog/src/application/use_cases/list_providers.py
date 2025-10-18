from typing import List, Tuple

from src.application.ports.provider_repository_port import ProviderRepositoryPort
from src.domain.entities.provider import Provider


class ListProvidersUseCase:
    def __init__(self, repository: ProviderRepositoryPort):
        self.repository = repository

    async def execute(
        self, limit: int = 10, offset: int = 0
    ) -> Tuple[List[Provider], int]:
        return await self.repository.list_providers(limit=limit, offset=offset)
