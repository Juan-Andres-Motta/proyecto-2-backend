from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from src.adapters.input.schemas import (
    OrderCreate,
    PaginatedOrdersResponse,
)
from src.adapters.output.clients.http_client import HTTPClient
from src.infrastructure.config.settings import settings

router = APIRouter(tags=["orders"])

# Create HTTP client for order service
order_client = HTTPClient(settings.order_url)


@router.post(
    "/order",
    responses={
        201: {
            "description": "Order created successfully",
        }
    },
)
async def create_order(order: OrderCreate):
    response = await order_client.post("/order/order", order.model_dump())
    return JSONResponse(content=response, status_code=201)


@router.get(
    "/orders",
    response_model=PaginatedOrdersResponse,
    responses={
        200: {
            "description": "List of orders with pagination",
        }
    },
)
async def list_orders(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    params = {"limit": limit, "offset": offset}
    response = await order_client.get("/order/orders", params)
    return response
