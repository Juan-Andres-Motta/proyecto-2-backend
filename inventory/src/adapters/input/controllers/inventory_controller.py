"""Thin controllers for inventories - just delegate to use cases.

No business logic, no validation, no try/catch.
All exceptions are handled by global exception handlers.
"""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse

from src.adapters.input.error_schemas import ValidationErrorResponse
from src.adapters.input.examples import (
    inventories_list_response_example,
    inventory_create_response_example,
)
from src.adapters.input.schemas import (
    InventoryCreate,
    InventoryReserveRequest,
    InventoryResponse,
    PaginatedInventoriesResponse,
)
from src.application.use_cases.create_inventory import CreateInventoryUseCase
from src.application.use_cases.get_inventory import GetInventoryUseCase
from src.application.use_cases.list_inventories import ListInventoriesUseCase
from src.application.use_cases.update_reserved_quantity import (
    UpdateReservedQuantityUseCase,
)
from src.infrastructure.dependencies import (
    get_create_inventory_use_case,
    get_get_inventory_use_case,
    get_list_inventories_use_case,
    get_update_reserved_quantity_use_case,
)

router = APIRouter(tags=["inventories"])


@router.post(
    "/inventory",
    responses={
        201: {
            "description": "Inventory created successfully",
            "content": {
                "application/json": {"example": inventory_create_response_example}
            },
        },
        422: {"description": "Invalid inventory data", "model": ValidationErrorResponse},
    },
)
async def create_inventory(
    inventory: InventoryCreate,
    use_case: CreateInventoryUseCase = Depends(get_create_inventory_use_case),
):
    """Create a new inventory - THIN controller."""
    # Delegate to use case - no try/catch, exceptions bubble up
    created_inventory = await use_case.execute(inventory.model_dump())
    return JSONResponse(
        content={
            "id": str(created_inventory.id),
            "message": "Inventory created successfully",
        },
        status_code=201,
    )


@router.get(
    "/inventories",
    response_model=PaginatedInventoriesResponse,
    responses={
        200: {
            "description": "List of inventories with pagination",
            "content": {
                "application/json": {"example": inventories_list_response_example}
            },
        },
        422: {"description": "Invalid query parameters", "model": ValidationErrorResponse},
    },
)
async def list_inventories(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    product_id: Optional[UUID] = Query(None),
    warehouse_id: Optional[UUID] = Query(None),
    sku: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    name: Optional[str] = Query(None),
    use_case: ListInventoriesUseCase = Depends(get_list_inventories_use_case),
):
    """List inventories with optional filters - THIN controller."""
    # Delegate to use case
    inventories, total = await use_case.execute(
        limit=limit,
        offset=offset,
        product_id=product_id,
        warehouse_id=warehouse_id,
        sku=sku,
        category=category,
        name=name,
    )

    page = (offset // limit) + 1
    has_next = (offset + limit) < total
    has_previous = offset > 0

    return PaginatedInventoriesResponse(
        items=[
            InventoryResponse.model_validate(inventory, from_attributes=True)
            for inventory in inventories
        ],
        total=total,
        page=page,
        size=len(inventories),
        has_next=has_next,
        has_previous=has_previous,
    )


@router.get(
    "/inventory/{inventory_id}",
    response_model=InventoryResponse,
    responses={
        200: {
            "description": "Inventory details retrieved successfully",
        },
        404: {
            "description": "Inventory not found",
            "model": ValidationErrorResponse,
        },
    },
)
async def get_inventory(
    inventory_id: UUID,
    use_case: GetInventoryUseCase = Depends(get_get_inventory_use_case),
):
    """Get a single inventory entry by ID.

    This endpoint allows clients to:
    - Fetch specific inventory details for validation
    - View available quantity (total_quantity - reserved_quantity)
    - Get all denormalized product and warehouse information
    """
    # Delegate to use case - no try/catch, exceptions bubble up
    inventory = await use_case.execute(inventory_id)

    # Convert domain entity to response schema
    return InventoryResponse.model_validate(inventory, from_attributes=True)


@router.patch(
    "/inventory/{inventory_id}/reserve",
    response_model=InventoryResponse,
    responses={
        200: {"description": "Reservation updated successfully"},
        404: {"description": "Inventory not found", "model": ValidationErrorResponse},
        409: {
            "description": "Insufficient inventory or invalid release",
            "model": ValidationErrorResponse,
        },
        422: {"description": "Invalid request data", "model": ValidationErrorResponse},
    },
)
async def update_reserved_quantity(
    inventory_id: UUID,
    request: InventoryReserveRequest,
    use_case: UpdateReservedQuantityUseCase = Depends(
        get_update_reserved_quantity_use_case
    ),
):
    """
    Update reserved quantity on inventory (reserve or release units).

    - Reserve units: positive quantity_delta (e.g., {"quantity_delta": 10})
    - Release units: negative quantity_delta (e.g., {"quantity_delta": -5})

    Validations:
    - Cannot reserve more than available
    - Cannot release more than currently reserved
    - Uses row-level locking to prevent race conditions
    """
    inventory = await use_case.execute(inventory_id, request.quantity_delta)
    return InventoryResponse.model_validate(inventory, from_attributes=True)
