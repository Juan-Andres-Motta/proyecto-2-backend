"""Test error scenarios in provider controller by mocking use case exceptions."""
import uuid
from unittest.mock import AsyncMock, patch, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient
from fastapi import FastAPI

from src.adapters.input.controllers.provider_controller import router
from src.domain.exceptions import BusinessRuleException, ValidationException
from src.infrastructure.api.exception_handlers import register_exception_handlers
from src.infrastructure.database.config import get_db


@pytest.mark.asyncio
async def test_create_provider_validation_error_from_use_case(db_session):
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
        "Invalid email format", "INVALID_EMAIL"
    )

    from src.infrastructure.dependencies import get_create_provider_use_case
    app.dependency_overrides[get_create_provider_use_case] = lambda: mock_use_case

    # Mock country validation to bypass pycountry library
    with patch("src.adapters.input.schemas.provider_schemas.pycountry") as mock_pycountry:
        mock_country = MagicMock()
        mock_country.name = "United States"
        mock_pycountry.countries.lookup.return_value = mock_country

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            request_data = {
                "name": "Test Provider",
                "nit": "123456789",
                "contact_name": "John Doe",
                "email": "test@example.com",
                "phone": "+1234567890",
                "address": "123 Test St",
                "country": "United States",
            }
            response = await client.post("/catalog/provider", json=request_data)

    assert response.status_code == 422
    data = response.json()
    assert data["error_code"] == "INVALID_EMAIL"
    assert data["type"] == "validation_error"
    assert "email" in data["message"].lower()


@pytest.mark.asyncio
async def test_create_provider_duplicate_nit_from_use_case(db_session):
    """Test that BusinessRuleException for duplicate NIT returns 400."""
    app = FastAPI()
    register_exception_handlers(app)
    app.include_router(router, prefix="/catalog")

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    # Mock the use case to raise BusinessRuleException
    mock_use_case = AsyncMock()
    mock_use_case.execute.side_effect = BusinessRuleException(
        "Provider with NIT 123456789 already exists", "DUPLICATE_NIT"
    )

    from src.infrastructure.dependencies import get_create_provider_use_case
    app.dependency_overrides[get_create_provider_use_case] = lambda: mock_use_case

    # Mock country validation to bypass pycountry library
    with patch("src.adapters.input.schemas.provider_schemas.pycountry") as mock_pycountry:
        mock_country = MagicMock()
        mock_country.name = "United States"
        mock_pycountry.countries.lookup.return_value = mock_country

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            request_data = {
                "name": "Test Provider",
                "nit": "123456789",
                "contact_name": "John Doe",
                "email": "john@test.com",
                "phone": "+1234567890",
                "address": "123 Test St",
                "country": "United States",
            }
            response = await client.post("/catalog/provider", json=request_data)

    assert response.status_code == 400
    data = response.json()
    assert data["error_code"] == "DUPLICATE_NIT"
    assert data["type"] == "business_rule_violation"
    assert "duplicate" in data["message"].lower() or "already exists" in data["message"].lower()
