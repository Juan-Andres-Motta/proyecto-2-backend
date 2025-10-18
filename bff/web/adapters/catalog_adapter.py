"""
Catalog adapter implementation.

This adapter implements the CatalogPort interface using HTTP communication.
"""

import logging
from typing import List, Optional
from uuid import UUID

from common.http_client import HttpClient

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

logger = logging.getLogger(__name__)


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
        logger.info(f"Creating provider: name='{provider_data.name}', nit='{provider_data.nit}'")
        response_data = await self.client.post(
            "/provider",
            json=provider_data.model_dump(mode="json"),
        )
        return ProviderCreateResponse(**response_data)

    async def get_providers(
        self, limit: int = 10, offset: int = 0
    ) -> PaginatedProvidersResponse:
        """Retrieve a paginated list of providers."""
        logger.info(f"Getting providers: limit={limit}, offset={offset}")
        response_data = await self.client.get(
            "/providers",
            params={"limit": limit, "offset": offset},
        )
        return PaginatedProvidersResponse(**response_data)

    async def create_products(self, products: List[ProductCreate]) -> BatchProductsResponse:
        """Create multiple products in the catalog."""
        logger.info(f"Creating products: count={len(products)}")
        products_data = [p.model_dump(mode="json") for p in products]
        response_data = await self.client.post(
            "/products",
            json={"products": products_data},
        )
        return BatchProductsResponse(**response_data)

    async def get_products(
        self, limit: int = 10, offset: int = 0
    ) -> PaginatedProductsResponse:
        """Retrieve a paginated list of products."""
        logger.info(f"Getting products: limit={limit}, offset={offset}")
        response_data = await self.client.get(
            "/products",
            params={"limit": limit, "offset": offset},
        )
        return PaginatedProductsResponse(**response_data)

    async def get_product_by_id(self, product_id: UUID) -> Optional[ProductResponse]:
        """Retrieve a single product by its ID."""
        logger.info(f"Getting product by ID: product_id={product_id}")
        try:
            response_data = await self.client.get(
                f"/product/{product_id}",
            )
            return ProductResponse(**response_data)
        except Exception:
            # If product not found or any error, return None
            return None
