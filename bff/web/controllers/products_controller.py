from fastapi import APIRouter, HTTPException, Query

from ..schemas import PaginatedProductsResponse
from ..services import CatalogService

router = APIRouter()


@router.get(
    "/products",
    response_model=PaginatedProductsResponse,
    responses={
        200: {
            "description": "List of products from catalog microservice"
        },
        500: {"description": "Error communicating with catalog microservice"},
    },
)
async def get_products(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """
    Retrieve products from the catalog microservice.

    Args:
        limit: Maximum number of products to return (1-100)
        offset: Number of products to skip

    Returns:
        Paginated list of products
    """
    try:
        catalog_service = CatalogService()
        products_data = await catalog_service.get_products(
            limit=limit, offset=offset
        )
        return products_data
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching products: {str(e)}",
        )
