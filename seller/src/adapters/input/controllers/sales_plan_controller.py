"""Thin controllers for sales plans - just delegate to use cases.

No business logic, no validation, no try/catch.
All exceptions are handled by global exception handlers.
"""
from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import JSONResponse

from src.adapters.input.examples import (
    sales_plan_create_response_example,
    sales_plans_list_response_example,
)
from src.adapters.input.schemas import (
    PaginatedSalesPlansResponse,
    SalesPlanCreate,
    SalesPlanResponse,
)
from src.application.use_cases.create_sales_plan import CreateSalesPlanUseCase
from src.application.use_cases.list_sales_plans import ListSalesPlansUseCase
from src.infrastructure.dependencies import (
    get_create_sales_plan_use_case,
    get_list_sales_plans_use_case,
)

router = APIRouter(tags=["sales-plans"])


@router.post(
    "/sales-plans",
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {
            "description": "Sales plan created successfully",
            "content": {
                "application/json": {"example": sales_plan_create_response_example}
            },
        }
    },
)
async def create_sales_plan(
    request: SalesPlanCreate,
    use_case: CreateSalesPlanUseCase = Depends(get_create_sales_plan_use_case)
):
    """Create a new sales plan - THIN controller.

    Just delegates to use case. All validation and business logic
    is in the use case. Domain exceptions are caught by global handlers.

    Args:
        request: Sales plan creation request
        use_case: Injected use case

    Returns:
        Created sales plan response
    """
    # Delegate to use case - no try/catch, exceptions bubble up
    created_plan = await use_case.execute(
        seller_id=request.seller_id,
        sales_period=request.sales_period,
        goal=request.goal
    )

    # Map domain entity to DTO
    return SalesPlanResponse.from_domain(created_plan)


@router.get(
    "/sales-plans",
    response_model=PaginatedSalesPlansResponse,
    responses={
        200: {
            "description": "List of sales plans with pagination",
            "content": {
                "application/json": {"example": sales_plans_list_response_example}
            },
        }
    },
)
async def list_sales_plans(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    use_case: ListSalesPlansUseCase = Depends(get_list_sales_plans_use_case)
):
    """List sales plans - THIN controller.

    Just delegates to use case and maps to DTOs.

    Args:
        limit: Maximum number of results
        offset: Number to skip
        use_case: Injected use case

    Returns:
        Paginated sales plans response
    """
    # Delegate to use case
    sales_plans, total = await use_case.execute(limit=limit, offset=offset)

    # Calculate pagination metadata
    page = (offset // limit) + 1
    has_next = (offset + limit) < total
    has_previous = offset > 0

    # Map domain entities to DTOs
    return PaginatedSalesPlansResponse(
        items=[
            SalesPlanResponse.from_domain(plan) for plan in sales_plans
        ],
        total=total,
        page=page,
        size=len(sales_plans),
        has_next=has_next,
        has_previous=has_previous,
    )
