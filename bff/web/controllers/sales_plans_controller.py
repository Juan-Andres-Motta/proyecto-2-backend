"""
Sales Plans controller.

This controller handles sales plan-related endpoints using the seller port
for communication with the seller microservice.
"""

from fastapi import APIRouter, Depends, Query, status

from dependencies import get_seller_port

from ..ports import SellerPort
from ..schemas.seller_schemas import (
    PaginatedSalesPlansResponse,
    SalesPlanCreate,
    SalesPlanCreateResponse,
)

router = APIRouter(prefix="/sales-plans")


@router.post(
    "", response_model=SalesPlanCreateResponse, status_code=status.HTTP_201_CREATED
)
async def create_sales_plan(
    sales_plan: SalesPlanCreate,
    seller_port: SellerPort = Depends(get_seller_port),
):
    """
    Create a new sales plan.

    Args:
        sales_plan: Sales plan data to create
        seller_port: Seller port for service communication

    Returns:
        Created sales plan id and success message
    """
    return await seller_port.create_sales_plan(sales_plan)


@router.get("", response_model=PaginatedSalesPlansResponse)
async def get_sales_plans(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    seller_port: SellerPort = Depends(get_seller_port),
):
    """
    Get sales plans with pagination.

    Args:
        limit: Maximum number of sales plans to return (1-100)
        offset: Number of sales plans to skip
        seller_port: Seller port for service communication

    Returns:
        Paginated list of sales plans
    """
    return await seller_port.get_sales_plans(limit=limit, offset=offset)
