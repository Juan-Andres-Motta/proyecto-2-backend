from typing import Any, Dict

import httpx

from config.settings import settings


class SellerService:
    def __init__(self):
        self.seller_url = settings.seller_url

    async def create_seller(self, seller_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new seller."""
        async with httpx.AsyncClient(timeout=settings.service_timeout) as client:
            response = await client.post(
                f"{self.seller_url}/seller/sellers", json=seller_data
            )
            response.raise_for_status()
            return response.json()

    async def get_sellers(
        self, limit: int = 10, offset: int = 0, all: bool = False
    ) -> Dict[str, Any]:
        """Get sellers with pagination or all sellers."""
        async with httpx.AsyncClient(timeout=settings.service_timeout) as client:
            params = {"limit": limit, "offset": offset}
            if all:
                params["all"] = "true"
            response = await client.get(
                f"{self.seller_url}/seller/sellers", params=params
            )
            response.raise_for_status()
            return response.json()

    async def create_sales_plan(
        self, sales_plan_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a new sales plan."""
        async with httpx.AsyncClient(timeout=settings.service_timeout) as client:
            response = await client.post(
                f"{self.seller_url}/seller/sales-plans", json=sales_plan_data
            )
            response.raise_for_status()
            return response.json()

    async def get_sales_plans(
        self, limit: int = 10, offset: int = 0
    ) -> Dict[str, Any]:
        """Get sales plans with pagination."""
        async with httpx.AsyncClient(timeout=settings.service_timeout) as client:
            response = await client.get(
                f"{self.seller_url}/seller/sales-plans",
                params={"limit": limit, "offset": offset},
            )
            response.raise_for_status()
            return response.json()

    async def get_seller_sales_plans(
        self, seller_id: str, limit: int = 10, offset: int = 0
    ) -> Dict[str, Any]:
        """Get sales plans for a specific seller with pagination."""
        async with httpx.AsyncClient(timeout=settings.service_timeout) as client:
            response = await client.get(
                f"{self.seller_url}/seller/sellers/{seller_id}/sales-plans",
                params={"limit": limit, "offset": offset},
            )
            response.raise_for_status()
            return response.json()
