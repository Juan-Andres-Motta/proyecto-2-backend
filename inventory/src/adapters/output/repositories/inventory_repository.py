from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.ports.inventory_repository_port import InventoryRepositoryPort
from src.domain.entities.inventory import Inventory as DomainInventory
from src.infrastructure.database.models import Inventory as ORMInventory


class InventoryRepository(InventoryRepositoryPort):
    """Implementation of InventoryRepositoryPort for PostgreSQL."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, inventory_data: dict) -> DomainInventory:
        """Create an inventory and return domain entity."""
        orm_inventory = ORMInventory(**inventory_data)
        self.session.add(orm_inventory)
        await self.session.commit()
        await self.session.refresh(orm_inventory)
        return self._to_domain(orm_inventory)

    async def find_by_id(self, inventory_id: UUID) -> Optional[DomainInventory]:
        """Find an inventory by ID and return domain entity."""
        stmt = select(ORMInventory).where(ORMInventory.id == inventory_id)
        result = await self.session.execute(stmt)
        orm_inventory = result.scalars().first()
        if orm_inventory is None:
            return None
        return self._to_domain(orm_inventory)

    async def list_inventories(
        self,
        limit: int = 10,
        offset: int = 0,
        product_id: Optional[UUID] = None,
        warehouse_id: Optional[UUID] = None,
        sku: Optional[str] = None,
    ) -> Tuple[List[DomainInventory], int]:
        """List inventories with pagination and filters, return domain entities."""
        # Build base query
        query = select(ORMInventory)
        count_query = select(func.count()).select_from(ORMInventory)

        # Apply filters
        if product_id:
            query = query.where(ORMInventory.product_id == product_id)
            count_query = count_query.where(ORMInventory.product_id == product_id)

        if warehouse_id:
            query = query.where(ORMInventory.warehouse_id == warehouse_id)
            count_query = count_query.where(ORMInventory.warehouse_id == warehouse_id)

        if sku:
            query = query.where(ORMInventory.product_sku == sku)
            count_query = count_query.where(ORMInventory.product_sku == sku)

        # Get total count with filters
        count_result = await self.session.execute(count_query)
        total = count_result.scalar()

        # Get paginated data with filters
        query = query.limit(limit).offset(offset)
        result = await self.session.execute(query)
        orm_inventories = result.scalars().all()

        return [self._to_domain(i) for i in orm_inventories], total

    @staticmethod
    def _to_domain(orm_inventory: ORMInventory) -> DomainInventory:
        """Map ORM model to domain entity."""
        return DomainInventory(
            id=orm_inventory.id,
            product_id=orm_inventory.product_id,
            warehouse_id=orm_inventory.warehouse_id,
            total_quantity=orm_inventory.total_quantity,
            reserved_quantity=orm_inventory.reserved_quantity,
            batch_number=orm_inventory.batch_number,
            expiration_date=orm_inventory.expiration_date,
            product_sku=orm_inventory.product_sku,
            product_name=orm_inventory.product_name,
            warehouse_name=orm_inventory.warehouse_name,
            warehouse_city=orm_inventory.warehouse_city,
            created_at=orm_inventory.created_at,
            updated_at=orm_inventory.updated_at,
        )
