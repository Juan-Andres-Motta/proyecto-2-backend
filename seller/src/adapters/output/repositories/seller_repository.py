from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.ports.seller_repository_port import SellerRepositoryPort
from src.domain.entities.seller import Seller as DomainSeller
from src.infrastructure.database.models import Seller as ORMSeller


class SellerRepository(SellerRepositoryPort):
    """Implementation of SellerRepositoryPort for PostgreSQL."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def find_by_id(self, seller_id: UUID) -> Optional[DomainSeller]:
        """Find a seller by ID and return domain entity."""
        stmt = select(ORMSeller).where(ORMSeller.id == seller_id)
        result = await self.session.execute(stmt)
        orm_seller = result.scalars().first()

        if orm_seller is None:
            return None

        return self._to_domain(orm_seller)

    async def create(self, seller_data: dict) -> ORMSeller:
        """Create a seller (returns ORM model for backward compatibility)."""
        seller = ORMSeller(**seller_data)
        self.session.add(seller)
        await self.session.commit()
        await self.session.refresh(seller)
        return seller

    async def list_sellers(
        self, limit: int = 10, offset: int = 0
    ) -> Tuple[List[ORMSeller], int]:
        """List sellers (returns ORM models for backward compatibility)."""
        # Get total count
        count_stmt = select(func.count()).select_from(ORMSeller)
        count_result = await self.session.execute(count_stmt)
        total = count_result.scalar()

        # Get data
        stmt = select(ORMSeller).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        sellers = result.scalars().all()

        return sellers, total

    @staticmethod
    def _to_domain(orm_seller: ORMSeller) -> DomainSeller:
        """Map ORM model to domain entity."""
        return DomainSeller(
            id=orm_seller.id,
            name=orm_seller.name,
            email=orm_seller.email,
            phone=orm_seller.phone,
            city=orm_seller.city,
            country=orm_seller.country,
            created_at=orm_seller.created_at,
            updated_at=orm_seller.updated_at
        )
