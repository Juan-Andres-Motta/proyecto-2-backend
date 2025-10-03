from src.adapters.output.repositories.provider_repository import ProviderRepository
from src.infrastructure.database.models import Provider


class CreateProviderUseCase:
    def __init__(self, repository: ProviderRepository):
        self.repository = repository

    async def execute(self, provider_data: dict) -> Provider:
        return await self.repository.create(provider_data)
