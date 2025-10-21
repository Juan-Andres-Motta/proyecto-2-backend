"""
Warehouses controller.

This controller handles warehouse-related endpoints using the inventory port
for communication with the inventory microservice.
"""

import logging
from typing import Dict

from fastapi import APIRouter, Depends, Query, status

from common.auth.dependencies import require_web_user
from dependencies import get_inventory_port

from ..ports import InventoryPort
from ..schemas import PaginatedWarehousesResponse, WarehouseCreate, WarehouseCreateResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/warehouse",
    response_model=WarehouseCreateResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"description": "Warehouse created successfully"},
        400: {"description": "Invalid warehouse data"},
        401: {"description": "Unauthorized - Invalid or missing token"},
        403: {"description": "Forbidden - Requires web_users group"},
        500: {"description": "Error communicating with inventory microservice"},
    },
)
async def create_warehouse(
    warehouse: WarehouseCreate,
    inventory: InventoryPort = Depends(get_inventory_port),
    user: Dict = Depends(require_web_user),
):
    """
    Create a new warehouse in the inventory microservice.

    Args:
        warehouse: Warehouse data to create
        inventory: Inventory port for service communication

    Returns:
        Created warehouse id and success message
    """
    logger.info(f"Request: POST /warehouse: name='{warehouse.name}'")
    return await inventory.create_warehouse(warehouse)


@router.get(
    "/warehouses",
    response_model=PaginatedWarehousesResponse,
    responses={
        200: {"description": "List of warehouses from inventory microservice"},
        401: {"description": "Unauthorized - Invalid or missing token"},
        403: {"description": "Forbidden - Requires web_users group"},
        500: {"description": "Error communicating with inventory microservice"},
    },
)
async def get_warehouses(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    inventory: InventoryPort = Depends(get_inventory_port),
    user: Dict = Depends(require_web_user),
):
    """
    Retrieve warehouses from the inventory microservice.

    Args:
        limit: Maximum number of warehouses to return (1-100)
        offset: Number of warehouses to skip
        inventory: Inventory port for service communication

    Returns:
        Paginated list of warehouses
    """
    logger.info(f"Request: GET /warehouses: limit={limit}, offset={offset}")
    return await inventory.get_warehouses(limit=limit, offset=offset)
