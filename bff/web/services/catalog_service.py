from typing import Any, Dict, List

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
                f"{self.catalog_url}/providers",
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
                f"{self.catalog_url}/products",
                params={"limit": limit, "offset": offset},
            )
            response.raise_for_status()
            return response.json()

    async def get_catalog(
        self, providers_limit: int = 10, products_limit: int = 10
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Fetch both providers and products from the catalog microservice.

        Args:
            providers_limit: Maximum number of providers to return
            products_limit: Maximum number of products to return

        Returns:
            Dictionary with providers and products lists

        Raises:
            httpx.HTTPError: If any request fails
        """
        providers_data = await self.get_providers(limit=providers_limit, offset=0)
        products_data = await self.get_products(limit=products_limit, offset=0)

        return {
            "providers": providers_data.get("items", []),
            "products": products_data.get("items", []),
        }
