from typing import List, Union

import httpx
from fastapi import APIRouter, HTTPException, Query, status

from web.schemas.seller_schemas import (
    PaginatedSellersResponse,
    SellerCreate,
    SellerCreateResponse,
    SellerResponse,
)
from web.services.seller_service import SellerService

router = APIRouter(prefix="/sellers", tags=["sellers"])


@router.post("", response_model=SellerCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_seller(seller: SellerCreate):
    """Create a new seller."""
    try:
        seller_service = SellerService()
        result = await seller_service.create_seller(seller.model_dump())
        return SellerCreateResponse(**result)
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"Error creating seller: {e.response.text}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating seller: {str(e)}",
        )


@router.get("", response_model=Union[PaginatedSellersResponse, List[SellerResponse]])
async def get_sellers(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    all: bool = Query(False, description="Return all sellers without pagination"),
):
    """Get sellers with pagination or all sellers."""
    try:
        seller_service = SellerService()
        sellers_data = await seller_service.get_sellers(
            limit=limit, offset=offset, all=all
        )

        # If all=True, the response is a list, otherwise it's paginated
        if all:
            return sellers_data

        return sellers_data
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"Error fetching sellers: {e.response.text}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching sellers: {str(e)}",
        )
