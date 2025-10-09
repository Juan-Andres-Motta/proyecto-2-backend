from typing import Any, Dict

import httpx

from config import settings


class CatalogService:
    def __init__(self):
        self.catalog_url = settings.catalog_url

    async def get_providers(
        self, limit: int = 10, offset: int = 0
    ) -> Dict[str, Any]:
        """
        Fetch providers from the catalog microservice.

        Args:
            limit: Maximum number of providers to return
            offset: Number of providers to skip

        Returns:
            Dictionary with providers data and pagination info

        Raises:
            httpx.HTTPError: If the request fails
        """
        async with httpx.AsyncClient(timeout=settings.service_timeout) as client:
            response = await client.get(
                f"{self.catalog_url}/catalog/providers",
                params={"limit": limit, "offset": offset},
            )
            response.raise_for_status()
            return response.json()

    async def get_products(
        self, limit: int = 10, offset: int = 0
    ) -> Dict[str, Any]:
        """
        Fetch products from the catalog microservice.

        Args:
            limit: Maximum number of products to return
            offset: Number of products to skip

        Returns:
            Dictionary with products data and pagination info

        Raises:
            httpx.HTTPError: If the request fails
        """
        async with httpx.AsyncClient(timeout=settings.service_timeout) as client:
            response = await client.get(
                f"{self.catalog_url}/catalog/products",
                params={"limit": limit, "offset": offset},
            )
            response.raise_for_status()
            return response.json()
