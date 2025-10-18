"""
Port interface for Catalog microservice operations.

This defines the contract for provider and product management operations
without specifying how the communication is implemented.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from web.schemas.catalog_schemas import (
    BatchProductsResponse,
    PaginatedProductsResponse,
    PaginatedProvidersResponse,
    ProductCreate,
    ProductResponse,
    ProviderCreate,
    ProviderCreateResponse,
)


class CatalogPort(ABC):
    """
    Abstract port interface for catalog operations.

    Implementations of this port handle communication with the catalog
    microservice for provider and product management.
    """

    @abstractmethod
    async def create_provider(self, provider_data: ProviderCreate) -> ProviderCreateResponse:
        """
        Create a new provider in the catalog.

        Args:
            provider_data: The provider information to create

        Returns:
            ProviderCreateResponse with the created provider ID

        Raises:
            MicroserviceValidationError: If the provider data is invalid
            MicroserviceConnectionError: If unable to connect to the catalog service
            MicroserviceHTTPError: If the catalog service returns an error
        """
        pass

    @abstractmethod
    async def get_providers(
        self, limit: int = 10, offset: int = 0
    ) -> PaginatedProvidersResponse:
        """
        Retrieve a paginated list of providers.

        Args:
            limit: Maximum number of providers to return
            offset: Number of providers to skip

        Returns:
            PaginatedProvidersResponse with provider data

        Raises:
            MicroserviceConnectionError: If unable to connect to the catalog service
            MicroserviceHTTPError: If the catalog service returns an error
        """
        pass

    @abstractmethod
    async def create_products(self, products: List[ProductCreate]) -> BatchProductsResponse:
        """
        Create multiple products in the catalog.

        Args:
            products: List of product data to create

        Returns:
            BatchProductsResponse with created products

        Raises:
            MicroserviceValidationError: If any product data is invalid
            MicroserviceConnectionError: If unable to connect to the catalog service
            MicroserviceHTTPError: If the catalog service returns an error
        """
        pass

    @abstractmethod
    async def get_products(
        self, limit: int = 10, offset: int = 0
    ) -> PaginatedProductsResponse:
        """
        Retrieve a paginated list of products.

        Args:
            limit: Maximum number of products to return
            offset: Number of products to skip

        Returns:
            PaginatedProductsResponse with product data

        Raises:
            MicroserviceConnectionError: If unable to connect to the catalog service
            MicroserviceHTTPError: If the catalog service returns an error
        """
        pass

    @abstractmethod
    async def get_product_by_id(self, product_id: UUID) -> Optional[ProductResponse]:
        """
        Retrieve a single product by its ID.

        Args:
            product_id: UUID of the product to retrieve

        Returns:
            ProductResponse if found, None otherwise

        Raises:
            MicroserviceConnectionError: If unable to connect to the catalog service
            MicroserviceHTTPError: If the catalog service returns an error
        """
        pass
