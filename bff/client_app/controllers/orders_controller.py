"""
Orders controller for client app.

This controller handles order creation for mobile client app users.
Orders created through this endpoint automatically have metodo_creacion='app_cliente'.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException

from client_app.ports import OrderPort
from client_app.schemas import OrderCreateInput, OrderCreateResponse
from common.exceptions import (
    MicroserviceConnectionError,
    MicroserviceHTTPError,
    MicroserviceValidationError,
)
from dependencies import get_client_order_port

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/orders", response_model=OrderCreateResponse, status_code=201)
async def create_order(
    order_input: OrderCreateInput,
    order_port: OrderPort = Depends(get_client_order_port),
):
    """
    Create a new order via client app.

    This endpoint:
    1. Accepts customer_id and items (producto_id, cantidad)
    2. Forwards request to Order Service with metodo_creacion='app_cliente'
    3. No seller_id or visit_id required (client app orders)

    Args:
        order_input: Order creation input
        order_port: Order port for service communication

    Returns:
        OrderCreateResponse with order ID and message

    Raises:
        HTTPException: If order creation fails
    """
    logger.info(f"Request: POST /orders (client app): customer_id={order_input.customer_id}, items_count={len(order_input.items)}")
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
