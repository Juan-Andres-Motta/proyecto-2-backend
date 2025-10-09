import asyncio
from typing import Dict, List

import httpx

from config import settings


class HealthService:
    """Service for checking health of microservices."""

    def __init__(self):
        self.services = {
            "catalog": settings.catalog_url,
            "client": settings.client_url,
            "delivery": settings.delivery_url,
            "inventory": settings.inventory_url,
            "order": settings.order_url,
            "seller": settings.seller_url,
        }

    async def check_service_health(
        self, service_name: str, service_url: str
    ) -> Dict[str, str]:
        """
        Check health status of a single service.

        Args:
            service_name: Name of the service
            service_url: URL of the service

        Returns:
            Dictionary with service name and health status
        """
        try:
            async with httpx.AsyncClient(timeout=settings.service_timeout) as client:
                response = await client.get(f"{service_url}/health")
                if response.status_code == 200:
                    data = response.json()
                    if data.get("status") == "ok":
                        return {service_name: "healthy"}
                return {service_name: "unhealthy"}
        except (httpx.RequestError, httpx.TimeoutException):
            return {service_name: "unreachable"}
        except Exception:
            return {service_name: "error"}

    async def check_all_services(self) -> List[Dict[str, str]]:
        """
        Check health status of all microservices concurrently.

        Returns:
            List of dictionaries with service name as key and health status as value.
            Example: [{"catalog": "healthy"}, {"order": "unhealthy"}, ...]
        """
        tasks = [
            self.check_service_health(service_name, service_url)
            for service_name, service_url in self.services.items()
        ]
        results = await asyncio.gather(*tasks)
        return results
