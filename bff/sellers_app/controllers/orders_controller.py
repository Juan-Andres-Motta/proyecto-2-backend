"""
Orders controller for sellers app.

This controller handles order creation for mobile seller app users.
Orders created through this endpoint automatically have metodo_creacion='app_vendedor'.
"""

from fastapi import APIRouter, Depends, HTTPException

from sellers_app.ports import OrderPort
from sellers_app.schemas import OrderCreateInput, OrderCreateResponse
from common.exceptions import (
    MicroserviceConnectionError,
    MicroserviceHTTPError,
    MicroserviceValidationError,
)

router = APIRouter()


# Dependency function - will be added to dependencies.py
def get_order_port() -> OrderPort:
    """
    Temporary dependency function.
    This will be moved to dependencies.py
    """
    from sellers_app.adapters import OrderAdapter
    from web.adapters import HttpClient
    from config.settings import settings

    client = HttpClient(
        base_url=settings.order_url,
        timeout=settings.service_timeout,
        service_name="order",
    )
    return OrderAdapter(client)


@router.post("/orders", response_model=OrderCreateResponse, status_code=201)
async def create_order(
    order_input: OrderCreateInput,
    order_port: OrderPort = Depends(get_order_port),
):
    """
    Create a new order via sellers app.

    This endpoint:
    1. Accepts customer_id, seller_id, items, and optional visit_id
    2. Forwards request to Order Service with metodo_creacion='app_vendedor'
    3. seller_id is REQUIRED (seller creating the order)
    4. visit_id is OPTIONAL (can be linked to a visit or not)

    Args:
        order_input: Order creation input
        order_port: Order port for service communication

    Returns:
        OrderCreateResponse with order ID and message

    Raises:
        HTTPException: If order creation fails
    """
    try:
        return await order_port.create_order(order_input)

    except MicroserviceValidationError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid order data: {e.message}",
        )

    except MicroserviceConnectionError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Order service unavailable: {e.message}",
        )

    except MicroserviceHTTPError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=f"Order service error: {e.message}",
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error creating order: {str(e)}",
        )
