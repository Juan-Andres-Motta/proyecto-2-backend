"""Test error scenarios in product controller by mocking use case exceptions."""
import uuid
from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient
from fastapi import FastAPI

from src.adapters.input.controllers.product_controller import router
from src.domain.exceptions import (
    BusinessRuleException,
    NotFoundException,
    ValidationException,
)
from src.infrastructure.api.exception_handlers import register_exception_handlers
from src.infrastructure.database.config import get_db
from src.infrastructure.dependencies import (
    get_create_products_use_case,
    get_get_product_use_case,
)


@pytest.mark.asyncio
async def test_get_product_not_found_from_use_case(db_session):
    """Test that NotFoundException from use case returns 404."""
    app = FastAPI()
    register_exception_handlers(app)
    app.include_router(router, prefix="/catalog")

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    # Mock the use case to raise NotFoundException
    mock_use_case = AsyncMock()
    mock_use_case.execute.side_effect = NotFoundException(
        "Product not found", "PRODUCT_NOT_FOUND"
    )

    app.dependency_overrides[get_get_product_use_case] = lambda: mock_use_case

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        product_id = str(uuid.uuid4())
        response = await client.get(f"/catalog/product/{product_id}")

    assert response.status_code == 404
    data = response.json()
    assert data["error_code"] == "PRODUCT_NOT_FOUND"
    assert data["type"] == "not_found"
    assert "product not found" in data["message"].lower()


@pytest.mark.asyncio
async def test_create_products_validation_error_from_use_case(db_session):
    """Test that ValidationException from use case returns 422."""
    app = FastAPI()
    register_exception_handlers(app)
    app.include_router(router, prefix="/catalog")

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    # Mock the use case to raise ValidationException
    mock_use_case = AsyncMock()
    mock_use_case.execute.side_effect = ValidationException(
        "Invalid product data", "INVALID_PRODUCT_DATA"
    )

    app.dependency_overrides[get_create_products_use_case] = lambda: mock_use_case

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        request_data = {
            "products": [
                {
                    "provider_id": str(uuid.uuid4()),
                    "name": "Test Product",
                    "category": "medicamentos_especiales",
                    "sku": "SKU-001",
                    "price": "100.00",
                }
            ]
        }
        response = await client.post("/catalog/products", json=request_data)

    assert response.status_code == 422
    data = response.json()
    assert data["error_code"] == "INVALID_PRODUCT_DATA"
    assert data["type"] == "validation_error"
    assert "invalid product data" in data["message"].lower()


@pytest.mark.asyncio
async def test_create_products_business_rule_error_from_use_case(db_session):
    """Test that BusinessRuleException from use case returns 400."""
    app = FastAPI()
    register_exception_handlers(app)
    app.include_router(router, prefix="/catalog")

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    # Mock the use case to raise BusinessRuleException
    mock_use_case = AsyncMock()
    mock_use_case.execute.side_effect = BusinessRuleException(
        "Duplicate SKU found", "DUPLICATE_SKU"
    )

    app.dependency_overrides[get_create_products_use_case] = lambda: mock_use_case

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        request_data = {
            "products": [
                {
                    "provider_id": str(uuid.uuid4()),
                    "name": "Test Product",
                    "category": "medicamentos_especiales",
                    "sku": "SKU-001",
                    "price": "100.00",
                }
            ]
        }
        response = await client.post("/catalog/products", json=request_data)

    assert response.status_code == 400
    data = response.json()
    assert data["error_code"] == "DUPLICATE_SKU"
    assert data["type"] == "business_rule_violation"
    assert "duplicate sku" in data["message"].lower()
