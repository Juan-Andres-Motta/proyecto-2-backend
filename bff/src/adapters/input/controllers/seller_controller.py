from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from src.adapters.input.schemas import (
    PaginatedSalesPlansResponse,
    PaginatedSellersResponse,
    SalesPlanCreate,
    SellerCreate,
)
from src.adapters.output.clients.http_client import HTTPClient
from src.infrastructure.config.settings import settings

router = APIRouter(tags=["sellers"])

# Create HTTP client for seller service
seller_client = HTTPClient(settings.seller_url)


@router.post(
    "/sellers",
    responses={
        201: {
            "description": "Seller created successfully",
        }
    },
)
async def create_seller(seller: SellerCreate):
    response = await seller_client.post("/sellers", seller.model_dump())
    return JSONResponse(content=response, status_code=201)


@router.get(
    "/sellers",
    response_model=PaginatedSellersResponse,
    responses={
        200: {
            "description": "List of sellers with pagination",
        }
    },
)
async def list_sellers(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    params = {"limit": limit, "offset": offset}
    response = await seller_client.get("/sellers", params)
    return response


@router.post(
    "/sales-plans",
    responses={
        201: {
            "description": "Sales plan created successfully",
        }
    },
)
async def create_sales_plan(sales_plan: SalesPlanCreate):
    response = await seller_client.post("/sales-plans", sales_plan.model_dump())
    return JSONResponse(content=response, status_code=201)


@router.get(
    "/sales-plans",
    response_model=PaginatedSalesPlansResponse,
    responses={
        200: {
            "description": "List of sales plans with pagination",
        }
    },
)
async def list_sales_plans(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    params = {"limit": limit, "offset": offset}
    response = await seller_client.get("/sales-plans", params)
    return response
