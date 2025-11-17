import logging
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.ports.inventory_repository_port import InventoryRepositoryPort
from src.domain.entities.inventory import Inventory as DomainInventory
from src.domain.exceptions import (
    InsufficientInventoryException,
    InvalidReservationReleaseException,
    InventoryNotFoundException,
)
from src.infrastructure.database.models import Inventory as ORMInventory

logger = logging.getLogger(__name__)


class InventoryRepository(InventoryRepositoryPort):
    """Implementation of InventoryRepositoryPort for PostgreSQL."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, inventory_data: dict) -> DomainInventory:
        """Create an inventory and return domain entity."""
        logger.debug(
            f"DB: Creating inventory with data: product_id={inventory_data.get('product_id')}, warehouse_id={inventory_data.get('warehouse_id')}"
        )
        try:
            orm_inventory = ORMInventory(**inventory_data)
            self.session.add(orm_inventory)
            await self.session.commit()
            await self.session.refresh(orm_inventory)
            logger.debug(f"DB: Successfully created inventory: id={orm_inventory.id}")
            return self._to_domain(orm_inventory)
        except Exception as e:
            logger.error(f"DB: Create inventory failed: {e}")
            raise

    async def find_by_id(self, inventory_id: UUID) -> Optional[DomainInventory]:
        """Find an inventory by ID and return domain entity."""
        logger.debug(f"DB: Finding inventory by id: inventory_id={inventory_id}")
        try:
            stmt = select(ORMInventory).where(ORMInventory.id == inventory_id)
            result = await self.session.execute(stmt)
            orm_inventory = result.scalars().first()
            if orm_inventory is None:
                logger.debug(f"DB: Inventory not found: inventory_id={inventory_id}")
                return None
            logger.debug(f"DB: Successfully found inventory: id={orm_inventory.id}")
            return self._to_domain(orm_inventory)
        except Exception as e:
            logger.error(f"DB: Find inventory by id failed: {e}")
            raise

    async def list_inventories(
        self,
        limit: int = 10,
        offset: int = 0,
        product_id: Optional[UUID] = None,
        warehouse_id: Optional[UUID] = None,
        sku: Optional[str] = None,
        category: Optional[str] = None,
        name: Optional[str] = None,
    ) -> Tuple[List[DomainInventory], int]:
        """List inventories with pagination and filters, return domain entities."""
        logger.debug(
            f"DB: Listing inventories with limit={limit}, offset={offset}, product_id={product_id}, warehouse_id={warehouse_id}, sku={sku}, category={category}, name={name}"
        )
        try:
            # Build base query
            query = select(ORMInventory)
            count_query = select(func.count()).select_from(ORMInventory)

            # Apply filters
            if product_id:
                logger.debug(f"DB: Applying product_id filter: {product_id}")
                query = query.where(ORMInventory.product_id == product_id)
                count_query = count_query.where(ORMInventory.product_id == product_id)

            if warehouse_id:
                logger.debug(f"DB: Applying warehouse_id filter: {warehouse_id}")
                query = query.where(ORMInventory.warehouse_id == warehouse_id)
                count_query = count_query.where(
                    ORMInventory.warehouse_id == warehouse_id
                )

            if sku:
                logger.debug(f"DB: Applying sku filter: {sku}")
                query = query.where(ORMInventory.product_sku.ilike(f"%{sku}%"))
                count_query = count_query.where(ORMInventory.product_sku.ilike(f"%{sku}%"))

            if category:
                logger.debug(f"DB: Applying category filter: {category}")
                query = query.where(ORMInventory.product_category == category)
                count_query = count_query.where(
                    ORMInventory.product_category == category
                )

            if name:
                logger.debug(f"DB: Applying name filter: {name}")
                query = query.where(ORMInventory.product_name.ilike(f"%{name}%"))
                count_query = count_query.where(
                    ORMInventory.product_name.ilike(f"%{name}%")
                )

            # Get total count with filters
            count_result = await self.session.execute(count_query)
            total = count_result.scalar()

            # Get paginated data with filters, ordered by product name
            query = query.order_by(ORMInventory.product_name).limit(limit).offset(offset)
            result = await self.session.execute(query)
            orm_inventories = result.scalars().all()

            logger.debug(
                f"DB: Successfully listed inventories: count={len(orm_inventories)}, total={total}"
            )
            return [self._to_domain(i) for i in orm_inventories], total
        except Exception as e:
            logger.error(f"DB: List inventories failed: {e}")
            raise

    async def update_reserved_quantity(
        self, inventory_id: UUID, quantity_delta: int
    ) -> DomainInventory:
        """Update reserved quantity atomically with SELECT FOR UPDATE."""
        logger.debug(
            f"DB: Updating reserved quantity: inventory_id={inventory_id}, quantity_delta={quantity_delta}"
        )

        try:
            # SELECT FOR UPDATE to lock the row
            stmt = (
                select(ORMInventory)
                .where(ORMInventory.id == inventory_id)
                .with_for_update()
            )
            result = await self.session.execute(stmt)
            orm_inventory = result.scalars().first()

            if orm_inventory is None:
                raise InventoryNotFoundException(inventory_id)

            # Convert to domain entity
            domain_inventory = self._to_domain(orm_inventory)

            # Apply business logic (validates constraints)
            domain_inventory.adjust_reservation(quantity_delta)

            # Update ORM model
            orm_inventory.reserved_quantity = domain_inventory.reserved_quantity

            # Commit transaction
            await self.session.commit()
            await self.session.refresh(orm_inventory)

            logger.debug(
                f"DB: Successfully updated: new_reserved={orm_inventory.reserved_quantity}"
            )

            return self._to_domain(orm_inventory)

        except (
            InventoryNotFoundException,
            InsufficientInventoryException,
            InvalidReservationReleaseException,
        ):
            raise
        except Exception as e:
            logger.error(f"DB: Update failed: {e}")
            await self.session.rollback()
            raise

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
            product_price=orm_inventory.product_price,
            product_category=orm_inventory.product_category,
            warehouse_name=orm_inventory.warehouse_name,
            warehouse_city=orm_inventory.warehouse_city,
            warehouse_country=orm_inventory.warehouse_country,
            created_at=orm_inventory.created_at,
            updated_at=orm_inventory.updated_at,
        )
