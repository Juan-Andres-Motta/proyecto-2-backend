"""
Inventories controller for shared BFF functionality.

This controller handles inventory-related endpoints accessible only to
authenticated mobile users (sellers and clients). Web users are NOT allowed.
"""

import logging
from typing import Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from common.auth.dependencies import require_mobile_user
from common.schemas import PaginatedInventoriesResponse
from dependencies import get_common_inventory_port

from ..ports import InventoryPort

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/inventories",
    response_model=PaginatedInventoriesResponse,
    responses={
        200: {
            "description": "Paginated list of inventories with product and warehouse details",
            "model": PaginatedInventoriesResponse,
        },
        400: {"description": "Invalid query parameters - only one filter allowed"},
        401: {"description": "Unauthorized - missing or invalid authentication token"},
        403: {"description": "Forbidden - web users are not allowed to access this endpoint"},
    },
)
async def get_inventories(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    name: Optional[str] = Query(None),
    sku: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    user: Dict = Depends(require_mobile_user),
    inventory: InventoryPort = Depends(get_common_inventory_port),
):
    """
    Retrieve inventories from the inventory microservice with optional filters.

    **Authentication Required**: Only seller_users and client_users can access this endpoint.
    Web users are NOT allowed.

    Only ONE filter can be applied at a time (name OR sku OR category).

    Each inventory item includes:
    - Product details (SKU, name, price, category)
    - Warehouse information (name, city, country)
    - Stock levels (total, reserved, available quantities)
    - Batch information (batch number, expiration date)

    Args:
        limit: Maximum number of inventories to return (1-100)
        offset: Number of inventories to skip
        name: Optional product name filter
        sku: Optional product SKU filter
        category: Optional category filter
        user: Authenticated user (seller or client only)
        inventory: Inventory port for service communication

    Returns:
        PaginatedInventoriesResponse with:
        - items: List of inventory records with full details
        - total: Total number of items matching the filter
        - page: Current page number
        - size: Number of items per page
        - has_next: Whether there are more pages
        - has_previous: Whether there are previous pages

    Raises:
        HTTPException: 400 if more than one filter is provided
        HTTPException: 401 if authentication token is missing or invalid
        HTTPException: 403 if user is not a seller or client (e.g., web user)
    """
    # Validate that only one filter is provided at a time
    filters_provided = sum(
        [
            name is not None,
            sku is not None,
            category is not None,
        ]
    )

    if filters_provided > 1:
        logger.warning(
            f"Multiple filters provided: name={name}, sku={sku}, category={category}"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only one filter allowed at a time",
        )

    logger.info(
        f"Request: GET /inventories: limit={limit}, offset={offset}, "
        f"name={name}, sku={sku}, category={category}"
    )

    return await inventory.get_inventories(
        limit=limit,
        offset=offset,
        name=name,
        sku=sku,
        category=category,
    )
