import csv
import io
from typing import List

from fastapi import APIRouter, File, HTTPException, Query, UploadFile, status
import httpx

from ..schemas import BatchProductsResponse, PaginatedProductsResponse, ProductCreate
from ..services import CatalogService

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
async def create_product(product: ProductCreate):
    """
    Create a single product.

    This endpoint accepts a single product and sends it as a batch of size 1
    to the catalog microservice.

    Args:
        product: Product data to create

    Returns:
        Response with the created product
    """
    try:
        catalog_service = CatalogService()

        # Send as array of size 1 (mode='json' converts UUIDs to strings)
        products_data = await catalog_service.create_products([product.model_dump(mode='json')])

        return products_data
    except httpx.HTTPStatusError as e:
        error_detail = e.response.text if e.response else "Unknown error"

        if e.response.status_code == 404:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Provider not found. Please verify the provider_id exists.",
            )
        elif e.response.status_code == 400:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid product data: {error_detail}",
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Catalog service error: {error_detail}",
            )
    except httpx.RequestError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to connect to catalog service",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}",
        )


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
async def create_products_from_csv(file: UploadFile = File(...)):
    """
    Create multiple products from a CSV file.

    The CSV file must have the following columns:
    - provider_id (UUID)
    - name (string)
    - category (medicamentos_especiales, insumos_quirurgicos, reactivos_diagnosticos, equipos_biomedicos, otros)
    - description (string)
    - price (decimal)
    - status (optional: activo, descontinuado, pendiente_aprobacion - defaults to pendiente_aprobacion)

    All products are created in a single transaction in the catalog service.
    If any product fails validation or creation, all products are rolled back.

    Args:
        file: CSV file with product data

    Returns:
        Response with all created products
    """
    # Validate file type
    if not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be a CSV file",
        )

    try:
        # Read CSV content
        contents = await file.read()
        csv_text = contents.decode('utf-8')
        csv_file = io.StringIO(csv_text)
        csv_reader = csv.DictReader(csv_file)

        # Parse products from CSV
        products: List[dict] = []
        for row_number, row in enumerate(csv_reader, start=2):  # start=2 because row 1 is header
            try:
                # Build product dict with required fields
                product_data = {
                    "provider_id": row.get("provider_id", "").strip(),
                    "name": row.get("name", "").strip(),
                    "category": row.get("category", "").strip(),
                    "description": row.get("description", "").strip(),
                    "price": row.get("price", "").strip(),
                    "status": row.get("status", "pendiente_aprobacion").strip() or "pendiente_aprobacion",
                }

                # Validate with Pydantic (mode='json' converts UUIDs to strings)
                product = ProductCreate(**product_data)
                products.append(product.model_dump(mode='json'))

            except ValueError as e:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"CSV row {row_number}: Invalid data - {str(e)}",
                )
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"CSV row {row_number}: {str(e)}",
                )

        if not products:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="CSV file is empty or contains no valid products",
            )

        # Send to catalog service
        catalog_service = CatalogService()
        products_data = await catalog_service.create_products(products)

        return products_data

    except UnicodeDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid CSV encoding. Please use UTF-8 encoding.",
        )
    except csv.Error as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"CSV parsing error: {str(e)}",
        )
    except httpx.HTTPStatusError as e:
        error_detail = e.response.text if e.response else "Unknown error"

        if e.response.status_code == 404:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Provider not found in one of the products: {error_detail}",
            )
        elif e.response.status_code == 400:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Product creation failed, all changes rolled back: {error_detail}",
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Catalog service error: {error_detail}",
            )
    except httpx.RequestError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to connect to catalog service",
        )
    except HTTPException:
        raise  # Re-raise HTTPExceptions as-is
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}",
        )


@router.get(
    "/products",
    response_model=PaginatedProductsResponse,
    responses={
        200: {
            "description": "List of products from catalog microservice"
        },
        500: {"description": "Error communicating with catalog microservice"},
    },
)
async def get_products(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """
    Retrieve products from the catalog microservice.

    Args:
        limit: Maximum number of products to return (1-100)
        offset: Number of products to skip

    Returns:
        Paginated list of products
    """
    try:
        catalog_service = CatalogService()
        products_data = await catalog_service.get_products(
            limit=limit, offset=offset
        )
        return products_data
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching products: Catalog service returned {e.response.status_code}",
        )
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching products: Unable to connect to catalog service",
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching products: {type(e).__name__}",
        )
