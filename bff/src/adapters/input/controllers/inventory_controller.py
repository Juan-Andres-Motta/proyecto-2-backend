from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from src.adapters.input.schemas import (
    InventoryCreate,
    PaginatedInventoriesResponse,
    PaginatedStoresResponse,
    StoreCreate,
)
from src.adapters.output.clients.http_client import HTTPClient
from src.infrastructure.config.settings import settings

router = APIRouter(tags=["inventories"])

# Create HTTP client for inventory service
inventory_client = HTTPClient(settings.inventory_url)


@router.post(
    "/inventory",
    responses={
        201: {
            "description": "Inventory created successfully",
        }
    },
)
async def create_inventory(inventory: InventoryCreate):
    response = await inventory_client.post("/inventory", inventory.model_dump())
    return JSONResponse(content=response, status_code=201)


@router.get(
    "/inventories",
    response_model=PaginatedInventoriesResponse,
    responses={
        200: {
            "description": "List of inventories with pagination",
        }
    },
)
async def list_inventories(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    params = {"limit": limit, "offset": offset}
    response = await inventory_client.get("/inventories", params)
    return response


@router.post(
    "/store",
    responses={
        201: {
            "description": "Store created successfully",
        }
    },
)
async def create_store(store: StoreCreate):
    response = await inventory_client.post("/store", store.model_dump())
    return JSONResponse(content=response, status_code=201)


@router.get(
    "/stores",
    response_model=PaginatedStoresResponse,
    responses={
        200: {
            "description": "List of stores with pagination",
        }
    },
)
async def list_stores(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    params = {"limit": limit, "offset": offset}
    response = await inventory_client.get("/stores", params)
    return response
