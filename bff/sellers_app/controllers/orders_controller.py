"""
Orders controller for sellers app.

This controller handles order creation for mobile seller app users.
Orders created through this endpoint automatically have metodo_creacion='app_vendedor'.
"""

import logging
from typing import Dict

from fastapi import APIRouter, Depends, HTTPException

from common.auth.dependencies import require_seller_user
from sellers_app.ports import OrderPort
from sellers_app.schemas import OrderCreateInput, OrderCreateResponse
from common.exceptions import (
    MicroserviceConnectionError,
    MicroserviceHTTPError,
    MicroserviceValidationError,
)
from dependencies import get_seller_order_port

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post(
    "/orders",
    response_model=OrderCreateResponse,
    status_code=201,
    responses={
        201: {"description": "Order created successfully via seller app"},
        400: {"description": "Invalid order data"},
        401: {"description": "Unauthorized - Invalid or missing token"},
        403: {"description": "Forbidden - Requires seller_users group"},
        503: {"description": "Order service unavailable"},
    },
)
async def create_order(
    order_input: OrderCreateInput,
    order_port: OrderPort = Depends(get_seller_order_port),
    user: Dict = Depends(require_seller_user),
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
    logger.info(f"Request: POST /sellers-app/orders: customer_id={order_input.customer_id}, seller_id={order_input.seller_id}, items={len(order_input.items)}")

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
