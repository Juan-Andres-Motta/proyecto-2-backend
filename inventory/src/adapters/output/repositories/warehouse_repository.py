from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.ports.warehouse_repository_port import WarehouseRepositoryPort
from src.domain.entities.warehouse import Warehouse as DomainWarehouse
from src.infrastructure.database.models import Warehouse as ORMWarehouse


class WarehouseRepository(WarehouseRepositoryPort):
    """Implementation of WarehouseRepositoryPort for PostgreSQL."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, warehouse_data: dict) -> DomainWarehouse:
        """Create a warehouse and return domain entity."""
        orm_warehouse = ORMWarehouse(**warehouse_data)
        self.session.add(orm_warehouse)
        await self.session.commit()
        await self.session.refresh(orm_warehouse)
        return self._to_domain(orm_warehouse)

    async def find_by_id(self, warehouse_id: UUID) -> Optional[DomainWarehouse]:
        """Find a warehouse by ID and return domain entity."""
        stmt = select(ORMWarehouse).where(ORMWarehouse.id == warehouse_id)
        result = await self.session.execute(stmt)
        orm_warehouse = result.scalars().first()
        if orm_warehouse is None:
            return None
        return self._to_domain(orm_warehouse)

    async def list_warehouses(
        self, limit: int = 10, offset: int = 0
    ) -> Tuple[List[DomainWarehouse], int]:
        """List warehouses with pagination and return domain entities."""
        # Get total count
        count_stmt = select(func.count()).select_from(ORMWarehouse)
        count_result = await self.session.execute(count_stmt)
        total = count_result.scalar()

        # Get paginated data
        stmt = select(ORMWarehouse).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        orm_warehouses = result.scalars().all()

        return [self._to_domain(w) for w in orm_warehouses], total

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
