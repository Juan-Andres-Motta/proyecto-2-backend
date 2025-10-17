import httpx
from fastapi import APIRouter, HTTPException, Query, status

from web.schemas.order_schemas import (
    OrderCreate,
    OrderCreateResponse,
    PaginatedOrdersResponse,
)
from web.services.order_service import OrderService

router = APIRouter(prefix="/orders")


@router.post("", response_model=OrderCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_order(order: OrderCreate):
    """Create a new order."""
    try:
        order_service = OrderService()
        result = await order_service.create_order(order.model_dump(mode="json"))
        return OrderCreateResponse(**result)
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"Error creating order: {e.response.text}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating order: {str(e)}",
        )


@router.get("", response_model=PaginatedOrdersResponse)
async def get_orders(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """Get orders with pagination."""
    try:
        order_service = OrderService()
        orders_data = await order_service.get_orders(limit=limit, offset=offset)
        return orders_data
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"Error fetching orders: {e.response.text}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching orders: {str(e)}",
        )
