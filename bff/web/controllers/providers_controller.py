from fastapi import APIRouter, HTTPException, Query
import httpx

from ..schemas import PaginatedProvidersResponse, ProviderCreate, ProviderCreateResponse
from ..services import CatalogService

router = APIRouter()


@router.post(
    "/provider",
    response_model=ProviderCreateResponse,
    status_code=201,
    responses={
        201: {
            "description": "Provider created successfully"
        },
        400: {"description": "Invalid provider data"},
        500: {"description": "Error communicating with catalog microservice"},
    },
)
async def create_provider(provider: ProviderCreate):
    """
    Create a new provider in the catalog microservice.

    Args:
        provider: Provider data to create

    Returns:
        Created provider id and success message
    """
    try:
        catalog_service = CatalogService()
        result = await catalog_service.create_provider(provider.model_dump())
        return ProviderCreateResponse(**result)
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 400:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid provider data: {e.response.text}",
            )
        raise HTTPException(
            status_code=500,
            detail=f"Error creating provider: Catalog service returned {e.response.status_code}",
        )
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error creating provider: Unable to connect to catalog service",
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error creating provider: {type(e).__name__}",
        )


@router.get(
    "/providers",
    response_model=PaginatedProvidersResponse,
    responses={
        200: {
            "description": "List of providers from catalog microservice"
        },
        500: {"description": "Error communicating with catalog microservice"},
    },
)
async def get_providers(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """
    Retrieve providers from the catalog microservice.

    Args:
        limit: Maximum number of providers to return (1-100)
        offset: Number of providers to skip

    Returns:
        Paginated list of providers
    """
    try:
        catalog_service = CatalogService()
        providers_data = await catalog_service.get_providers(
            limit=limit, offset=offset
        )
        return providers_data
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching providers: Catalog service returned {e.response.status_code}",
        )
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching providers: Unable to connect to catalog service",
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching providers: {type(e).__name__}",
        )
