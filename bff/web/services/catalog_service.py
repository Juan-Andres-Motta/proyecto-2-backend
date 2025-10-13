from typing import Any, Dict, List

import httpx

from config import settings


class CatalogService:
    def __init__(self):
        self.catalog_url = settings.catalog_url

    async def create_provider(self, provider_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new provider in the catalog microservice.

        Args:
            provider_data: Dictionary with provider data

        Returns:
            Dictionary with created provider id and message

        Raises:
            httpx.HTTPError: If the request fails
        """
        async with httpx.AsyncClient(timeout=settings.service_timeout) as client:
            response = await client.post(
                f"{self.catalog_url}/catalog/provider",
                json=provider_data,
            )
            response.raise_for_status()
            return response.json()

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

    async def create_products(self, products: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Create multiple products in the catalog microservice.

        Args:
            products: List of product dictionaries to create

        Returns:
            Dictionary with created products data

        Raises:
            httpx.HTTPError: If the request fails
        """
        async with httpx.AsyncClient(timeout=settings.service_timeout) as client:
            response = await client.post(
                f"{self.catalog_url}/catalog/products",
                json={"products": products},
            )
            response.raise_for_status()
            return response.json()
