from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.adapters.input.examples import (
    order_create_response_example,
    orders_list_response_example,
)
from src.adapters.input.schemas import (
    OrderCreate,
    OrderResponse,
    PaginatedOrdersResponse,
)
from src.adapters.output.repositories.order_repository import OrderRepository
from src.application.use_cases.create_order import CreateOrderUseCase
from src.application.use_cases.list_orders import ListOrdersUseCase
from src.infrastructure.database.config import get_db

router = APIRouter(tags=["orders"])


@router.post(
    "/order",
    responses={
        201: {
            "description": "Order created successfully",
            "content": {"application/json": {"example": order_create_response_example}},
        }
    },
)
async def create_order(order: OrderCreate, db: AsyncSession = Depends(get_db)):
    repository = OrderRepository(db)
    use_case = CreateOrderUseCase(repository)

    # Extract items data
    items_data = [item.model_dump() for item in order.items]

    # Extract order data without items
    order_data = order.model_dump(exclude={"items"})

    created_order = await use_case.execute(order_data, items_data)
    return JSONResponse(
        content={
            "id": str(created_order.id),
            "message": "Order created successfully",
        },
        status_code=201,
    )


@router.get(
    "/orders",
    response_model=PaginatedOrdersResponse,
    responses={
        200: {
            "description": "List of orders with pagination",
            "content": {"application/json": {"example": orders_list_response_example}},
        }
    },
)
async def list_orders(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    repository = OrderRepository(db)
    use_case = ListOrdersUseCase(repository)
    orders, total = await use_case.execute(limit=limit, offset=offset)

    page = (offset // limit) + 1
    has_next = (offset + limit) < total
    has_previous = offset > 0

    return PaginatedOrdersResponse(
        items=[
            OrderResponse.model_validate(order, from_attributes=True)
            for order in orders
        ],
        total=total,
        page=page,
        size=len(orders),
        has_next=has_next,
        has_previous=has_previous,
    )
