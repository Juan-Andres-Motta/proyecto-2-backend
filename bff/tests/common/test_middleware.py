"""
Unit tests for exception handling middleware.

Tests OUR logic:
- Mapping exceptions to HTTP responses
"""

import json
from unittest.mock import AsyncMock, Mock
import pytest
from fastapi import Request, Response
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError as PydanticValidationError

from common.exceptions import (
    BFFException,
    ValidationError,
    MicroserviceTimeoutError,
    MicroserviceConnectionError,
    MicroserviceHTTPError,
)
from common.middleware import ExceptionHandlerMiddleware


@pytest.fixture
def middleware():
    """Create middleware instance."""
    return ExceptionHandlerMiddleware(app=Mock())


@pytest.fixture
def mock_request():
    """Create a mock request."""
    request = Mock(spec=Request)
    request.url.path = "/test"
    request.method = "GET"
    return request


class TestExceptionHandlerMiddlewareMapsBFFException:
    """Test middleware maps BFFException to JSON response."""

    @pytest.mark.asyncio
    async def test_maps_bff_exception_to_json(self, middleware, mock_request):
        """Test that BFFException is mapped to JSON response."""
        async def call_next(request):
            raise BFFException("Test error", status_code=400)

        response = await middleware.dispatch(mock_request, call_next)

        assert response.status_code == 400
        assert b"Test error" in response.body


class TestExceptionHandlerMiddlewareMapsMicroserviceExceptions:
    """Test middleware maps microservice exceptions."""

    @pytest.mark.asyncio
    async def test_maps_timeout_to_504(self, middleware, mock_request):
        """Test that MicroserviceTimeoutError is mapped to 504."""
        async def call_next(request):
            raise MicroserviceTimeoutError("test-service", 10.0)

        response = await middleware.dispatch(mock_request, call_next)

        assert response.status_code == 504

    @pytest.mark.asyncio
    async def test_maps_connection_error_to_503(self, middleware, mock_request):
        """Test that MicroserviceConnectionError is mapped to 503."""
        async def call_next(request):
            raise MicroserviceConnectionError("test-service")

        response = await middleware.dispatch(mock_request, call_next)

        assert response.status_code == 503

    @pytest.mark.asyncio
    async def test_maps_validation_error_to_400(self, middleware, mock_request):
        """Test that ValidationError is mapped to 400."""
        async def call_next(request):
            raise ValidationError("Validation failed")

        response = await middleware.dispatch(mock_request, call_next)

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_maps_http_error_preserves_status(self, middleware, mock_request):
        """Test that MicroserviceHTTPError preserves status code."""
        async def call_next(request):
            raise MicroserviceHTTPError("test-service", 404, "Not found")

        response = await middleware.dispatch(mock_request, call_next)

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_handles_unexpected_exception(self, middleware, mock_request):
        """Test that unexpected exceptions are mapped to 500."""
        async def call_next(request):
            raise Exception("Unexpected error")

        response = await middleware.dispatch(mock_request, call_next)

        assert response.status_code == 500

        # Verify standardized error format
        body = json.loads(response.body.decode())
        assert body["error_code"] == "INTERNAL_SERVER_ERROR"
        assert body["message"] == "An unexpected error occurred"
        assert body["type"] == "system_error"


class TestExceptionHandlerMiddlewareMapsValidationErrors:
    """Test middleware maps Pydantic validation errors to standardized format."""

    @pytest.mark.asyncio
    async def test_maps_request_validation_error_to_422(self, middleware, mock_request):
        """Test that RequestValidationError is mapped to 422 with standardized format."""
        async def call_next(request):
            # Simulate FastAPI RequestValidationError
            raise RequestValidationError(errors=[
                {
                    "loc": ("body", "price"),
                    "msg": "Input should be greater than 0",
                    "type": "greater_than"
                }
            ])

        response = await middleware.dispatch(mock_request, call_next)

        assert response.status_code == 422

        # Verify standardized error format
        body = json.loads(response.body.decode())
        assert body["error_code"] == "VALIDATION_ERROR"
        assert "price" in body["message"]
        assert body["type"] == "validation_error"

    @pytest.mark.asyncio
    async def test_maps_pydantic_validation_error_to_422(self, middleware, mock_request):
        """Test that PydanticValidationError is mapped to 422 with standardized format."""
        async def call_next(request):
            # Simulate Pydantic ValidationError
            from pydantic import BaseModel, Field

            class TestModel(BaseModel):
                price: float = Field(gt=0)

            try:
                TestModel(price=-10)
            except PydanticValidationError as e:
                raise e

        response = await middleware.dispatch(mock_request, call_next)

        assert response.status_code == 422

        # Verify standardized error format
        body = json.loads(response.body.decode())
        assert body["error_code"] == "VALIDATION_ERROR"
        assert body["type"] == "validation_error"
        assert "message" in body
