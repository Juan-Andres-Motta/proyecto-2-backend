"""Tests for exception handlers to achieve full coverage."""

import pytest
from uuid import uuid4
from unittest.mock import AsyncMock
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from httpx import ASGITransport, AsyncClient

from src.domain.exceptions import (
    InsufficientInventoryException,
    InvalidReservationReleaseException,
    InventoryNotFoundException,
    ValidationException,
    BusinessRuleException,
    DomainException,
)
from src.infrastructure.api.exception_handlers import register_exception_handlers


class TestInsufficientInventoryExceptionHandler:
    """Test InsufficientInventoryException handler (lines 96-113)."""

    @pytest.mark.asyncio
    async def test_insufficient_inventory_exception_returns_409_with_details(self):
        """Test that InsufficientInventoryException returns 409 with details."""
        app = FastAPI()
        register_exception_handlers(app)

        inventory_id = uuid4()

        @app.get("/test-insufficient")
        async def test_endpoint():
            raise InsufficientInventoryException(
                inventory_id=inventory_id,
                requested=100,
                available=50,
                product_sku="MED-001",
            )

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/test-insufficient")

        assert response.status_code == 409
        data = response.json()
        assert data["error_code"] == "INSUFFICIENT_INVENTORY"
        assert "message" in data
        assert data["details"]["inventory_id"] == str(inventory_id)
        assert data["details"]["requested"] == 100
        assert data["details"]["available"] == 50
        assert data["details"]["product_sku"] == "MED-001"

    @pytest.mark.asyncio
    async def test_insufficient_inventory_exception_message_content(self):
        """Test the message content of InsufficientInventoryException."""
        app = FastAPI()
        register_exception_handlers(app)

        inventory_id = uuid4()

        @app.get("/test-message")
        async def test_endpoint():
            raise InsufficientInventoryException(
                inventory_id=inventory_id,
                requested=150,
                available=75,
                product_sku="SURG-001",
            )

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/test-message")

        data = response.json()
        # Message should contain meaningful error information
        assert isinstance(data["message"], str)
        assert len(data["message"]) > 0


class TestInvalidReservationReleaseExceptionHandler:
    """Test InvalidReservationReleaseException handler (lines 115-130)."""

    @pytest.mark.asyncio
    async def test_invalid_release_exception_returns_409_with_details(self):
        """Test that InvalidReservationReleaseException returns 409 with details."""
        app = FastAPI()
        register_exception_handlers(app)

        @app.get("/test-invalid-release")
        async def test_endpoint():
            raise InvalidReservationReleaseException(
                requested_release=50, currently_reserved=20
            )

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/test-invalid-release")

        assert response.status_code == 409
        data = response.json()
        assert data["error_code"] == "INVALID_RESERVATION_RELEASE"
        assert "message" in data
        assert data["details"]["requested_release"] == 50
        assert data["details"]["currently_reserved"] == 20

    @pytest.mark.asyncio
    async def test_invalid_release_exception_with_different_values(self):
        """Test InvalidReservationReleaseException with various values."""
        app = FastAPI()
        register_exception_handlers(app)

        test_cases = [
            (100, 50),
            (1, 0),
            (999, 100),
            (5000, 1000),
        ]

        for requested, reserved in test_cases:
            @app.get(f"/test-{requested}-{reserved}")
            async def test_endpoint():
                raise InvalidReservationReleaseException(
                    requested_release=requested, currently_reserved=reserved
                )

            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.get(f"/test-{requested}-{reserved}")

            assert response.status_code == 409
            data = response.json()
            assert data["details"]["requested_release"] == requested
            assert data["details"]["currently_reserved"] == reserved


class TestOtherExceptionHandlers:
    """Test other exception handlers for full coverage."""

    @pytest.mark.asyncio
    async def test_validation_exception_handler(self):
        """Test ValidationException handler."""
        app = FastAPI()
        register_exception_handlers(app)

        @app.get("/test-validation")
        async def test_endpoint():
            raise ValidationException(
                message="Invalid input data",
                error_code="VALIDATION_ERROR"
            )

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/test-validation")

        assert response.status_code == 422
        data = response.json()
        assert data["error_code"] == "VALIDATION_ERROR"

    @pytest.mark.asyncio
    async def test_business_rule_exception_handler(self):
        """Test BusinessRuleException handler."""
        app = FastAPI()
        register_exception_handlers(app)

        @app.get("/test-business-rule")
        async def test_endpoint():
            raise BusinessRuleException(
                message="Business rule violated",
                error_code="BUSINESS_RULE_ERROR"
            )

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/test-business-rule")

        assert response.status_code == 400
        data = response.json()
        assert data["error_code"] == "BUSINESS_RULE_ERROR"

    @pytest.mark.asyncio
    async def test_domain_exception_handler(self):
        """Test DomainException handler."""
        app = FastAPI()
        register_exception_handlers(app)

        @app.get("/test-domain")
        async def test_endpoint():
            raise DomainException(
                message="Domain error occurred",
                error_code="DOMAIN_ERROR"
            )

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/test-domain")

        assert response.status_code == 500
        data = response.json()
        assert data["error_code"] == "DOMAIN_ERROR"

    @pytest.mark.asyncio
    async def test_inventory_not_found_exception_handler(self):
        """Test InventoryNotFoundException handler."""
        app = FastAPI()
        register_exception_handlers(app)

        inventory_id = uuid4()

        @app.get("/test-not-found")
        async def test_endpoint():
            raise InventoryNotFoundException(inventory_id=inventory_id)

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/test-not-found")

        assert response.status_code == 404
        data = response.json()
        assert "message" in data

    @pytest.mark.asyncio
    async def test_validation_exception_with_custom_code(self):
        """Test ValidationException handler with custom error code."""
        app = FastAPI()
        register_exception_handlers(app)

        @app.get("/test-validation-custom")
        async def test_endpoint():
            raise ValidationException(
                message="Custom validation failed",
                error_code="CUSTOM_VALIDATION_ERROR"
            )

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/test-validation-custom")

        assert response.status_code == 422
        data = response.json()
        assert data["error_code"] == "CUSTOM_VALIDATION_ERROR"
        assert data["message"] == "Custom validation failed"
