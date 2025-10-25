"""
Sellers controller.

This controller handles seller-related endpoints using the seller port
for communication with the seller microservice.
"""

import logging
from typing import Dict, List, Union
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from common.auth.dependencies import require_web_user
from dependencies import get_seller_port

from ..ports import SellerPort
from ..schemas.seller_schemas import (
    PaginatedSalesPlansResponse,
    PaginatedSellersResponse,
    SellerCreate,
    SellerCreateResponse,
    SellerResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sellers")


@router.post("", response_model=SellerCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_seller(
    seller: SellerCreate,
    seller_port: SellerPort = Depends(get_seller_port),
    user: Dict = Depends(require_web_user),
):
    """
    Create a new seller.

    Args:
        seller: Seller data to create
        seller_port: Seller port for service communication

    Returns:
        Created seller id and success message
    """
    logger.info(f"Request: POST /sellers: name='{seller.name}'")
    return await seller_port.create_seller(seller)


@router.get("", response_model=Union[PaginatedSellersResponse, List[SellerResponse]])
async def get_sellers(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    seller_port: SellerPort = Depends(get_seller_port),
    user: Dict = Depends(require_web_user),
):
    """
    Get sellers with pagination.

    Args:
        limit: Maximum number of sellers to return (1-100)
        offset: Number of sellers to skip
        seller_port: Seller port for service communication

    Returns:
        Paginated list of sellers
    """
    logger.info(f"Request: GET /sellers: limit={limit}, offset={offset}")
    return await seller_port.get_sellers(limit=limit, offset=offset)


@router.get("/{seller_id}/sales-plans", response_model=PaginatedSalesPlansResponse)
async def get_seller_sales_plans(
    seller_id: UUID,
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    seller_port: SellerPort = Depends(get_seller_port),
    user: Dict = Depends(require_web_user),
):
    """
    Get sales plans for a specific seller with pagination.

    Args:
        seller_id: UUID of the seller
        limit: Maximum number of sales plans to return (1-100)
        offset: Number of sales plans to skip
        seller_port: Seller port for service communication

    Returns:
        Paginated list of sales plans for the seller
    """
    logger.info(f"Request: GET /sellers/{seller_id}/sales-plans: limit={limit}, offset={offset}")
    return await seller_port.get_seller_sales_plans(
        seller_id=seller_id, limit=limit, offset=offset
    )
