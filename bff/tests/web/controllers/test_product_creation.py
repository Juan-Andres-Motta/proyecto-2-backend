import io
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from web.controllers.products_controller import router
from web.schemas import ProductCategory


@pytest.mark.asyncio
async def test_create_product_success():
    """Test successful single product creation."""
    app = FastAPI()
    app.include_router(router)

    product_request = {
        "provider_id": "550e8400-e29b-41d4-a716-446655440000",
        "name": "New Product",
        "category": ProductCategory.SPECIAL_MEDICATIONS.value,
        "sku": "NEW-PROD-001",
        "price": "150.00",
    }

    mock_response = {
        "created": [
            {
                "id": "660e8400-e29b-41d4-a716-446655440000",
                "provider_id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "New Product",
                "category": "Medicamentos Especiales",  # Human-readable from catalog
                "sku": "NEW-PROD-001",
                "price": "150.00",
                "created_at": "2025-01-15T10:30:00Z",
                "updated_at": "2025-01-15T10:30:00Z",
            }
        ],
        "count": 1,
    }

    with patch(
        "web.controllers.products_controller.CatalogService"
    ) as MockCatalogService:
        mock_service = MockCatalogService.return_value
        mock_service.create_products = AsyncMock(return_value=mock_response)

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post("/products", json=product_request)

        assert response.status_code == 201
        data = response.json()
        assert "created" in data
        assert "count" in data
        assert len(data["created"]) == 1
        assert data["count"] == 1
        assert data["created"][0]["name"] == "New Product"

        # Verify the service was called with array of size 1
        mock_service.create_products.assert_called_once()
        call_args = mock_service.create_products.call_args[0][0]
        assert len(call_args) == 1


@pytest.mark.asyncio
async def test_create_product_invalid_category():
    """Test product creation with invalid category."""
    app = FastAPI()
    app.include_router(router)

    product_request = {
        "provider_id": "550e8400-e29b-41d4-a716-446655440000",
        "name": "New Product",
        "category": "invalid_category",
        "sku": "NEW-PROD-002",
        "price": "150.00",
    }

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post("/products", json=product_request)

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_product_provider_not_found():
    """Test product creation when provider doesn't exist."""
    from httpx import HTTPStatusError, Response, Request

    app = FastAPI()
    app.include_router(router)

    product_request = {
        "provider_id": "550e8400-e29b-41d4-a716-446655440000",
        "name": "New Product",
        "category": ProductCategory.OTHER.value,
        "sku": "NEW-PROD-003",
        "price": "150.00",
    }

    # Create a mock response with 404 status
    mock_request = Request("POST", "http://test/products")
    mock_response = Response(404, text="Provider not found")

    with patch(
        "web.controllers.products_controller.CatalogService"
    ) as MockCatalogService:
        mock_service = MockCatalogService.return_value
        mock_service.create_products = AsyncMock(
            side_effect=HTTPStatusError(
                "Provider not found", request=mock_request, response=mock_response
            )
        )

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post("/products", json=product_request)

        assert response.status_code == 404
        assert "provider" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_create_products_from_csv_success():
    """Test successful CSV batch product creation."""
    app = FastAPI()
    app.include_router(router)

    # Create CSV content
    csv_content = """provider_id,name,category,sku,price
550e8400-e29b-41d4-a716-446655440000,Product 1,medicamentos_especiales,PROD-001,100.00
550e8400-e29b-41d4-a716-446655440000,Product 2,insumos_quirurgicos,PROD-002,200.00
"""

    mock_response = {
        "created": [
            {
                "id": "660e8400-e29b-41d4-a716-446655440001",
                "provider_id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "Product 1",
                "category": "Medicamentos Especiales",  # Human-readable from catalog
                "sku": "PROD-001",
                "price": "100.00",
                "created_at": "2025-01-15T10:30:00Z",
                "updated_at": "2025-01-15T10:30:00Z",
            },
            {
                "id": "660e8400-e29b-41d4-a716-446655440002",
                "provider_id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "Product 2",
                "category": "Insumos Quirúrgicos",  # Human-readable from catalog
                "sku": "PROD-002",
                "price": "200.00",
                "created_at": "2025-01-15T10:30:00Z",
                "updated_at": "2025-01-15T10:30:00Z",
            },
        ],
        "count": 2,
    }

    with patch(
        "web.controllers.products_controller.CatalogService"
    ) as MockCatalogService:
        mock_service = MockCatalogService.return_value
        mock_service.create_products = AsyncMock(return_value=mock_response)

        csv_file = io.BytesIO(csv_content.encode("utf-8"))
        files = {"file": ("products.csv", csv_file, "text/csv")}

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post("/products/batch", files=files)

        assert response.status_code == 201
        data = response.json()
        assert "created" in data
        assert "count" in data
        assert len(data["created"]) == 2
        assert data["count"] == 2

        # Verify the service was called with correct data
        mock_service.create_products.assert_called_once()
        call_args = mock_service.create_products.call_args[0][0]
        assert len(call_args) == 2
        assert call_args[0]["name"] == "Product 1"
        assert call_args[1]["name"] == "Product 2"


@pytest.mark.asyncio
async def test_create_products_from_csv_invalid_file_type():
    """Test CSV upload with non-CSV file."""
    app = FastAPI()
    app.include_router(router)

    txt_file = io.BytesIO(b"not a csv")
    files = {"file": ("products.txt", txt_file, "text/plain")}

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post("/products/batch", files=files)

    assert response.status_code == 400
    assert "csv" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_create_products_from_csv_invalid_row():
    """Test CSV upload with invalid data in a row."""
    app = FastAPI()
    app.include_router(router)

    # CSV with invalid category in second row
    csv_content = """provider_id,name,category,sku,price
550e8400-e29b-41d4-a716-446655440000,Product 1,medicamentos_especiales,PROD-001,100.00
550e8400-e29b-41d4-a716-446655440000,Product 2,invalid_category,PROD-002,200.00
"""

    csv_file = io.BytesIO(csv_content.encode("utf-8"))
    files = {"file": ("products.csv", csv_file, "text/csv")}

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post("/products/batch", files=files)

    assert response.status_code == 422
    assert "row 3" in response.json()["detail"].lower()  # Row 3 because header is row 1


@pytest.mark.asyncio
async def test_create_products_from_csv_empty():
    """Test CSV upload with empty file."""
    app = FastAPI()
    app.include_router(router)

    # CSV with only header
    csv_content = """provider_id,name,category,sku,price
"""

    csv_file = io.BytesIO(csv_content.encode("utf-8"))
    files = {"file": ("products.csv", csv_file, "text/csv")}

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post("/products/batch", files=files)

    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_create_products_from_csv_transaction_rollback():
    """Test CSV upload rolls back on catalog service error."""
    from httpx import HTTPStatusError, Response, Request

    app = FastAPI()
    app.include_router(router)

    csv_content = """provider_id,name,category,sku,price
550e8400-e29b-41d4-a716-446655440000,Product 1,medicamentos_especiales,PROD-001,100.00
"""

    # Create a mock response with 400 status (e.g., provider not found)
    mock_request = Request("POST", "http://test/products")
    mock_response = Response(400, text="Product creation failed")

    with patch(
        "web.controllers.products_controller.CatalogService"
    ) as MockCatalogService:
        mock_service = MockCatalogService.return_value
        mock_service.create_products = AsyncMock(
            side_effect=HTTPStatusError(
                "Product creation failed",
                request=mock_request,
                response=mock_response,
            )
        )

        csv_file = io.BytesIO(csv_content.encode("utf-8"))
        files = {"file": ("products.csv", csv_file, "text/csv")}

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post("/products/batch", files=files)

        assert response.status_code == 400
        assert "rolled back" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_create_products_from_csv_invalid_encoding():
    """Test CSV upload with invalid encoding."""
    app = FastAPI()
    app.include_router(router)

    # Invalid UTF-8 bytes
    invalid_content = b"\xff\xfe\xfd"

    csv_file = io.BytesIO(invalid_content)
    files = {"file": ("products.csv", csv_file, "text/csv")}

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post("/products/batch", files=files)

    assert response.status_code == 400
    assert "encoding" in response.json()["detail"].lower()
