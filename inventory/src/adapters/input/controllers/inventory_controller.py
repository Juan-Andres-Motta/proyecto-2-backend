from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.adapters.input.examples import (
    inventory_create_response_example,
    inventories_list_response_example,
)
from src.adapters.input.schemas import (
    InventoryCreate,
    InventoryResponse,
    PaginatedInventoriesResponse,
)
from src.adapters.output.repositories.inventory_repository import InventoryRepository
from src.application.use_cases.create_inventory import CreateInventoryUseCase
from src.application.use_cases.list_inventories import ListInventoriesUseCase
from src.infrastructure.database.config import get_db

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
    inventory: InventoryCreate, db: AsyncSession = Depends(get_db)
):
    repository = InventoryRepository(db)
    use_case = CreateInventoryUseCase(repository)
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
    db: AsyncSession = Depends(get_db),
):
    repository = InventoryRepository(db)
    use_case = ListInventoriesUseCase(repository)
    inventories, total = await use_case.execute(limit=limit, offset=offset)

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
