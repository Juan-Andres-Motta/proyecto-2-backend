"""
Additional edge case tests for ExceptionHandlerMiddleware.

Tests error handling edge cases not covered in basic middleware tests.
"""

import pytest
from unittest.mock import AsyncMock, Mock
from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError as PydanticValidationError

from common.middleware import ExceptionHandlerMiddleware, setup_exception_handlers
from common.exceptions import (
    BFFException,
    MicroserviceConnectionError,
    MicroserviceHTTPError,
)


@pytest.fixture
def middleware():
    """Create an ExceptionHandlerMiddleware instance."""
    return ExceptionHandlerMiddleware(app=AsyncMock())


@pytest.fixture
def mock_request():
    """Create a mock Request."""
    request = Mock(spec=Request)
    request.url.path = "/test/path"
    request.method = "POST"
    return request


class TestExceptionHandlerMiddlewareEdgeCases:
    """Tests for edge cases in exception handling."""

    @pytest.mark.asyncio
    async def test_handle_microservice_connection_error(self, middleware, mock_request):
        """Test handling of MicroserviceConnectionError."""
        exc = MicroserviceConnectionError(
            "inventory",
            original_error="Connection refused"
        )

        response = middleware._handle_bff_exception(exc, mock_request)

        assert response.status_code == 503
        body = response.body.decode()
        assert "inventory" in body
        assert "Unable to connect" in body

    @pytest.mark.asyncio
    async def test_handle_microservice_http_error(self, middleware, mock_request):
        """Test handling of MicroserviceHTTPError."""
        exc = MicroserviceHTTPError(
            "catalog",
            404,
            response_text="Not found"
        )

        response = middleware._handle_bff_exception(exc, mock_request)

        assert response.status_code == 404
        body = response.body.decode()
        assert "catalog" in body

    @pytest.mark.asyncio
    async def test_handle_bff_exception_with_empty_details(self, middleware, mock_request):
        """Test BFF exception handling with empty details."""
        exc = BFFException("Test error", status_code=400, details={})

        response = middleware._handle_bff_exception(exc, mock_request)

        assert response.status_code == 400
        body = response.body.decode()
        assert "Test error" in body

    @pytest.mark.asyncio
    async def test_handle_bff_exception_with_nested_details(self, middleware, mock_request):
        """Test BFF exception handling with nested details."""
        exc = BFFException(
            "Validation error",
            status_code=400,
            details={
                "fields": {
                    "email": "Invalid email format",
                    "password": "Too short"
                }
            }
        )

        response = middleware._handle_bff_exception(exc, mock_request)

        assert response.status_code == 400
        body = response.body.decode()
        assert "email" in body

    @pytest.mark.asyncio
    async def test_handle_request_validation_error_with_empty_errors(
        self, middleware, mock_request
    ):
        """Test request validation error with empty errors list."""
        exc = RequestValidationError([])

        response = middleware._handle_request_validation_error(exc, mock_request)

        assert response.status_code == 422
        body = response.body.decode()
        assert "Validation error" in body

    @pytest.mark.asyncio
    async def test_handle_pydantic_validation_error_with_empty_errors(
        self, middleware, mock_request
    ):
        """Test pydantic validation error with empty errors list."""
        exc = PydanticValidationError.from_exception_data("test", [])

        response = middleware._handle_pydantic_validation_error(exc, mock_request)

        assert response.status_code == 422
        body = response.body.decode()
        assert "Validation error" in body

    @pytest.mark.asyncio
    async def test_handle_unexpected_exception(self, middleware, mock_request):
        """Test handling of unexpected exceptions."""
        exc = RuntimeError("Unexpected error occurred")

        response = middleware._handle_unexpected_exception(exc, mock_request)

        assert response.status_code == 500
        body = response.body.decode()
        assert "INTERNAL_SERVER_ERROR" in body

    @pytest.mark.asyncio
    async def test_dispatch_with_bff_exception(self, middleware, mock_request):
        """Test dispatch method handling BFF exception."""
        call_next_mock = AsyncMock(side_effect=BFFException("Test error", 400))

        response = await middleware.dispatch(mock_request, call_next_mock)

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_dispatch_with_general_exception(self, middleware, mock_request):
        """Test dispatch method handling unexpected exception."""
        call_next_mock = AsyncMock(side_effect=ValueError("Test error"))

        response = await middleware.dispatch(mock_request, call_next_mock)

        assert response.status_code == 500

    @pytest.mark.asyncio
    async def test_dispatch_with_successful_response(self, middleware, mock_request):
        """Test dispatch method with successful response."""
        expected_response = Mock()
        expected_response.status_code = 200
        call_next_mock = AsyncMock(return_value=expected_response)

        response = await middleware.dispatch(mock_request, call_next_mock)

        assert response.status_code == 200
        assert response is expected_response


class TestSetupExceptionHandlers:
    """Tests for setup_exception_handlers function."""

    def test_setup_exception_handlers_registers_middleware(self):
        """Test that setup_exception_handlers registers the middleware."""
        app = Mock()
        app.add_middleware = Mock()

        setup_exception_handlers(app)

        app.add_middleware.assert_called_once()
        # Verify ExceptionHandlerMiddleware was passed
        args = app.add_middleware.call_args[0]
        assert args[0] == ExceptionHandlerMiddleware

    def test_setup_exception_handlers_with_real_app(self):
        """Test setup_exception_handlers with minimal FastAPI app."""
        from fastapi import FastAPI

        app = FastAPI()

        # Should not raise any exceptions
        setup_exception_handlers(app)

        # Verify middleware was added
        assert len(app.user_middleware) > 0
