from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.adapters.input.examples import (
    warehouse_create_response_example,
    warehouses_list_response_example,
)
from src.adapters.input.schemas import (
    PaginatedWarehousesResponse,
    WarehouseCreate,
    WarehouseResponse,
)
from src.adapters.output.repositories.warehouse_repository import WarehouseRepository
from src.application.use_cases.create_warehouse import CreateWarehouseUseCase
from src.application.use_cases.list_warehouses import ListWarehousesUseCase
from src.infrastructure.database.config import get_db

router = APIRouter(tags=["warehouses"])


@router.post(
    "/warehouse",
    responses={
        201: {
            "description": "Warehouse created successfully",
            "content": {"application/json": {"example": warehouse_create_response_example}},
        }
    },
)
async def create_warehouse(warehouse: WarehouseCreate, db: AsyncSession = Depends(get_db)):
    repository = WarehouseRepository(db)
    use_case = CreateWarehouseUseCase(repository)
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
            "content": {"application/json": {"example": warehouses_list_response_example}},
        }
    },
)
async def list_warehouses(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    repository = WarehouseRepository(db)
    use_case = ListWarehousesUseCase(repository)
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
