"""
Warehouses controller.

This controller handles warehouse-related endpoints using the inventory port
for communication with the inventory microservice.
"""

from fastapi import APIRouter, Depends, Query, status

from dependencies import get_inventory_port

from ..ports import InventoryPort
from ..schemas import PaginatedWarehousesResponse, WarehouseCreate, WarehouseCreateResponse

router = APIRouter()


@router.post(
    "/warehouse",
    response_model=WarehouseCreateResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"description": "Warehouse created successfully"},
        400: {"description": "Invalid warehouse data"},
        500: {"description": "Error communicating with inventory microservice"},
    },
)
async def create_warehouse(
    warehouse: WarehouseCreate,
    inventory: InventoryPort = Depends(get_inventory_port),
):
    """
    Create a new warehouse in the inventory microservice.

    Args:
        warehouse: Warehouse data to create
        inventory: Inventory port for service communication

    Returns:
        Created warehouse id and success message
    """
    return await inventory.create_warehouse(warehouse)


@router.get(
    "/warehouses",
    response_model=PaginatedWarehousesResponse,
    responses={
        200: {"description": "List of warehouses from inventory microservice"},
        500: {"description": "Error communicating with inventory microservice"},
    },
)
async def get_warehouses(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    inventory: InventoryPort = Depends(get_inventory_port),
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
    return await inventory.get_warehouses(limit=limit, offset=offset)
