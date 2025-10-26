"""Order controller for HTTP endpoints."""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.adapters.input.examples import (
    order_create_response_example,
    orders_list_response_example,
)
from src.adapters.input.schemas import (
    OrderCreateInput,
    OrderCreateResponse,
    OrderItemInput,
    OrderItemResponse,
    OrderResponse,
    PaginatedOrdersResponse,
)
from src.adapters.output.adapters import (
    MockCustomerAdapter,
    MockEventPublisher,
    MockInventoryAdapter,
    MockSellerAdapter,
)
from src.adapters.output.repositories.order_repository import OrderRepository
from src.application.use_cases import (
    CreateOrderInput,
    CreateOrderUseCase,
    GetOrderByIdUseCase,
    ListOrdersUseCase,
    OrderItemInput as UseCaseOrderItemInput,
)
from src.application.use_cases.list_customer_orders import ListCustomerOrdersUseCase
from src.domain.entities import Order as OrderEntity
from src.domain.value_objects import CreationMethod
from src.infrastructure.database.config import get_db

logger = logging.getLogger(__name__)
router = APIRouter(tags=["orders"])


def _entity_to_response(order_entity: OrderEntity) -> OrderResponse:
    """
    Convert domain entity to response schema.

    Args:
        order_entity: Order domain entity

    Returns:
        OrderResponse schema
    """
    return OrderResponse(
        id=order_entity.id,
        customer_id=order_entity.customer_id,
        seller_id=order_entity.seller_id,
        visit_id=order_entity.visit_id,
        route_id=order_entity.route_id,
        fecha_pedido=order_entity.fecha_pedido,
        fecha_entrega_estimada=order_entity.fecha_entrega_estimada,
        metodo_creacion=order_entity.metodo_creacion.value,
        direccion_entrega=order_entity.direccion_entrega,
        ciudad_entrega=order_entity.ciudad_entrega,
        pais_entrega=order_entity.pais_entrega,
        customer_name=order_entity.customer_name,
        customer_phone=order_entity.customer_phone,
        customer_email=order_entity.customer_email,
        seller_name=order_entity.seller_name,
        seller_email=order_entity.seller_email,
        monto_total=order_entity.monto_total,
        created_at=order_entity.fecha_pedido,  # Using fecha_pedido as proxy
        updated_at=order_entity.fecha_pedido,  # Using fecha_pedido as proxy
        items=[
            OrderItemResponse(
                id=item.id,
                pedido_id=item.pedido_id,
                producto_id=item.producto_id,
                inventario_id=item.inventario_id,
                cantidad=item.cantidad,
                precio_unitario=item.precio_unitario,
                precio_total=item.precio_total,
                product_name=item.product_name,
                product_sku=item.product_sku,
                warehouse_id=item.warehouse_id,
                warehouse_name=item.warehouse_name,
                warehouse_city=item.warehouse_city,
                warehouse_country=item.warehouse_country,
                batch_number=item.batch_number,
                expiration_date=item.expiration_date,
                created_at=order_entity.fecha_pedido,
                updated_at=order_entity.fecha_pedido,
            )
            for item in order_entity.items
        ],
    )


@router.post(
    "/order",
    response_model=OrderCreateResponse,
    status_code=201,
    responses={
        201: {
            "description": "Order created successfully",
            "content": {"application/json": {"example": order_create_response_example}},
        }
    },
)
async def create_order(
    order_input: OrderCreateInput, db: AsyncSession = Depends(get_db)
):
    """
    Create a new order.

    This endpoint:
    1. Validates customer, seller, visit (based on creation method)
    2. Allocates inventory using FEFO logic
    3. Applies 30% markup to product prices
    4. Creates order with denormalized data
    5. Publishes order_created event (fire-and-forget)

    Args:
        order_input: Order creation input
        db: Database session

    Returns:
        OrderCreateResponse with order ID

    Raises:
        HTTPException: If validation or creation fails
    """
    logger.info(f"Creating order for customer {order_input.customer_id}")

    try:
        # Initialize repository and adapters
        repository = OrderRepository(db)
        customer_adapter = MockCustomerAdapter()
        seller_adapter = MockSellerAdapter()
        inventory_adapter = MockInventoryAdapter()
        event_publisher = MockEventPublisher()

        # Initialize use case
        use_case = CreateOrderUseCase(
            order_repository=repository,
            customer_port=customer_adapter,
            seller_port=seller_adapter,
            inventory_port=inventory_adapter,
            event_publisher=event_publisher,
        )

        # Convert schema to use case input
        use_case_input = CreateOrderInput(
            customer_id=order_input.customer_id,
            metodo_creacion=CreationMethod(order_input.metodo_creacion),
            items=[
                UseCaseOrderItemInput(
                    producto_id=item.producto_id, cantidad=item.cantidad
                )
                for item in order_input.items
            ],
            seller_id=order_input.seller_id,
            visit_id=order_input.visit_id,
        )

        # Execute use case
        created_order = await use_case.execute(use_case_input)

        logger.info(f"Order {created_order.id} created successfully")

        return OrderCreateResponse(
            id=created_order.id, message="Order created successfully"
        )

    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error creating order: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


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
    """
    List orders with pagination.

    Args:
        limit: Maximum number of orders to return (1-100)
        offset: Number of orders to skip
        db: Database session

    Returns:
        PaginatedOrdersResponse with orders
    """
    logger.info(f"Listing orders (limit={limit}, offset={offset})")

    try:
        repository = OrderRepository(db)
        use_case = ListOrdersUseCase(order_repository=repository)

        orders, total = await use_case.execute(limit=limit, offset=offset)

        page = (offset // limit) + 1 if limit > 0 else 1
        has_next = (offset + limit) < total
        has_previous = offset > 0

        return PaginatedOrdersResponse(
            items=[_entity_to_response(order) for order in orders],
            total=total,
            page=page,
            size=len(orders),
            has_next=has_next,
            has_previous=has_previous,
        )

    except Exception as e:
        logger.error(f"Error listing orders: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/orders/{order_id}",
    response_model=OrderResponse,
    responses={
        200: {"description": "Order details"},
        404: {"description": "Order not found"},
    },
)
async def get_order(order_id: UUID, db: AsyncSession = Depends(get_db)):
    """
    Get an order by ID.

    Args:
        order_id: Order UUID
        db: Database session

    Returns:
        OrderResponse with order details

    Raises:
        HTTPException: If order not found
    """
    logger.info(f"Fetching order {order_id}")

    try:
        repository = OrderRepository(db)
        use_case = GetOrderByIdUseCase(order_repository=repository)

        order = await use_case.execute(order_id)

        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        return _entity_to_response(order)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching order {order_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/customers/{customer_id}/orders",
    response_model=PaginatedOrdersResponse,
    responses={
        200: {
            "description": "List of orders for a specific customer",
        }
    },
)
async def list_customer_orders(
    customer_id: UUID,
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """
    List orders for a specific customer with pagination.

    Args:
        customer_id: Customer UUID
        limit: Maximum number of orders to return (1-100)
        offset: Number of orders to skip
        db: Database session

    Returns:
        PaginatedOrdersResponse with customer's orders
    """
    logger.info(f"Listing orders for customer {customer_id} (limit={limit}, offset={offset})")

    try:
        repository = OrderRepository(db)
        use_case = ListCustomerOrdersUseCase(order_repository=repository)

        orders, total = await use_case.execute(
            customer_id=customer_id, limit=limit, offset=offset
        )

        page = (offset // limit) + 1 if limit > 0 else 1
        has_next = (offset + limit) < total
        has_previous = offset > 0

        return PaginatedOrdersResponse(
            items=[_entity_to_response(order) for order in orders],
            total=total,
            page=page,
            size=len(orders),
            has_next=has_next,
            has_previous=has_previous,
        )

    except Exception as e:
        logger.error(f"Error listing orders for customer {customer_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
