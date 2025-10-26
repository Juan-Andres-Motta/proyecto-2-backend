"""
Clients controller for sellers app.

This controller handles client management for mobile seller app users.
List endpoint requires seller_users authentication.
"""

import logging
from typing import Dict
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from common.auth.dependencies import require_seller_user
from common.exceptions import (
    MicroserviceConnectionError,
    MicroserviceHTTPError,
    MicroserviceValidationError,
)
from dependencies import get_seller_client_port
from sellers_app.ports import ClientPort
from sellers_app.schemas import ClientCreateInput, ClientListResponse

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post(
    "/clients",
    status_code=201,
    responses={
        201: {"description": "Client created successfully via seller app"},
        400: {"description": "Invalid client data or duplicate NIT/Cognito User"},
        401: {"description": "Unauthorized - Invalid or missing token"},
        403: {"description": "Forbidden - Requires seller_users group"},
        503: {"description": "Client service unavailable"},
    },
)
async def create_client(
    client_input: ClientCreateInput,
    client_port: ClientPort = Depends(get_seller_client_port),
    user: Dict = Depends(require_seller_user),
):
    """
    Create a new client via sellers app.

    Requires mobile seller authentication (seller_users group).

    Args:
        client_input: Client creation input
        client_port: Client port for service communication
        user: Authenticated seller user

    Returns:
        Client creation response with ID and message

    Raises:
        HTTPException: If client creation fails
    """
    logger.info(f"Request: POST /sellers-app/clients: nit={client_input.nit}, nombre_institucion={client_input.nombre_institucion}")

    try:
        return await client_port.create_client(client_input)

    except MicroserviceValidationError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid client data: {e.message}",
        )

    except MicroserviceConnectionError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Client service unavailable: {e.message}",
        )

    except MicroserviceHTTPError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=f"Client service error: {e.message}",
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error creating client: {str(e)}",
        )


@router.get(
    "/clients",
    response_model=ClientListResponse,
    responses={
        200: {"description": "List of clients"},
        401: {"description": "Unauthorized - Invalid or missing token"},
        403: {"description": "Forbidden - Requires seller_users group"},
        503: {"description": "Client service unavailable"},
    },
)
async def list_clients(
    vendedor_asignado_id: UUID | None = Query(None, description="Filter clients by assigned seller ID"),
    client_port: ClientPort = Depends(get_seller_client_port),
    user: Dict = Depends(require_seller_user),
):
    """
    List clients, optionally filtered by assigned seller.

    Requires mobile seller authentication (seller_users group).

    Args:
        vendedor_asignado_id: Optional seller ID to filter clients
        client_port: Client port for service communication
        user: Authenticated seller user

    Returns:
        List of clients

    Raises:
        HTTPException: If listing clients fails
    """
    logger.info(f"Request: GET /sellers-app/clients: vendedor_asignado_id={vendedor_asignado_id}, user={user.get('email')}")

    try:
        return await client_port.list_clients(vendedor_asignado_id)

    except MicroserviceConnectionError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Client service unavailable: {e.message}",
        )

    except MicroserviceHTTPError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=f"Client service error: {e.message}",
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error listing clients: {str(e)}",
        )
