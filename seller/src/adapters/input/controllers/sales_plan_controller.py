from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.adapters.input.examples import (
    sales_plan_create_response_example,
    sales_plans_list_response_example,
)
from src.adapters.input.schemas import (
    PaginatedSalesPlansResponse,
    SalesPlanCreate,
    SalesPlanResponse,
)
from src.adapters.output.repositories.sales_plan_repository import SalesPlanRepository
from src.application.use_cases.create_sales_plan import CreateSalesPlanUseCase
from src.application.use_cases.list_sales_plans import ListSalesPlansUseCase
from src.infrastructure.database.config import get_db

router = APIRouter(tags=["sales-plans"])


@router.post(
    "/sales-plans",
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
    sales_plan: SalesPlanCreate, db: AsyncSession = Depends(get_db)
):
    repository = SalesPlanRepository(db)
    use_case = CreateSalesPlanUseCase(repository)
    created_sales_plan = await use_case.execute(sales_plan.model_dump())
    return JSONResponse(
        content={
            "id": str(created_sales_plan.id),
            "message": "Sales plan created successfully",
        },
        status_code=201,
    )


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
    db: AsyncSession = Depends(get_db),
):
    repository = SalesPlanRepository(db)
    use_case = ListSalesPlansUseCase(repository)
    sales_plans, total = await use_case.execute(limit=limit, offset=offset)

    page = (offset // limit) + 1
    has_next = (offset + limit) < total
    has_previous = offset > 0

    return PaginatedSalesPlansResponse(
        items=[
            SalesPlanResponse.model_validate(sales_plan, from_attributes=True)
            for sales_plan in sales_plans
        ],
        total=total,
        page=page,
        size=len(sales_plans),
        has_next=has_next,
        has_previous=has_previous,
    )
