"""
Products controller.

This controller handles product-related endpoints using the catalog port
for communication with the catalog microservice.
"""

import logging

from fastapi import APIRouter, Depends, File, Query, UploadFile, status

from dependencies import get_catalog_port

from ..ports import CatalogPort
from ..schemas import BatchProductsResponse, PaginatedProductsResponse, ProductCreate
from ..services.csv_parser import CsvParserService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/products",
    response_model=BatchProductsResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"description": "Product created successfully"},
        400: {"description": "Invalid product data"},
        404: {"description": "Provider not found"},
        500: {"description": "Error communicating with catalog microservice"},
    },
)
async def create_product(
    product: ProductCreate,
    catalog: CatalogPort = Depends(get_catalog_port),
):
    """
    Create a single product.

    This endpoint accepts a single product and sends it as a batch of size 1
    to the catalog microservice.

    Args:
        product: Product data to create
        catalog: Catalog port for service communication

    Returns:
        Response with the created product
    """
    logger.info(f"Request: POST /products: name='{product.name}', sku='{product.sku}'")
    return await catalog.create_products([product])


@router.post(
    "/products/batch",
    response_model=BatchProductsResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"description": "Products created successfully from CSV"},
        400: {"description": "Invalid CSV format or product data"},
        404: {"description": "Provider not found"},
        422: {"description": "CSV parsing error"},
        500: {"description": "Error communicating with catalog microservice"},
    },
)
async def create_products_from_csv(
    file: UploadFile = File(...),
    catalog: CatalogPort = Depends(get_catalog_port),
):
    """
    Create multiple products from a CSV file.

    The CSV file must have the following columns:
    - provider_id (UUID)
    - name (string)
    - category (medicamentos_especiales, insumos_quirurgicos, reactivos_diagnosticos, equipos_biomedicos, otros)
    - sku (string - unique identifier)
    - price (decimal)

    All products are created in a single transaction in the catalog service.
    If any product fails validation or creation, all products are rolled back.

    Args:
        file: CSV file with product data
        catalog: Catalog port for service communication

    Returns:
        Response with all created products
    """
    logger.info(f"Request: POST /products/batch: filename='{file.filename}'")
    products = await CsvParserService.parse_products_from_csv(file)
    return await catalog.create_products(products)


@router.get(
    "/products",
    response_model=PaginatedProductsResponse,
    responses={
        200: {"description": "List of products from catalog microservice"},
        500: {"description": "Error communicating with catalog microservice"},
    },
)
async def get_products(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    catalog: CatalogPort = Depends(get_catalog_port),
):
    """
    Retrieve products from the catalog microservice.

    Args:
        limit: Maximum number of products to return (1-100)
        offset: Number of products to skip
        catalog: Catalog port for service communication

    Returns:
        Paginated list of products
    """
    logger.info(f"Request: GET /products: limit={limit}, offset={offset}")
    return await catalog.get_products(limit=limit, offset=offset)
