from fastapi import APIRouter, HTTPException, Query

from ..schemas import PaginatedProvidersResponse
from ..services import CatalogService

router = APIRouter()


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
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching providers: {str(e)}",
        )
