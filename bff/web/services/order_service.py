from typing import Any, Dict

import httpx

from config.settings import settings


class OrderService:
    def __init__(self):
        self.order_url = settings.order_url

    async def create_order(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new order."""
        async with httpx.AsyncClient(timeout=settings.service_timeout) as client:
            response = await client.post(
                f"{self.order_url}/order/order", json=order_data
            )
            response.raise_for_status()
            return response.json()

    async def get_orders(
        self, limit: int = 10, offset: int = 0
    ) -> Dict[str, Any]:
        """Get orders with pagination."""
        async with httpx.AsyncClient(timeout=settings.service_timeout) as client:
            response = await client.get(
                f"{self.order_url}/order/orders",
                params={"limit": limit, "offset": offset},
            )
            response.raise_for_status()
            return response.json()
