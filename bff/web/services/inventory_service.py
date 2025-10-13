from typing import Any, Dict

import httpx

from config import settings


class InventoryService:
    def __init__(self):
        self.inventory_url = settings.inventory_url

    async def create_warehouse(self, warehouse_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new warehouse in the inventory microservice.

        Args:
            warehouse_data: Dictionary with warehouse data

        Returns:
            Dictionary with created warehouse id and message

        Raises:
            httpx.HTTPError: If the request fails
        """
        async with httpx.AsyncClient(timeout=settings.service_timeout) as client:
            response = await client.post(
                f"{self.inventory_url}/inventory/warehouse",
                json=warehouse_data,
            )
            response.raise_for_status()
            return response.json()

    async def get_warehouses(
        self, limit: int = 10, offset: int = 0
    ) -> Dict[str, Any]:
        """
        Fetch warehouses from the inventory microservice.

        Args:
            limit: Maximum number of warehouses to return
            offset: Number of warehouses to skip

        Returns:
            Dictionary with warehouses data and pagination info

        Raises:
            httpx.HTTPError: If the request fails
        """
        async with httpx.AsyncClient(timeout=settings.service_timeout) as client:
            response = await client.get(
                f"{self.inventory_url}/inventory/warehouses",
                params={"limit": limit, "offset": offset},
            )
            response.raise_for_status()
            return response.json()
