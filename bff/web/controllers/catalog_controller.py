from fastapi import APIRouter, HTTPException, Query

from ..schemas import CatalogResponse
from ..services import CatalogService

router = APIRouter(tags=["catalog"])


@router.get(
    "/catalog",
    response_model=CatalogResponse,
    responses={
        200: {
            "description": "List of providers and products from catalog microservice"
        },
        500: {"description": "Error communicating with catalog microservice"},
    },
)
async def get_catalog(
    providers_limit: int = Query(10, ge=1, le=100),
    products_limit: int = Query(10, ge=1, le=100),
):
    """
    Retrieve providers and products from the catalog microservice.

    Args:
        providers_limit: Maximum number of providers to return (1-100)
        products_limit: Maximum number of products to return (1-100)

    Returns:
        Combined catalog response with providers and products
    """
    try:
        catalog_service = CatalogService()
        catalog_data = await catalog_service.get_catalog(
            providers_limit=providers_limit, products_limit=products_limit
        )
        return catalog_data
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching catalog data: {str(e)}",
        )
