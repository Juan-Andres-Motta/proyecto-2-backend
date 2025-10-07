from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.adapters.input.examples import (
    store_create_response_example,
    stores_list_response_example,
)
from src.adapters.input.schemas import (
    PaginatedStoresResponse,
    StoreCreate,
    StoreResponse,
)
from src.adapters.output.repositories.store_repository import StoreRepository
from src.application.use_cases.create_store import CreateStoreUseCase
from src.application.use_cases.list_stores import ListStoresUseCase
from src.infrastructure.database.config import get_db

router = APIRouter(tags=["stores"])


@router.post(
    "/store",
    responses={
        201: {
            "description": "Store created successfully",
            "content": {"application/json": {"example": store_create_response_example}},
        }
    },
)
async def create_store(store: StoreCreate, db: AsyncSession = Depends(get_db)):
    repository = StoreRepository(db)
    use_case = CreateStoreUseCase(repository)
    created_store = await use_case.execute(store.model_dump())
    return JSONResponse(
        content={
            "id": str(created_store.id),
            "message": "Store created successfully",
        },
        status_code=201,
    )


@router.get(
    "/stores",
    response_model=PaginatedStoresResponse,
    responses={
        200: {
            "description": "List of stores with pagination",
            "content": {"application/json": {"example": stores_list_response_example}},
        }
    },
)
async def list_stores(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    repository = StoreRepository(db)
    use_case = ListStoresUseCase(repository)
    stores, total = await use_case.execute(limit=limit, offset=offset)

    page = (offset // limit) + 1
    has_next = (offset + limit) < total
    has_previous = offset > 0

    return PaginatedStoresResponse(
        items=[
            StoreResponse.model_validate(store, from_attributes=True)
            for store in stores
        ],
        total=total,
        page=page,
        size=len(stores),
        has_next=has_next,
        has_previous=has_previous,
    )
