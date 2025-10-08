import asyncio
import os
from typing import Dict, List

import httpx
from fastapi import FastAPI

app = FastAPI(root_path="/bff")

# Microservices to check (URLs from environment variables)
SERVICES = {
    "catalog": os.getenv("CATALOG_URL", "http://catalog:8000"),
    "client": os.getenv("CLIENT_URL", "http://client:8000"),
    "delivery": os.getenv("DELIVERY_URL", "http://delivery:8000"),
    "inventory": os.getenv("INVENTORY_URL", "http://inventory:8000"),
    "order": os.getenv("ORDER_URL", "http://order:8000"),
    "seller": os.getenv("SELLER_URL", "http://seller:8000"),
}


async def check_service_health(service_name: str, service_url: str) -> Dict[str, str]:
    """Check health status of a single service."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
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


@app.get("/")
async def read_root():
    return {"name": "BFF Service"}


@app.get("/health")
async def read_health():
    return {"status": "ok"}


@app.get("/check-all")
async def check_all_services() -> List[Dict[str, str]]:
    """
    Check health status of all microservices.

    Returns:
        List of dictionaries with service name as key and health status as value.
        Example: [{"catalog": "healthy"}, {"order": "unhealthy"}, ...]
    """
    tasks = [
        check_service_health(service_name, service_url)
        for service_name, service_url in SERVICES.items()
    ]
    results = await asyncio.gather(*tasks)
    return results
