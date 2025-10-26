from fastapi import APIRouter, FastAPI

from src.adapters.input.controllers.client_controller import router as client_router
from src.infrastructure.api.exception_handlers import register_exception_handlers
from src.infrastructure.config.settings import settings

app = FastAPI(
    title=settings.app_name,
    description=settings.app_description,
    version=settings.app_version,
    docs_url=settings.docs_url,
    redoc_url=settings.redoc_url,
    openapi_url=settings.openapi_url,
)

# Register global exception handlers
register_exception_handlers(app)

# Create router for common endpoints
common_router = APIRouter(tags=["common"])


@common_router.get("/")
async def read_root():
    return {"name": "Client Service"}


@common_router.get("/health")
async def read_health():
    return {"status": "ok"}


# Include all routers under /client prefix
app.include_router(common_router, prefix="/client")
app.include_router(client_router, prefix="/client")
