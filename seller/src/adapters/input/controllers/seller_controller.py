from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.adapters.input.examples import (
    seller_create_response_example,
    sellers_list_response_example,
)
from src.adapters.input.schemas import (
    PaginatedSellersResponse,
    SellerCreate,
    SellerResponse,
)
from src.adapters.output.repositories.seller_repository import SellerRepository
from src.application.use_cases.create_seller import CreateSellerUseCase
from src.application.use_cases.list_sellers import ListSellersUseCase
from src.infrastructure.database.config import get_db

router = APIRouter(tags=["sellers"])


@router.post(
    "/sellers",
    responses={
        201: {
            "description": "Seller created successfully",
            "content": {
                "application/json": {"example": seller_create_response_example}
            },
        }
    },
)
async def create_seller(seller: SellerCreate, db: AsyncSession = Depends(get_db)):
    repository = SellerRepository(db)
    use_case = CreateSellerUseCase(repository)
    created_seller = await use_case.execute(seller.model_dump())
    return JSONResponse(
        content={
            "id": str(created_seller.id),
            "message": "Seller created successfully",
        },
        status_code=201,
    )


@router.get(
    "/sellers",
    responses={
        200: {
            "description": "List of sellers with or without pagination",
            "content": {"application/json": {"example": sellers_list_response_example}},
        }
    },
)
async def list_sellers(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    repository = SellerRepository(db)
    use_case = ListSellersUseCase(repository)

    sellers, total = await use_case.execute(limit=limit, offset=offset)

    page = (offset // limit) + 1
    has_next = (offset + limit) < total
    has_previous = offset > 0

    return PaginatedSellersResponse(
        items=[
            SellerResponse.model_validate(seller, from_attributes=True)
            for seller in sellers
        ],
        total=total,
        page=page,
        size=len(sellers),
        has_next=has_next,
        has_previous=has_previous,
    )
