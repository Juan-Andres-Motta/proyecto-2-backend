import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from common.middleware import setup_exception_handlers
from config.settings import settings
from web.router import router as web_router
from client_app.router import router as client_app_router
from sellers_app.router import router as sellers_app_router

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

# Configure exception handling middleware
# This must be registered first to catch exceptions from all other middleware and routes
setup_exception_handlers(app)

# Configure CORS
# TODO: Move hardcoded origins to environment variables/settings (requires terraform update)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://develop.medisupply.andres-duque.com"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger.info(f"Starting {settings.app_name} v{settings.app_version}")

app.include_router(web_router)
app.include_router(client_app_router)
app.include_router(sellers_app_router)


@app.get("/bff/health", tags=["health"])
async def health_check():
    """
    Health check endpoint for BFF service.

    Returns:
        Simple health status response
    """
    return {"status": "ok", "service": "bff"}
