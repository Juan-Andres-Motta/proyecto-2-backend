from typing import List, Tuple

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.models import Provider


class ProviderRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, provider_data: dict) -> Provider:
        provider = Provider(**provider_data)
        self.session.add(provider)
        await self.session.commit()
        await self.session.refresh(provider)
        return provider

    async def list_providers(
        self, limit: int = 10, offset: int = 0
    ) -> Tuple[List[Provider], int]:
        # Get total count
        count_stmt = select(func.count()).select_from(Provider)
        count_result = await self.session.execute(count_stmt)
        total = count_result.scalar()

        # Get paginated data
        stmt = select(Provider).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        providers = result.scalars().all()

        return providers, total
