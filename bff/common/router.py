from typing import Dict, List

from fastapi import APIRouter

from config import settings

from .controllers import router as inventories_router
from .health_service import HealthService

router = APIRouter(prefix="/bff", tags=["common"])


@router.get("/")
async def read_root() -> Dict[str, str]:
    """Root endpoint returning service information."""
    return {"name": settings.app_name}


@router.get("/health")
async def read_health() -> Dict[str, str]:
    """Health check endpoint for this service."""
    return {"status": "ok"}


@router.get("/check-all")
async def check_all_services() -> List[Dict[str, str]]:
    """
    Check health status of all microservices.

    Returns:
        List of dictionaries with service name as key and health status as value.
        Example: [{"catalog": "healthy"}, {"order": "unhealthy"}, ...]
    """
    health_service = HealthService()
    return await health_service.check_all_services()


# Include inventories controller
router.include_router(inventories_router)
