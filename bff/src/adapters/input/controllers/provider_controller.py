from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from src.adapters.input.schemas import (
    PaginatedProvidersResponse,
    ProviderCreate,
)
from src.adapters.output.clients.http_client import HTTPClient
from src.infrastructure.config.settings import settings

router = APIRouter(tags=["providers"])

# Create HTTP client for catalog service
catalog_client = HTTPClient(settings.catalog_url)


@router.post(
    "/provider",
    responses={
        201: {
            "description": "Provider created successfully",
        }
    },
)
async def create_provider(provider: ProviderCreate):
    response = await catalog_client.post("/provider", provider.model_dump())
    return JSONResponse(content=response, status_code=201)


@router.get(
    "/providers",
    response_model=PaginatedProvidersResponse,
    responses={
        200: {
            "description": "List of providers with pagination",
        }
    },
)
async def list_providers(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    params = {"limit": limit, "offset": offset}
    response = await catalog_client.get("/providers", params)
    return response
