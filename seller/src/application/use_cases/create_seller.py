from src.adapters.output.repositories.seller_repository import SellerRepository
from src.infrastructure.database.models import Seller


class CreateSellerUseCase:
    def __init__(self, repository: SellerRepository):
        self.repository = repository

    async def execute(self, seller_data: dict) -> Seller:
        return await self.repository.create(seller_data)
