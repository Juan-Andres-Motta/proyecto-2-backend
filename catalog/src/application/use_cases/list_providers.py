import logging
from typing import List, Tuple

from src.application.ports.provider_repository_port import ProviderRepositoryPort
from src.domain.entities.provider import Provider

logger = logging.getLogger(__name__)


class ListProvidersUseCase:
    def __init__(self, repository: ProviderRepositoryPort):
        self.repository = repository

    async def execute(
        self, limit: int = 10, offset: int = 0
    ) -> Tuple[List[Provider], int]:
        logger.debug(f"Listing providers: limit={limit}, offset={offset}")
        providers, total = await self.repository.list_providers(limit=limit, offset=offset)
        logger.info(f"Retrieved {len(providers)} providers (total={total})")
        return providers, total
