import logging
from typing import List, Optional, Set, Tuple
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from src.application.ports.product_repository_port import ProductRepositoryPort
from src.domain.entities.product import Product as DomainProduct
from src.infrastructure.database.models import Product as ORMProduct

logger = logging.getLogger(__name__)


class ProductRepository(ProductRepositoryPort):
    """Implementation of ProductRepositoryPort for PostgreSQL."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def batch_create(self, products_data: List[dict]) -> List[DomainProduct]:
        """
        Create multiple products in a single transaction.
        If any product fails, all creations are rolled back.

        Args:
            products_data: List of dictionaries containing product data

        Returns:
            List of created Product domain entities

        Raises:
            SQLAlchemyError: If any product creation fails
        """
        logger.debug(f"DB: Batch creating {len(products_data)} products")
        created_products = []

        try:
            # Create all products
            for product_data in products_data:
                product = ORMProduct(**product_data)
                self.session.add(product)
                created_products.append(product)

            # Commit the transaction
            await self.session.commit()

            # Refresh all products to get generated IDs and timestamps
            for product in created_products:
                await self.session.refresh(product)

            logger.debug(f"DB: Successfully batch created {len(created_products)} products")
            # Map to domain entities
            return [self._to_domain(orm) for orm in created_products]

        except SQLAlchemyError as e:
            # Rollback on any error
            logger.error(f"DB: Batch product creation failed, rolling back: {str(e)}")
            await self.session.rollback()
            raise e

    async def find_by_id(self, product_id: UUID) -> Optional[DomainProduct]:
        """Find a product by ID and return domain entity."""
        logger.debug(f"DB: Finding product by ID: product_id={product_id}")
        stmt = select(ORMProduct).where(ORMProduct.id == product_id)
        result = await self.session.execute(stmt)
        orm_product = result.scalars().first()

        if orm_product is None:
            logger.debug(f"DB: Product not found: product_id={product_id}")
            return None

        logger.debug(f"DB: Product found: product_id={product_id}, sku='{orm_product.sku}'")
        return self._to_domain(orm_product)

    async def find_by_sku(self, sku: str) -> Optional[DomainProduct]:
        """Find a product by SKU and return domain entity."""
        stmt = select(ORMProduct).where(ORMProduct.sku == sku)
        result = await self.session.execute(stmt)
        orm_product = result.scalars().first()

        if orm_product is None:
            return None

        return self._to_domain(orm_product)

    async def find_existing_skus(self, skus: List[str]) -> Set[str]:
        """Find which SKUs already exist in database.

        Args:
            skus: List of SKUs to check

        Returns:
            Set of SKUs that already exist
        """
        if not skus:
            return set()

        stmt = select(ORMProduct.sku).where(ORMProduct.sku.in_(skus))
        result = await self.session.execute(stmt)
        existing_skus = result.scalars().all()

        return set(existing_skus)

    async def list_products(
        self, limit: int = 10, offset: int = 0
    ) -> Tuple[List[DomainProduct], int]:
        """List products and return domain entities."""
        logger.debug(f"DB: Listing products with limit={limit}, offset={offset}")
        # Get total count
        count_stmt = select(func.count()).select_from(ORMProduct)
        count_result = await self.session.execute(count_stmt)
        total = count_result.scalar()

        # Get paginated data
        stmt = select(ORMProduct).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        orm_products = result.scalars().all()

        # Map to domain entities
        domain_products = [self._to_domain(orm) for orm in orm_products]
        logger.debug(f"DB: Retrieved {len(domain_products)} products from database")

        return domain_products, total

    @staticmethod
    def _to_domain(orm_product: ORMProduct) -> DomainProduct:
        """Map ORM model to domain entity."""
        return DomainProduct(
            id=orm_product.id,
            provider_id=orm_product.provider_id,
            name=orm_product.name,
            category=orm_product.category,
            sku=orm_product.sku,
            price=orm_product.price,
            created_at=orm_product.created_at,
            updated_at=orm_product.updated_at
        )
