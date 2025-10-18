import logging

from fastapi import FastAPI

from src.adapters.input.controllers.common_controller import router as common_router
from src.adapters.input.controllers.inventory_controller import (
    router as inventory_router,
)
from src.adapters.input.controllers.warehouse_controller import router as warehouse_router
from src.infrastructure.api.exception_handlers import register_exception_handlers
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
    openapi_url=settings.openapi_url,
)

logger.info(f"Starting {settings.app_name} v{settings.app_version}")

# Register global exception handlers (like Spring @ControllerAdvice)
register_exception_handlers(app)

app.include_router(common_router, prefix="/inventory")
app.include_router(warehouse_router, prefix="/inventory")
app.include_router(inventory_router, prefix="/inventory")
