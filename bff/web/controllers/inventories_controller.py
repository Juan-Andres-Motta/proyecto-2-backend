"""
Inventories controller.

This controller handles inventory-related endpoints, orchestrating between
the catalog microservice (for product data) and inventory microservice.
"""

import logging
from typing import Dict, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse

from common.auth.dependencies import require_web_user
from common.error_schemas import NotFoundErrorResponse, ValidationErrorResponse
from dependencies import get_catalog_port, get_inventory_port

from ..ports import CatalogPort, InventoryPort
from ..schemas import (
    InventoryCreate,
    InventoryCreateRequest,
    InventoryCreateResponse,
    PaginatedInventoriesResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/inventory",
    response_model=InventoryCreateResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"description": "Inventory created successfully"},
        404: {"description": "Product not found", "model": NotFoundErrorResponse},
        422: {"description": "Invalid inventory data", "model": ValidationErrorResponse},
    },
)
async def create_inventory(
    request_data: InventoryCreateRequest,
    catalog: CatalogPort = Depends(get_catalog_port),
    inventory: InventoryPort = Depends(get_inventory_port),
    user: Dict = Depends(require_web_user),
):
    """
    Create a new inventory entry.

    This endpoint orchestrates between catalog and inventory microservices:
    1. Fetches product data from catalog service
    2. Validates product exists
    3. Creates inventory with denormalized product data

    Args:
        request_data: Inventory creation data from client (JSON body) - does NOT include denormalized fields
        catalog: Catalog port for service communication
        inventory: Inventory port for service communication

    Returns:
        Created inventory id and success message

    Raises:
        HTTPException: 404 if product not found
    """
    logger.info(f"Request: POST /inventory: product_id={request_data.product_id}, warehouse_id={request_data.warehouse_id}")
    # Step 1: Fetch product from catalog
    product = await catalog.get_product_by_id(request_data.product_id)

    # Step 2: Validate product exists
    if not product:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "error_code": "PRODUCT_NOT_FOUND",
                "message": f"Product with ID '{request_data.product_id}' not found",
                "type": "not_found",
                "details": {
                    "resource": "Product",
                    "id": str(request_data.product_id)
                }
            }
        )

    # Step 3: Enrich request data with denormalized product data
    enriched_inventory = InventoryCreate(
        product_id=request_data.product_id,
        warehouse_id=request_data.warehouse_id,
        total_quantity=request_data.total_quantity,
        batch_number=request_data.batch_number,
        expiration_date=request_data.expiration_date,
        product_sku=product.sku,
        product_name=product.name,
        product_price=float(product.price),
        product_category=product.category,
    )

    return await inventory.create_inventory(enriched_inventory)


@router.get(
    "/inventories",
    response_model=PaginatedInventoriesResponse,
    responses={
        200: {"description": "List of inventories from inventory microservice"},
        422: {"description": "Invalid query parameters", "model": ValidationErrorResponse},
    },
)
async def get_inventories(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    sku: Optional[str] = Query(None),
    warehouse_id: Optional[UUID] = Query(None),
    inventory: InventoryPort = Depends(get_inventory_port),
    user: Dict = Depends(require_web_user),
):
    """
    Retrieve inventories from the inventory microservice with optional filters.

    Args:
        limit: Maximum number of inventories to return (1-100)
        offset: Number of inventories to skip
        sku: Optional product SKU filter
        warehouse_id: Optional warehouse ID filter
        inventory: Inventory port for service communication

    Returns:
        Paginated list of inventories (with denormalized product and warehouse data)
    """
    logger.info(f"Request: GET /inventories: limit={limit}, offset={offset}, sku={sku}, warehouse_id={warehouse_id}")
    return await inventory.get_inventories(
        limit=limit,
        offset=offset,
        sku=sku,
        warehouse_id=warehouse_id,
    )
