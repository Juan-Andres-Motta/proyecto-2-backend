import logging
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.ports.warehouse_repository_port import WarehouseRepositoryPort
from src.domain.entities.warehouse import Warehouse as DomainWarehouse
from src.infrastructure.database.models import Warehouse as ORMWarehouse

logger = logging.getLogger(__name__)


class WarehouseRepository(WarehouseRepositoryPort):
    """Implementation of WarehouseRepositoryPort for PostgreSQL."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, warehouse_data: dict) -> DomainWarehouse:
        """Create a warehouse and return domain entity."""
        logger.debug(f"DB: Creating warehouse with data: {warehouse_data}")
        try:
            orm_warehouse = ORMWarehouse(**warehouse_data)
            self.session.add(orm_warehouse)
            await self.session.commit()
            await self.session.refresh(orm_warehouse)
            logger.debug(f"DB: Successfully created warehouse: id={orm_warehouse.id}")
            return self._to_domain(orm_warehouse)
        except Exception as e:
            logger.error(f"DB: Create warehouse failed: {e}")
            raise

    async def find_by_id(self, warehouse_id: UUID) -> Optional[DomainWarehouse]:
        """Find a warehouse by ID and return domain entity."""
        logger.debug(f"DB: Finding warehouse by id: warehouse_id={warehouse_id}")
        try:
            stmt = select(ORMWarehouse).where(ORMWarehouse.id == warehouse_id)
            result = await self.session.execute(stmt)
            orm_warehouse = result.scalars().first()
            if orm_warehouse is None:
                logger.debug(f"DB: Warehouse not found: warehouse_id={warehouse_id}")
                return None
            logger.debug(f"DB: Successfully found warehouse: id={orm_warehouse.id}")
            return self._to_domain(orm_warehouse)
        except Exception as e:
            logger.error(f"DB: Find warehouse by id failed: {e}")
            raise

    async def list_warehouses(
        self, limit: int = 10, offset: int = 0
    ) -> Tuple[List[DomainWarehouse], int]:
        """List warehouses with pagination and return domain entities."""
        logger.debug(f"DB: Listing warehouses with limit={limit}, offset={offset}")
        try:
            # Get total count
            count_stmt = select(func.count()).select_from(ORMWarehouse)
            count_result = await self.session.execute(count_stmt)
            total = count_result.scalar()

            # Get paginated data
            stmt = select(ORMWarehouse).limit(limit).offset(offset)
            result = await self.session.execute(stmt)
            orm_warehouses = result.scalars().all()

            logger.debug(f"DB: Successfully listed warehouses: count={len(orm_warehouses)}, total={total}")
            return [self._to_domain(w) for w in orm_warehouses], total
        except Exception as e:
            logger.error(f"DB: List warehouses failed: {e}")
            raise

    @staticmethod
    def _to_domain(orm_warehouse: ORMWarehouse) -> DomainWarehouse:
        """Map ORM model to domain entity."""
        return DomainWarehouse(
            id=orm_warehouse.id,
            name=orm_warehouse.name,
            country=orm_warehouse.country,
            city=orm_warehouse.city,
            address=orm_warehouse.address,
            created_at=orm_warehouse.created_at,
            updated_at=orm_warehouse.updated_at,
        )
