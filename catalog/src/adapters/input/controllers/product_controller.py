from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from src.adapters.input.examples import products_list_response_example
from src.adapters.input.schemas import (
    BatchProductsErrorResponse,
    BatchProductsRequest,
    BatchProductsResponse,
    PaginatedProductsResponse,
    ProductCreate,
    ProductError,
    ProductResponse,
)
from src.adapters.output.repositories.product_repository import ProductRepository
from src.application.use_cases.create_products import CreateProductsUseCase
from src.application.use_cases.list_products import ListProductsUseCase
from src.infrastructure.database.config import get_db

router = APIRouter(tags=["products"])


@router.post(
    "/products",
    response_model=BatchProductsResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"description": "Products created successfully"},
        400: {"description": "Validation error or product creation failed"},
        404: {"description": "Provider not found"},
        422: {"description": "Invalid product data"},
    },
)
async def create_products(
    request: BatchProductsRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Create multiple products in a batch.
    All products are created in a single transaction.
    If any product fails, all creations are rolled back.
    """
    repository = ProductRepository(db)
    use_case = CreateProductsUseCase(repository)

    try:
        # Convert Pydantic models to dicts
        products_data = [product.model_dump() for product in request.products]

        # Execute batch creation
        created_products = await use_case.execute(products_data)

        return BatchProductsResponse(
            created=[
                ProductResponse.model_validate(product, from_attributes=True)
                for product in created_products
            ],
            count=len(created_products),
        )

    except IntegrityError as e:
        await db.rollback()
        # Check if it's a foreign key constraint (provider not found)
        if "foreign key constraint" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Provider not found. Please verify the provider_id exists.",
            )
        # Generic integrity error
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Database integrity error: {str(e)}",
        )

    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create products: {str(e)}",
        )

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}",
        )


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
