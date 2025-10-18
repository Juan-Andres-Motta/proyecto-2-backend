"""
Catalog adapter implementation.

This adapter implements the CatalogPort interface using HTTP communication.
"""

from typing import List, Optional
from uuid import UUID

from ..ports.catalog_port import CatalogPort
from ..schemas.catalog_schemas import (
    BatchProductsResponse,
    PaginatedProductsResponse,
    PaginatedProvidersResponse,
    ProductCreate,
    ProductResponse,
    ProviderCreate,
    ProviderCreateResponse,
)

from .http_client import HttpClient


class CatalogAdapter(CatalogPort):
    """
    HTTP adapter for catalog microservice operations.

    This adapter implements the CatalogPort interface and handles
    communication with the catalog microservice via HTTP.
    """

    def __init__(self, http_client: HttpClient):
        """
        Initialize the catalog adapter.

        Args:
            http_client: Configured HTTP client for the catalog service
        """
        self.client = http_client

    async def create_provider(self, provider_data: ProviderCreate) -> ProviderCreateResponse:
        """Create a new provider in the catalog."""
        response_data = await self.client.post(
            "/catalog/provider",
            json=provider_data.model_dump(mode="json"),
        )
        return ProviderCreateResponse(**response_data)

    async def get_providers(
        self, limit: int = 10, offset: int = 0
    ) -> PaginatedProvidersResponse:
        """Retrieve a paginated list of providers."""
        response_data = await self.client.get(
            "/catalog/providers",
            params={"limit": limit, "offset": offset},
        )
        return PaginatedProvidersResponse(**response_data)

    async def create_products(self, products: List[ProductCreate]) -> BatchProductsResponse:
        """Create multiple products in the catalog."""
        products_data = [p.model_dump(mode="json") for p in products]
        response_data = await self.client.post(
            "/catalog/products",
            json={"products": products_data},
        )
        return BatchProductsResponse(**response_data)

    async def get_products(
        self, limit: int = 10, offset: int = 0
    ) -> PaginatedProductsResponse:
        """Retrieve a paginated list of products."""
        response_data = await self.client.get(
            "/catalog/products",
            params={"limit": limit, "offset": offset},
        )
        return PaginatedProductsResponse(**response_data)

    async def get_product_by_id(self, product_id: UUID) -> Optional[ProductResponse]:
        """Retrieve a single product by its ID."""
        try:
            response_data = await self.client.get(
                f"/catalog/product/{product_id}",
            )
            return ProductResponse(**response_data)
        except Exception:
            # If product not found or any error, return None
            return None
