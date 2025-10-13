from fastapi import APIRouter, HTTPException, Query
import httpx

from ..schemas import PaginatedWarehousesResponse, WarehouseCreate, WarehouseCreateResponse
from ..services.inventory_service import InventoryService

router = APIRouter()


@router.post(
    "/warehouse",
    response_model=WarehouseCreateResponse,
    status_code=201,
    responses={
        201: {
            "description": "Warehouse created successfully"
        },
        400: {"description": "Invalid warehouse data"},
        500: {"description": "Error communicating with inventory microservice"},
    },
)
async def create_warehouse(warehouse: WarehouseCreate):
    """
    Create a new warehouse in the inventory microservice.

    Args:
        warehouse: Warehouse data to create

    Returns:
        Created warehouse id and success message
    """
    try:
        inventory_service = InventoryService()
        result = await inventory_service.create_warehouse(warehouse.model_dump())
        return WarehouseCreateResponse(**result)
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 400:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid warehouse data: {e.response.text}",
            )
        raise HTTPException(
            status_code=500,
            detail=f"Error creating warehouse: Inventory service returned {e.response.status_code}",
        )
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error creating warehouse: Unable to connect to inventory service",
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error creating warehouse: {type(e).__name__}",
        )


@router.get(
    "/warehouses",
    response_model=PaginatedWarehousesResponse,
    responses={
        200: {
            "description": "List of warehouses from inventory microservice"
        },
        500: {"description": "Error communicating with inventory microservice"},
    },
)
async def get_warehouses(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """
    Retrieve warehouses from the inventory microservice.

    Args:
        limit: Maximum number of warehouses to return (1-100)
        offset: Number of warehouses to skip

    Returns:
        Paginated list of warehouses
    """
    try:
        inventory_service = InventoryService()
        warehouses_data = await inventory_service.get_warehouses(
            limit=limit, offset=offset
        )
        return warehouses_data
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching warehouses: Inventory service returned {e.response.status_code}",
        )
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching warehouses: Unable to connect to inventory service",
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching warehouses: {type(e).__name__}",
        )
