from typing import List, Tuple

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from src.infrastructure.database.models import Product


class ProductRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def batch_create(self, products_data: List[dict]) -> List[Product]:
        """
        Create multiple products in a single transaction.
        If any product fails, all creations are rolled back.

        Args:
            products_data: List of dictionaries containing product data

        Returns:
            List of created Product objects

        Raises:
            SQLAlchemyError: If any product creation fails
        """
        created_products = []

        try:
            # Create all products
            for product_data in products_data:
                product = Product(**product_data)
                self.session.add(product)
                created_products.append(product)

            # Commit the transaction
            await self.session.commit()

            # Refresh all products to get generated IDs and timestamps
            for product in created_products:
                await self.session.refresh(product)

            return created_products

        except SQLAlchemyError as e:
            # Rollback on any error
            await self.session.rollback()
            raise e

    async def list_products(
        self, limit: int = 10, offset: int = 0
    ) -> Tuple[List[Product], int]:
        # Get total count
        count_stmt = select(func.count()).select_from(Product)
        count_result = await self.session.execute(count_stmt)
        total = count_result.scalar()

        # Get paginated data
        stmt = select(Product).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        products = result.scalars().all()

        return products, total
