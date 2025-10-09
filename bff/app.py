import logging

from fastapi import FastAPI

from src.adapters.input.controllers.common_controller import router as common_router
from src.adapters.input.controllers.inventory_controller import (
    router as inventory_router,
)
from src.adapters.input.controllers.order_controller import router as order_router
from src.adapters.input.controllers.provider_controller import router as provider_router
from src.adapters.input.controllers.seller_controller import router as seller_router
from src.infrastructure.config.logger import setup_logging
from src.infrastructure.config.settings import settings

# Setup logging
setup_logging()

# Get logger for this module
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.app_name,
    description=settings.app_description,
    version=settings.app_version,
    contact={
        "name": settings.app_contact_name,
        "email": settings.app_contact_email,
    },
    docs_url=settings.docs_url,
    redoc_url=settings.redoc_url,
)

logger.info(f"Starting {settings.app_name} v{settings.app_version}")

app.include_router(common_router, prefix="/bff")
app.include_router(provider_router, prefix="/bff")
app.include_router(inventory_router, prefix="/bff")
app.include_router(order_router, prefix="/bff")
app.include_router(seller_router, prefix="/bff")
