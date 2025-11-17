"""
Orders controller for client app.

This controller handles order creation for mobile client app users.
Orders created through this endpoint automatically have metodo_creacion='app_cliente'.
"""

import logging
from typing import Dict

from fastapi import APIRouter, Depends, HTTPException, Query

from common.auth.dependencies import require_client_user
from client_app.ports import OrderPort
from client_app.ports.client_port import ClientPort
from client_app.schemas import OrderCreateInput, OrderCreateResponse, PaginatedOrdersResponse
from common.exceptions import (
    MicroserviceConnectionError,
    MicroserviceHTTPError,
    MicroserviceValidationError,
)
from dependencies import get_client_order_port, get_client_app_client_port

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/orders",
    response_model=OrderCreateResponse,
    status_code=201,
    responses={
        201: {"description": "Order created successfully via client app"},
        400: {"description": "Invalid order data"},
        401: {"description": "Unauthorized - Invalid or missing token"},
        403: {"description": "Forbidden - Requires client_users group"},
        404: {"description": "Client not found for authenticated user"},
        503: {"description": "Order service unavailable"},
    },
)
async def create_order(
    order_input: OrderCreateInput,
    order_port: OrderPort = Depends(get_client_order_port),
    client_port: ClientPort = Depends(get_client_app_client_port),
    user: Dict = Depends(require_client_user),
):
    """
    Create a new order via client app.

    This endpoint:
    1. Gets the Cognito User ID from the authenticated user (JWT sub claim)
    2. Looks up the client record using cognito_user_id to get customer_id
    3. Validates that the client exists (404 if not found)
    4. Accepts items (inventario_id, cantidad)
    5. Forwards request to Order Service with metodo_creacion='app_cliente'
    6. No seller_id or visit_id required (client app orders)

    Args:
        order_input: Order creation input (items only)
        order_port: Order port for service communication
        client_port: Client port for service communication
        user: Authenticated client user

    Returns:
        OrderCreateResponse with order ID and message

    Raises:
        HTTPException: If client not found or order creation fails
    """
    cognito_user_id = user.get("sub")
    logger.info(f"Request: POST /orders (client app): cognito_user_id={cognito_user_id}, items_count={len(order_input.items)}")

    try:
        # Get client record by cognito_user_id
        client_data = await client_port.get_client_by_cognito_user_id(cognito_user_id)

        if not client_data:
            raise HTTPException(
                status_code=404,
                detail=f"No client found for authenticated user with cognito_user_id={cognito_user_id}",
            )

        customer_id = client_data["cliente_id"]
        logger.info(f"Found client: customer_id={customer_id}")

        # Create order with auto-fetched customer_id
        return await order_port.create_order(order_input, customer_id)

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


@router.get(
    "/my-orders",
    response_model=PaginatedOrdersResponse,
    responses={
        200: {"description": "List of orders for the authenticated client"},
        401: {"description": "Unauthorized - Invalid or missing token"},
        403: {"description": "Forbidden - Requires client_users group"},
        404: {"description": "Client not found for authenticated user"},
        503: {"description": "Order or Client service unavailable"},
    },
)
async def list_my_orders(
    limit: int = Query(10, ge=1, le=100, description="Maximum number of orders to return"),
    offset: int = Query(0, ge=0, description="Number of orders to skip"),
    order_port: OrderPort = Depends(get_client_order_port),
    client_port: ClientPort = Depends(get_client_app_client_port),
    user: Dict = Depends(require_client_user),
):
    """
    List orders for the authenticated client user.

    This endpoint:
    1. Gets the Cognito User ID from the authenticated user (JWT sub claim)
    2. Looks up the client record using cognito_user_id
    3. Fetches orders for that client (customer_id = cliente_id)

    Requires client_users group authentication.

    Args:
        limit: Maximum number of orders to return (1-100)
        offset: Number of orders to skip
        order_port: Order port for service communication
        client_port: Client port for service communication
        user: Authenticated client user

    Returns:
        PaginatedOrdersResponse with user's orders

    Raises:
        HTTPException: If client not found or order fetching fails
    """
    cognito_user_id = user.get("sub")
    logger.info(f"Request: GET /my-orders (client app): cognito_user_id={cognito_user_id}, limit={limit}, offset={offset}")

    try:
        # Get client record by cognito_user_id
        client_data = await client_port.get_client_by_cognito_user_id(cognito_user_id)

        if not client_data:
            raise HTTPException(
                status_code=404,
                detail=f"No client found for authenticated user with cognito_user_id={cognito_user_id}",
            )

        cliente_id = client_data["cliente_id"]
        logger.info(f"Found client: cliente_id={cliente_id}")

        # Fetch orders for this client
        return await order_port.list_customer_orders(
            customer_id=cliente_id, limit=limit, offset=offset
        )

    except HTTPException:
        raise

    except MicroserviceConnectionError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Service unavailable: {e.message}",
        )

    except MicroserviceHTTPError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=f"Service error: {e.message}",
        )

    except Exception as e:
        logger.error(f"Unexpected error listing orders: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error listing orders: {str(e)}",
        )
