"""Thin controllers for inventories - just delegate to use cases.

No business logic, no validation, no try/catch.
All exceptions are handled by global exception handlers.
"""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse

from src.adapters.input.examples import (
    inventories_list_response_example,
    inventory_create_response_example,
)
from src.adapters.input.schemas import (
    InventoryCreate,
    InventoryResponse,
    PaginatedInventoriesResponse,
)
from src.application.use_cases.create_inventory import CreateInventoryUseCase
from src.application.use_cases.list_inventories import ListInventoriesUseCase
from src.infrastructure.dependencies import (
    get_create_inventory_use_case,
    get_list_inventories_use_case,
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
        }
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
        }
    },
)
async def list_inventories(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    product_id: Optional[UUID] = Query(None),
    warehouse_id: Optional[UUID] = Query(None),
    sku: Optional[str] = Query(None),
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
