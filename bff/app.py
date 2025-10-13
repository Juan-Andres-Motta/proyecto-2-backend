import logging

from fastapi import FastAPI

from config.settings import settings
from web.router import router as web_router

# Get logger for this module
logger = logging.getLogger(__name__)

# Configure logging
logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

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

app.include_router(web_router)


@app.get("/bff/health", tags=["health"])
async def health_check():
    """
    Health check endpoint for BFF service.

    Returns:
        Simple health status response
    """
    return {"status": "ok", "service": "bff"}
