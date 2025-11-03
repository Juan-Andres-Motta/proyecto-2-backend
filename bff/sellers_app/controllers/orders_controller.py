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
from sellers_app.ports.seller_port import SellerPort
from sellers_app.schemas import OrderCreateInput, OrderCreateResponse
from common.exceptions import (
    MicroserviceConnectionError,
    MicroserviceHTTPError,
    MicroserviceValidationError,
)
from dependencies import get_seller_order_port, get_seller_app_seller_port

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
        404: {"description": "Seller not found for authenticated user"},
        503: {"description": "Order service unavailable"},
    },
)
async def create_order(
    order_input: OrderCreateInput,
    order_port: OrderPort = Depends(get_seller_order_port),
    seller_port: SellerPort = Depends(get_seller_app_seller_port),
    user: Dict = Depends(require_seller_user),
):
    """
    Create a new order via sellers app.

    This endpoint:
    1. Gets the Cognito User ID from the authenticated user (JWT sub claim)
    2. Looks up the seller record using cognito_user_id to get seller_id
    3. Validates that the seller exists (404 if not found)
    4. Accepts customer_id, items, and optional visit_id
    5. Forwards request to Order Service with metodo_creacion='app_vendedor'
    6. visit_id is OPTIONAL (can be linked to a visit or not)

    Args:
        order_input: Order creation input (customer_id, items, visit_id?)
        order_port: Order port for service communication
        seller_port: Seller port for service communication
        user: Authenticated seller user

    Returns:
        OrderCreateResponse with order ID and message

    Raises:
        HTTPException: If seller not found or order creation fails
    """
    cognito_user_id = user.get("sub")
    logger.info(f"Request: POST /sellers-app/orders: cognito_user_id={cognito_user_id}, customer_id={order_input.customer_id}, items={len(order_input.items)}")

    try:
        # Get seller record by cognito_user_id
        seller_data = await seller_port.get_seller_by_cognito_user_id(cognito_user_id)

        if not seller_data:
            raise HTTPException(
                status_code=404,
                detail=f"No seller found for authenticated user with cognito_user_id={cognito_user_id}",
            )

        seller_id = seller_data["id"]
        logger.info(f"Found seller: seller_id={seller_id}")

        # Create order with auto-fetched seller_id
        return await order_port.create_order(order_input, seller_id)

    except HTTPException:
        raise

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
        logger.error(f"Unexpected error creating order: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error creating order: {str(e)}",
        )
