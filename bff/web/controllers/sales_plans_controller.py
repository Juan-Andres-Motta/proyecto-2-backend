import httpx
from fastapi import APIRouter, HTTPException, Query, status

from web.schemas.seller_schemas import (
    PaginatedSalesPlansResponse,
    SalesPlanCreate,
    SalesPlanCreateResponse,
)
from web.services.seller_service import SellerService

router = APIRouter(prefix="/sales-plans", tags=["sales-plans"])


@router.post(
    "", response_model=SalesPlanCreateResponse, status_code=status.HTTP_201_CREATED
)
async def create_sales_plan(sales_plan: SalesPlanCreate):
    """Create a new sales plan."""
    try:
        seller_service = SellerService()
        result = await seller_service.create_sales_plan(sales_plan.model_dump())
        return SalesPlanCreateResponse(**result)
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"Error creating sales plan: {e.response.text}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating sales plan: {str(e)}",
        )


@router.get("", response_model=PaginatedSalesPlansResponse)
async def get_sales_plans(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """Get sales plans with pagination."""
    try:
        seller_service = SellerService()
        sales_plans_data = await seller_service.get_sales_plans(
            limit=limit, offset=offset
        )
        return sales_plans_data
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"Error fetching sales plans: {e.response.text}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching sales plans: {str(e)}",
        )
