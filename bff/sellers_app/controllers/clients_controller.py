"""
Clients controller for sellers app.

This controller handles client management for mobile seller app users.
Sellers can only LIST clients (view), not create them.
Clients are ONLY created via self-signup: POST /auth/signup with user_type="client"
"""

import logging
from typing import Dict
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from common.auth.dependencies import require_seller_user
from common.exceptions import (
    MicroserviceConnectionError,
    MicroserviceHTTPError,
)
from dependencies import get_seller_client_port
from sellers_app.ports import ClientPort
from sellers_app.schemas import ClientListResponse

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get(
    "/clients",
    response_model=ClientListResponse,
    summary="List clients with pagination",
    description="Retrieves clients, optionally filtered by assigned seller. Supports pagination with page and page_size parameters.",
    responses={
        200: {"description": "List of clients"},
        401: {"description": "Unauthorized - Invalid or missing token"},
        403: {"description": "Forbidden - Requires seller_users group"},
        503: {"description": "Client service unavailable"},
    },
)
async def list_clients(
    vendedor_asignado_id: UUID | None = Query(None, description="Filter clients by assigned seller ID"),
    client_name: str | None = Query(None, description="Filter by institution name (partial match)"),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(50, ge=1, le=100, description="Number of items per page"),
    client_port: ClientPort = Depends(get_seller_client_port),
    user: Dict = Depends(require_seller_user),
):
    """
    List clients with pagination, optionally filtered by assigned seller.

    Requires mobile seller authentication (seller_users group).

    Args:
        vendedor_asignado_id: Optional seller ID to filter clients
        client_name: Optional institution name filter (partial match)
        page: Page number (1-indexed)
        page_size: Number of items per page
        client_port: Client port for service communication
        user: Authenticated seller user

    Returns:
        List of clients with pagination metadata

    Raises:
        HTTPException: If listing clients fails
    """
    logger.info(
        f"Request: GET /sellers-app/clients: vendedor_asignado_id={vendedor_asignado_id}, "
        f"client_name={client_name}, page={page}, page_size={page_size}, user={user.get('email')}"
    )

    try:
        return await client_port.list_clients(vendedor_asignado_id, client_name, page, page_size)

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
