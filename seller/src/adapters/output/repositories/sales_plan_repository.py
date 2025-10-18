import logging
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.application.ports.sales_plan_repository_port import SalesPlanRepositoryPort
from src.domain.entities.sales_plan import SalesPlan as DomainSalesPlan
from src.domain.entities.seller import Seller as DomainSeller
from src.infrastructure.database.models import SalesPlan as ORMSalesPlan

logger = logging.getLogger(__name__)


class SalesPlanRepository(SalesPlanRepositoryPort):
    """Implementation of SalesPlanRepositoryPort for PostgreSQL."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, sales_plan: DomainSalesPlan) -> DomainSalesPlan:
        """Create a new sales plan from domain entity."""
        logger.debug(f"DB: Creating sales plan: seller_id={sales_plan.seller.id}, period={sales_plan.sales_period}, goal={sales_plan.goal}")

        try:
            # Map domain entity to ORM model
            orm_sales_plan = ORMSalesPlan(
                id=sales_plan.id,
                seller_id=sales_plan.seller.id,
                sales_period=sales_plan.sales_period,
                goal=sales_plan.goal,
                accumulate=sales_plan.accumulate,
                created_at=sales_plan.created_at,
                updated_at=sales_plan.updated_at
            )

            self.session.add(orm_sales_plan)
            await self.session.commit()

            # Eager load seller for return
            await self.session.refresh(orm_sales_plan, ['seller'])

            logger.debug(f"DB: Successfully created sales plan: id={orm_sales_plan.id}, seller_id={sales_plan.seller.id}, period={sales_plan.sales_period}")
            return self._to_domain(orm_sales_plan)
        except Exception as e:
            logger.error(f"DB: Create sales plan failed: seller_id={sales_plan.seller.id}, period={sales_plan.sales_period}, error={e}")
            await self.session.rollback()
            raise

    async def find_by_seller_and_period(
        self,
        seller_id: UUID,
        sales_period: str
    ) -> Optional[DomainSalesPlan]:
        """Find sales plan by seller and period."""
        logger.debug(f"DB: Finding sales plan by seller and period: seller_id={seller_id}, period={sales_period}")

        try:
            stmt = (
                select(ORMSalesPlan)
                .options(selectinload(ORMSalesPlan.seller))
                .where(
                    ORMSalesPlan.seller_id == seller_id,
                    ORMSalesPlan.sales_period == sales_period
                )
            )

            result = await self.session.execute(stmt)
            orm_sales_plan = result.scalars().first()

            if orm_sales_plan is None:
                logger.debug(f"DB: Sales plan not found: seller_id={seller_id}, period={sales_period}")
                return None

            logger.debug(f"DB: Successfully found sales plan: id={orm_sales_plan.id}, seller_id={seller_id}, period={sales_period}")
            return self._to_domain(orm_sales_plan)
        except Exception as e:
            logger.error(f"DB: Find sales plan by seller and period failed: seller_id={seller_id}, period={sales_period}, error={e}")
            raise

    async def list_sales_plans(
        self,
        limit: int = 10,
        offset: int = 0
    ) -> Tuple[List[DomainSalesPlan], int]:
        """List sales plans with eager-loaded sellers."""
        logger.debug(f"DB: Listing sales plans with limit={limit}, offset={offset}")

        try:
            # Get total count
            count_stmt = select(func.count()).select_from(ORMSalesPlan)
            count_result = await self.session.execute(count_stmt)
            total = count_result.scalar()

            # Get paginated data with eager loading
            stmt = (
                select(ORMSalesPlan)
                .options(selectinload(ORMSalesPlan.seller))  # Eager load seller
                .limit(limit)
                .offset(offset)
            )
            result = await self.session.execute(stmt)
            orm_sales_plans = result.scalars().all()

            # Map to domain entities
            domain_sales_plans = [
                self._to_domain(orm_plan) for orm_plan in orm_sales_plans
            ]

            logger.debug(f"DB: Successfully listed sales plans: count={len(domain_sales_plans)}, total={total}")
            return domain_sales_plans, total
        except Exception as e:
            logger.error(f"DB: List sales plans failed: limit={limit}, offset={offset}, error={e}")
            raise

    async def list_sales_plans_by_seller(
        self,
        seller_id: UUID,
        limit: int = 10,
        offset: int = 0
    ) -> Tuple[List[DomainSalesPlan], int]:
        """List sales plans for a specific seller with eager-loaded seller data."""
        logger.debug(f"DB: Listing sales plans by seller: seller_id={seller_id}, limit={limit}, offset={offset}")

        try:
            # Get total count for this seller
            count_stmt = (
                select(func.count())
                .select_from(ORMSalesPlan)
                .where(ORMSalesPlan.seller_id == seller_id)
            )
            count_result = await self.session.execute(count_stmt)
            total = count_result.scalar()

            # Get paginated data with eager loading
            stmt = (
                select(ORMSalesPlan)
                .options(selectinload(ORMSalesPlan.seller))  # Eager load seller
                .where(ORMSalesPlan.seller_id == seller_id)
                .limit(limit)
                .offset(offset)
            )
            result = await self.session.execute(stmt)
            orm_sales_plans = result.scalars().all()

            # Map to domain entities
            domain_sales_plans = [
                self._to_domain(orm_plan) for orm_plan in orm_sales_plans
            ]

            logger.debug(f"DB: Successfully listed sales plans by seller: seller_id={seller_id}, count={len(domain_sales_plans)}, total={total}")
            return domain_sales_plans, total
        except Exception as e:
            logger.error(f"DB: List sales plans by seller failed: seller_id={seller_id}, limit={limit}, offset={offset}, error={e}")
            raise

    @staticmethod
    def _to_domain(orm_sales_plan: ORMSalesPlan) -> DomainSalesPlan:
        """Map ORM model to domain entity with nested Seller."""
        # Map seller
        domain_seller = DomainSeller(
            id=orm_sales_plan.seller.id,
            name=orm_sales_plan.seller.name,
            email=orm_sales_plan.seller.email,
            phone=orm_sales_plan.seller.phone,
            city=orm_sales_plan.seller.city,
            country=orm_sales_plan.seller.country,
            created_at=orm_sales_plan.seller.created_at,
            updated_at=orm_sales_plan.seller.updated_at
        )

        # Map sales plan with embedded seller
        return DomainSalesPlan(
            id=orm_sales_plan.id,
            seller=domain_seller,
            sales_period=orm_sales_plan.sales_period,
            goal=orm_sales_plan.goal,
            accumulate=orm_sales_plan.accumulate,
            created_at=orm_sales_plan.created_at,
            updated_at=orm_sales_plan.updated_at
        )
