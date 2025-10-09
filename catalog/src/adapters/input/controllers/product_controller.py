from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.adapters.input.examples import products_list_response_example
from src.adapters.input.schemas import (
    PaginatedProductsResponse,
    ProductResponse,
)
from src.adapters.output.repositories.product_repository import ProductRepository
from src.application.use_cases.list_products import ListProductsUseCase
from src.infrastructure.database.config import get_db

router = APIRouter(tags=["products"])


@router.get(
    "/products",
    response_model=PaginatedProductsResponse,
    responses={
        200: {
            "description": "List of products with pagination",
            "content": {
                "application/json": {"example": products_list_response_example}
            },
        }
    },
)
async def list_products(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    repository = ProductRepository(db)
    use_case = ListProductsUseCase(repository)
    products, total = await use_case.execute(limit=limit, offset=offset)

    page = (offset // limit) + 1
    has_next = (offset + limit) < total
    has_previous = offset > 0

    return PaginatedProductsResponse(
        items=[
            ProductResponse.model_validate(product, from_attributes=True)
            for product in products
        ],
        total=total,
        page=page,
        size=len(products),
        has_next=has_next,
        has_previous=has_previous,
    )
