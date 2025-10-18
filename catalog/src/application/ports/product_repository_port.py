"""Product repository port (interface)."""
from abc import ABC, abstractmethod
from typing import List, Optional, Set, Tuple
from uuid import UUID

from src.domain.entities.product import Product


class ProductRepositoryPort(ABC):
    """Port for product repository operations.

    Defined by application layer needs.
    Implemented by infrastructure layer.
    """

    @abstractmethod
    async def batch_create(self, products_data: List[dict]) -> List[Product]:
        """Create multiple products in a batch.

        Args:
            products_data: List of dictionaries with product information

        Returns:
            List of created Product domain entities

        Raises:
            BatchProductCreationException: If any product fails validation
        """
        ...  # pragma: no cover

    @abstractmethod
    async def find_by_id(self, product_id: UUID) -> Optional[Product]:
        """Find a product by ID.

        Args:
            product_id: UUID of the product

        Returns:
            Product domain entity if found, None otherwise
        """
        ...  # pragma: no cover

    @abstractmethod
    async def find_by_sku(self, sku: str) -> Optional[Product]:
        """Find a product by SKU.

        Args:
            sku: SKU (unique identifier) of the product

        Returns:
            Product domain entity if found, None otherwise
        """
        ...  # pragma: no cover

    @abstractmethod
    async def find_existing_skus(self, skus: List[str]) -> Set[str]:
        """Find which SKUs already exist in database.

        Args:
            skus: List of SKUs to check

        Returns:
            Set of SKUs that already exist
        """
        ...  # pragma: no cover

    @abstractmethod
    async def list_products(
        self, limit: int = 10, offset: int = 0
    ) -> Tuple[List[Product], int]:
        """List products with pagination.

        Args:
            limit: Maximum number of products to return
            offset: Number of products to skip

        Returns:
            Tuple of (list of products, total count)
        """
        ...  # pragma: no cover
