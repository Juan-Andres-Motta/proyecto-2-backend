"""Thin controllers for warehouses - just delegate to use cases.

No business logic, no validation, no try/catch.
All exceptions are handled by global exception handlers.
"""
from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse

from src.adapters.input.examples import (
    warehouse_create_response_example,
    warehouses_list_response_example,
)
from src.adapters.input.schemas import (
    PaginatedWarehousesResponse,
    WarehouseCreate,
    WarehouseResponse,
)
from src.application.use_cases.create_warehouse import CreateWarehouseUseCase
from src.application.use_cases.list_warehouses import ListWarehousesUseCase
from src.infrastructure.dependencies import (
    get_create_warehouse_use_case,
    get_list_warehouses_use_case,
)

router = APIRouter(tags=["warehouses"])


@router.post(
    "/warehouse",
    responses={
        201: {
            "description": "Warehouse created successfully",
            "content": {
                "application/json": {"example": warehouse_create_response_example}
            },
        }
    },
)
async def create_warehouse(
    warehouse: WarehouseCreate,
    use_case: CreateWarehouseUseCase = Depends(get_create_warehouse_use_case),
):
    """Create a new warehouse - THIN controller."""
    # Delegate to use case - no try/catch, exceptions bubble up
    created_warehouse = await use_case.execute(warehouse.model_dump())
    return JSONResponse(
        content={
            "id": str(created_warehouse.id),
            "message": "Warehouse created successfully",
        },
        status_code=201,
    )


@router.get(
    "/warehouses",
    response_model=PaginatedWarehousesResponse,
    responses={
        200: {
            "description": "List of warehouses with pagination",
            "content": {
                "application/json": {"example": warehouses_list_response_example}
            },
        }
    },
)
async def list_warehouses(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    use_case: ListWarehousesUseCase = Depends(get_list_warehouses_use_case),
):
    """List warehouses - THIN controller."""
    # Delegate to use case
    warehouses, total = await use_case.execute(limit=limit, offset=offset)

    page = (offset // limit) + 1
    has_next = (offset + limit) < total
    has_previous = offset > 0

    return PaginatedWarehousesResponse(
        items=[
            WarehouseResponse.model_validate(warehouse, from_attributes=True)
            for warehouse in warehouses
        ],
        total=total,
        page=page,
        size=len(warehouses),
        has_next=has_next,
        has_previous=has_previous,
    )
