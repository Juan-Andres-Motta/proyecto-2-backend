"""Thin controllers for products - just delegate to use cases.

No business logic, no validation, no try/catch.
All exceptions are handled by global exception handlers.
"""
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from src.adapters.input.examples import products_list_response_example
from src.adapters.input.schemas import (
    BatchProductsRequest,
    BatchProductsResponse,
    PaginatedProductsResponse,
    ProductResponse,
)
from src.application.use_cases.create_products import CreateProductsUseCase
from src.application.use_cases.get_product import GetProductUseCase
from src.application.use_cases.list_products import ListProductsUseCase
from src.domain.exceptions import ProductNotFoundException
from src.infrastructure.dependencies import (
    get_create_products_use_case,
    get_get_product_use_case,
    get_list_products_use_case,
)

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
    use_case: CreateProductsUseCase = Depends(get_create_products_use_case)
):
    """Create multiple products in a batch - THIN controller.

    Just delegates to use case. All validation and business logic
    is in the use case. Domain exceptions are caught by global handlers.

    Args:
        request: Batch products creation request
        use_case: Injected use case

    Returns:
        Batch products response
    """
    # Convert Pydantic models to dicts
    products_data = [product.model_dump() for product in request.products]

    # Delegate to use case - no try/catch, exceptions bubble up
    created_products = await use_case.execute(products_data)

    # Map domain entities to DTOs
    return BatchProductsResponse(
        created=[
            ProductResponse.model_validate(product, from_attributes=True)
            for product in created_products
        ],
        count=len(created_products),
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
    use_case: ListProductsUseCase = Depends(get_list_products_use_case)
):
    """List products - THIN controller.

    Just delegates to use case and maps to DTOs.

    Args:
        limit: Maximum number of results
        offset: Number to skip
        use_case: Injected use case

    Returns:
        Paginated products response
    """
    # Delegate to use case
    products, total = await use_case.execute(limit=limit, offset=offset)

    # Calculate pagination metadata
    page = (offset // limit) + 1
    has_next = (offset + limit) < total
    has_previous = offset > 0

    # Map domain entities to DTOs
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


@router.get(
    "/product/{product_id}",
    response_model=ProductResponse,
    responses={
        200: {"description": "Product details"},
        404: {"description": "Product not found"},
    },
)
async def get_product(
    product_id: UUID,
    use_case: GetProductUseCase = Depends(get_get_product_use_case)
):
    """Get a single product by ID - THIN controller.

    Just delegates to use case and maps to DTO.

    Args:
        product_id: Product UUID
        use_case: Injected use case

    Returns:
        Product response

    Raises:
        HTTPException: 404 if product not found
    """
    # Delegate to use case
    product = await use_case.execute(product_id)

    # Return 404 if not found (raise domain exception that will be handled by exception handler)
    if product is None:
        raise ProductNotFoundException(product_id)

    # Map domain entity to DTO
    return ProductResponse.model_validate(product, from_attributes=True)
