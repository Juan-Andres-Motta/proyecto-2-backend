from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.ports.provider_repository_port import ProviderRepositoryPort
from src.domain.entities.provider import Provider as DomainProvider
from src.infrastructure.database.models import Provider as ORMProvider


class ProviderRepository(ProviderRepositoryPort):
    """Implementation of ProviderRepositoryPort for PostgreSQL."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, provider_data: dict) -> DomainProvider:
        """Create a provider and return domain entity."""
        orm_provider = ORMProvider(**provider_data)
        self.session.add(orm_provider)
        await self.session.commit()
        await self.session.refresh(orm_provider)
        return self._to_domain(orm_provider)

    async def find_by_id(self, provider_id: UUID) -> Optional[DomainProvider]:
        """Find a provider by ID and return domain entity."""
        stmt = select(ORMProvider).where(ORMProvider.id == provider_id)
        result = await self.session.execute(stmt)
        orm_provider = result.scalars().first()

        if orm_provider is None:
            return None

        return self._to_domain(orm_provider)

    async def find_by_nit(self, nit: str) -> Optional[DomainProvider]:
        """Find a provider by NIT and return domain entity."""
        stmt = select(ORMProvider).where(ORMProvider.nit == nit)
        result = await self.session.execute(stmt)
        orm_provider = result.scalars().first()

        if orm_provider is None:
            return None

        return self._to_domain(orm_provider)

    async def find_by_email(self, email: str) -> Optional[DomainProvider]:
        """Find a provider by email and return domain entity."""
        stmt = select(ORMProvider).where(ORMProvider.email == email)
        result = await self.session.execute(stmt)
        orm_provider = result.scalars().first()

        if orm_provider is None:
            return None

        return self._to_domain(orm_provider)

    async def list_providers(
        self, limit: int = 10, offset: int = 0
    ) -> Tuple[List[DomainProvider], int]:
        """List providers and return domain entities."""
        # Get total count
        count_stmt = select(func.count()).select_from(ORMProvider)
        count_result = await self.session.execute(count_stmt)
        total = count_result.scalar()

        # Get paginated data
        stmt = select(ORMProvider).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        orm_providers = result.scalars().all()

        # Map to domain entities
        domain_providers = [self._to_domain(orm) for orm in orm_providers]

        return domain_providers, total

    @staticmethod
    def _to_domain(orm_provider: ORMProvider) -> DomainProvider:
        """Map ORM model to domain entity."""
        return DomainProvider(
            id=orm_provider.id,
            name=orm_provider.name,
            nit=orm_provider.nit,
            contact_name=orm_provider.contact_name,
            email=orm_provider.email,
            phone=orm_provider.phone,
            address=orm_provider.address,
            country=orm_provider.country,
            created_at=orm_provider.created_at,
            updated_at=orm_provider.updated_at
        )
