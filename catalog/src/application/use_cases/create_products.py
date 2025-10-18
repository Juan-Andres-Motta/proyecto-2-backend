"""Create products use case with validation logic."""
from decimal import Decimal
from typing import List

from src.application.ports.product_repository_port import ProductRepositoryPort
from src.application.ports.provider_repository_port import ProviderRepositoryPort
from src.domain.entities.product import Product
from src.domain.exceptions import (
    BatchProductCreationException,
    PriceMustBePositiveException,
    ProviderNotFoundException,
)


class CreateProductsUseCase:
    """Use case for creating products in batch with validation."""

    def __init__(
        self,
        product_repository: ProductRepositoryPort,
        provider_repository: ProviderRepositoryPort
    ):
        """Initialize with repository ports (dependency injection).

        Args:
            product_repository: Port for product persistence
            provider_repository: Port for provider queries
        """
        self.product_repo = product_repository
        self.provider_repo = provider_repository

    async def execute(self, products_data: List[dict]) -> List[Product]:
        """
        Create multiple products in a batch with validation.

        Validation rules (stop on first failure):
        1. Each product's provider must exist
        2. Each product's price must be > 0
        3. Each product's SKU must be unique (not exist in DB)
        4. SKUs within batch must be unique

        Args:
            products_data: List of dictionaries containing product data

        Returns:
            List of created Product domain entities

        Raises:
            BatchProductCreationException: If any product fails validation
            ProviderNotFoundException: If provider doesn't exist
            PriceMustBePositiveException: If price <= 0
        """
        # Collect all provider IDs and SKUs for batch validation
        provider_ids = set()
        skus_in_batch = []

        for idx, product_data in enumerate(products_data):
            provider_ids.add(product_data.get("provider_id"))
            skus_in_batch.append(product_data.get("sku"))

        # Validation 1: Check all providers exist (batch query)
        for idx, product_data in enumerate(products_data):
            provider_id = product_data.get("provider_id")
            provider = await self.provider_repo.find_by_id(provider_id)
            if provider is None:
                raise BatchProductCreationException(
                    index=idx,
                    product_data=product_data,
                    error_message=f"Provider {provider_id} not found"
                )

        # Validation 2: Check all prices are positive
        for idx, product_data in enumerate(products_data):
            price = product_data.get("price")
            if price is None or Decimal(str(price)) <= 0:
                raise BatchProductCreationException(
                    index=idx,
                    product_data=product_data,
                    error_message=f"Price must be greater than 0, got {price}"
                )

        # Validation 3: Check SKUs are unique within batch
        seen_skus = set()
        for idx, sku in enumerate(skus_in_batch):
            if sku in seen_skus:
                raise BatchProductCreationException(
                    index=idx,
                    product_data=products_data[idx],
                    error_message=f"Duplicate SKU '{sku}' within batch"
                )
            seen_skus.add(sku)

        # Validation 4: Check SKUs don't exist in database (batch query)
        existing_skus = await self.product_repo.find_existing_skus(skus_in_batch)
        for idx, sku in enumerate(skus_in_batch):
            if sku in existing_skus:
                raise BatchProductCreationException(
                    index=idx,
                    product_data=products_data[idx],
                    error_message=f"Product with SKU '{sku}' already exists"
                )

        # All validations passed - create products
        return await self.product_repo.batch_create(products_data)
