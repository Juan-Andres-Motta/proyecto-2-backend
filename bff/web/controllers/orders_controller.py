"""
Orders controller.

This controller handles order-related endpoints using the order port
for communication with the order microservice.
"""

from fastapi import APIRouter, Depends, Query, status

from dependencies import get_order_port

from ..ports import OrderPort
from ..schemas.order_schemas import (
    OrderCreate,
    OrderCreateResponse,
    PaginatedOrdersResponse,
)

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("", response_model=OrderCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    order: OrderCreate,
    order_port: OrderPort = Depends(get_order_port),
):
    """
    Create a new order.

    Args:
        order: Order data to create
        order_port: Order port for service communication

    Returns:
        Created order id and success message
    """
    return await order_port.create_order(order)


@router.get("", response_model=PaginatedOrdersResponse)
async def get_orders(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    order_port: OrderPort = Depends(get_order_port),
):
    """
    Get orders with pagination.

    Args:
        limit: Maximum number of orders to return (1-100)
        offset: Number of orders to skip
        order_port: Order port for service communication

    Returns:
        Paginated list of orders
    """
    return await order_port.get_orders(limit=limit, offset=offset)
