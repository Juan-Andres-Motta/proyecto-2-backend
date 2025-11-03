import logging
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.ports.seller_repository_port import SellerRepositoryPort
from src.domain.entities.seller import Seller as DomainSeller
from src.infrastructure.database.models import Seller as ORMSeller

logger = logging.getLogger(__name__)


class SellerRepository(SellerRepositoryPort):
    """Implementation of SellerRepositoryPort for PostgreSQL."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def find_by_id(self, seller_id: UUID) -> Optional[DomainSeller]:
        """Find a seller by ID and return domain entity."""
        logger.debug(f"DB: Finding seller by ID: seller_id={seller_id}")

        try:
            stmt = select(ORMSeller).where(ORMSeller.id == seller_id)
            result = await self.session.execute(stmt)
            orm_seller = result.scalars().first()

            if orm_seller is None:
                logger.debug(f"DB: Seller not found: seller_id={seller_id}")
                return None

            logger.debug(f"DB: Successfully found seller: seller_id={seller_id}, name={orm_seller.name}")
            return self._to_domain(orm_seller)
        except Exception as e:
            logger.error(f"DB: Find seller by ID failed: seller_id={seller_id}, error={e}")
            raise

    async def find_by_cognito_user_id(self, cognito_user_id: str) -> Optional[DomainSeller]:
        """Find a seller by Cognito User ID and return domain entity."""
        logger.debug(f"DB: Finding seller by cognito_user_id={cognito_user_id}")

        try:
            stmt = select(ORMSeller).where(ORMSeller.cognito_user_id == cognito_user_id)
            result = await self.session.execute(stmt)
            orm_seller = result.scalars().first()

            if orm_seller is None:
                logger.debug(f"DB: Seller not found: cognito_user_id={cognito_user_id}")
                return None

            logger.debug(f"DB: Successfully found seller: cognito_user_id={cognito_user_id}, id={orm_seller.id}")
            return self._to_domain(orm_seller)
        except Exception as e:
            logger.error(f"DB: Find seller by cognito_user_id failed: cognito_user_id={cognito_user_id}, error={e}")
            raise

    async def create(self, seller_data: dict) -> ORMSeller:
        """Create a seller (returns ORM model for backward compatibility)."""
        logger.debug(f"DB: Creating seller with data: name={seller_data.get('name')}, email={seller_data.get('email')}")

        try:
            seller = ORMSeller(**seller_data)
            self.session.add(seller)
            await self.session.commit()
            await self.session.refresh(seller)

            logger.debug(f"DB: Successfully created seller: id={seller.id}, name={seller.name}")
            return seller
        except Exception as e:
            logger.error(f"DB: Create seller failed: name={seller_data.get('name')}, error={e}")
            await self.session.rollback()
            raise

    async def list_sellers(
        self, limit: int = 10, offset: int = 0
    ) -> Tuple[List[ORMSeller], int]:
        """List sellers (returns ORM models for backward compatibility)."""
        logger.debug(f"DB: Listing sellers with limit={limit}, offset={offset}")

        try:
            # Get total count
            count_stmt = select(func.count()).select_from(ORMSeller)
            count_result = await self.session.execute(count_stmt)
            total = count_result.scalar()

            # Get data
            stmt = select(ORMSeller).limit(limit).offset(offset)
            result = await self.session.execute(stmt)
            sellers = result.scalars().all()

            logger.debug(f"DB: Successfully listed sellers: count={len(sellers)}, total={total}")
            return sellers, total
        except Exception as e:
            logger.error(f"DB: List sellers failed: limit={limit}, offset={offset}, error={e}")
            raise

    @staticmethod
    def _to_domain(orm_seller: ORMSeller) -> DomainSeller:
        """Map ORM model to domain entity."""
        return DomainSeller(
            id=orm_seller.id,
            cognito_user_id=orm_seller.cognito_user_id,
            name=orm_seller.name,
            email=orm_seller.email,
            phone=orm_seller.phone,
            city=orm_seller.city,
            country=orm_seller.country,
            created_at=orm_seller.created_at,
            updated_at=orm_seller.updated_at
        )
