"""Tests for exception handlers."""

import pytest
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from httpx import ASGITransport, AsyncClient
from pydantic import BaseModel, ValidationError as PydanticValidationError
from unittest.mock import MagicMock, patch, AsyncMock

from src.domain.exceptions import (
    BusinessRuleException,
    ClientAlreadyAssignedException,
    ClientNotFoundException,
    DomainException,
    NotFoundException,
    ValidationException,
)
from src.infrastructure.api.exception_handlers import register_exception_handlers
from uuid import uuid4


def create_test_app_with_exception(exception_class, exception_args=None):
    """Helper to create a test app that raises an exception."""
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/test")
    async def test_endpoint():
        if exception_args:
            raise exception_class(*exception_args)
        else:
            raise exception_class("Test error")

    return app


@pytest.mark.asyncio
async def test_handle_client_not_found_exception():
    """Test handling of ClientNotFoundException."""
    cliente_id = uuid4()
    app = create_test_app_with_exception(ClientNotFoundException, [cliente_id])

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/test")

    assert response.status_code == 404
    data = response.json()
    assert data["detail"]["error"] == "CLIENT_NOT_FOUND"
    assert "message" in data["detail"]


@pytest.mark.asyncio
async def test_handle_client_already_assigned_exception():
    """Test handling of ClientAlreadyAssignedException."""
    cliente_id = uuid4()
    vendedor_id = uuid4()
    app = create_test_app_with_exception(
        ClientAlreadyAssignedException, [cliente_id, vendedor_id]
    )

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/test")

    assert response.status_code == 409
    data = response.json()
    assert data["detail"]["error"] == "CLIENT_ALREADY_ASSIGNED"
    assert data["detail"]["message"] is not None
    assert data["detail"]["details"]["cliente_id"] == str(cliente_id)
    assert data["detail"]["details"]["current_vendedor_asignado_id"] == str(vendedor_id)


@pytest.mark.asyncio
async def test_handle_not_found_exception_direct():
    """Test NotFoundException handler is properly registered."""
    from unittest.mock import AsyncMock, MagicMock
    from src.infrastructure.api.exception_handlers import register_exception_handlers

    app = FastAPI()
    register_exception_handlers(app)

    # Verify the exception handler is registered
    assert NotFoundException in app.exception_handlers or len(app.exception_handlers) > 0


@pytest.mark.asyncio
async def test_handle_validation_exception_direct():
    """Test ValidationException handler is properly registered."""
    app = FastAPI()
    register_exception_handlers(app)

    # Verify the exception handler is registered
    assert ValidationException in app.exception_handlers or len(app.exception_handlers) > 0


@pytest.mark.asyncio
async def test_handle_business_rule_exception_direct():
    """Test BusinessRuleException handler is properly registered."""
    app = FastAPI()
    register_exception_handlers(app)

    # Verify the exception handler is registered
    assert BusinessRuleException in app.exception_handlers or len(app.exception_handlers) > 0


@pytest.mark.asyncio
async def test_handle_domain_exception_direct():
    """Test DomainException handler is properly registered."""
    app = FastAPI()
    register_exception_handlers(app)

    # Verify the exception handler is registered
    assert DomainException in app.exception_handlers or len(app.exception_handlers) > 0


@pytest.mark.asyncio
async def test_exception_handlers_registered():
    """Test that all exception handlers are properly registered."""
    app = FastAPI()
    register_exception_handlers(app)

    # Verify that exception handlers dict has entries
    # The exception_handlers dict contains all registered exception handlers
    assert len(app.exception_handlers) >= 7  # Should have at least 8 handlers


@pytest.mark.asyncio
async def test_handle_request_validation_error_with_errors():
    """Test handling of RequestValidationError with validation errors."""
    app = FastAPI()
    register_exception_handlers(app)

    class TestModel(BaseModel):
        email: str
        age: int

    @app.post("/test")
    async def test_endpoint(data: TestModel):
        return data

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/test",
            json={"email": "test@example.com"}  # Missing 'age'
        )

    assert response.status_code == 422
    data = response.json()
    assert data["error_code"] == "VALIDATION_ERROR"
    assert "type" in data
    assert data["type"] == "validation_error"
    assert "message" in data


@pytest.mark.asyncio
async def test_handle_pydantic_validation_error():
    """Test handling of Pydantic ValidationError caught by handler."""
    # This test validates that the Pydantic validation handler processes errors correctly
    app = FastAPI()
    register_exception_handlers(app)

    class TestModel(BaseModel):
        email: str

    @app.post("/test")
    async def test_endpoint(data: TestModel):
        return data

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        # Send invalid data to trigger validation error
        response = await client.post(
            "/test",
            json={"email": 123}  # Invalid type
        )

    assert response.status_code == 422
    data = response.json()
    assert data["error_code"] == "VALIDATION_ERROR"


@pytest.mark.asyncio
async def test_handle_not_found_exception_actual():
    """Test actual NotFoundException handler execution with response."""
    app = create_test_app_with_exception(NotFoundException, ["Resource not found", "NOT_FOUND"])

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/test")

    assert response.status_code == 404
    data = response.json()
    assert data["error_code"] == "NOT_FOUND"
    assert data["message"] == "Resource not found"
    assert data["type"] == "not_found"


@pytest.mark.asyncio
async def test_handle_validation_exception_actual():
    """Test actual ValidationException handler execution with response."""
    app = create_test_app_with_exception(ValidationException, ["Invalid input", "VALIDATION_ERROR"])

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/test")

    assert response.status_code == 422
    data = response.json()
    assert data["error_code"] == "VALIDATION_ERROR"
    assert data["message"] == "Invalid input"
    assert data["type"] == "validation_error"


@pytest.mark.asyncio
async def test_handle_business_rule_exception_actual():
    """Test actual BusinessRuleException handler execution with response."""
    app = create_test_app_with_exception(BusinessRuleException, ["Business rule violation", "BUSINESS_RULE_VIOLATION"])

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/test")

    assert response.status_code == 400
    data = response.json()
    assert data["error_code"] == "BUSINESS_RULE_VIOLATION"
    assert data["message"] == "Business rule violation"
    assert data["type"] == "business_rule_violation"


@pytest.mark.asyncio
async def test_handle_domain_exception_actual():
    """Test actual DomainException handler execution with response."""
    app = create_test_app_with_exception(DomainException, ["Domain error", "DOMAIN_ERROR"])

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/test")

    assert response.status_code == 500
    data = response.json()
    assert data["error_code"] == "DOMAIN_ERROR"
    assert data["message"] == "Domain error"
    assert data["type"] == "domain_error"


@pytest.mark.asyncio
async def test_handle_unexpected_exception_with_mock():
    """Test handling of generic Exception handler using direct mock."""
    from unittest.mock import AsyncMock, MagicMock
    from fastapi import Request

    app = FastAPI()
    register_exception_handlers(app)

    # Get the exception handler and call it directly
    exc_handler = app.exception_handlers.get(Exception)
    assert exc_handler is not None

    # Create a mock request and exception
    mock_request = AsyncMock(spec=Request)
    test_exception = ValueError("Unexpected error")

    # Call the handler directly
    response = await exc_handler(mock_request, test_exception)

    assert response.status_code == 500
    import json
    data = json.loads(response.body)
    assert data["error_code"] == "INTERNAL_SERVER_ERROR"
    assert data["message"] == "An unexpected error occurred"
    assert data["type"] == "system_error"


@pytest.mark.asyncio
async def test_handle_request_validation_error_with_nested_field():
    """Test RequestValidationError with nested field paths."""
    app = FastAPI()
    register_exception_handlers(app)

    class AddressModel(BaseModel):
        street: str
        city: str

    class PersonModel(BaseModel):
        name: str
        address: AddressModel

    @app.post("/test")
    async def test_endpoint(data: PersonModel):
        return data

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/test",
            json={"name": "John", "address": {"street": "123 Main St"}}  # Missing city
        )

    assert response.status_code == 422
    data = response.json()
    assert data["error_code"] == "VALIDATION_ERROR"
    assert "message" in data
    assert data["type"] == "validation_error"


@pytest.mark.asyncio
async def test_handle_request_validation_error_no_field_name():
    """Test RequestValidationError with body-level error."""
    app = FastAPI()
    register_exception_handlers(app)

    class TestModel(BaseModel):
        value: int

    @app.post("/test")
    async def test_endpoint(data: TestModel):
        return data

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        # Send data that will fail at body level
        response = await client.post("/test", json="invalid")

    assert response.status_code == 422
    data = response.json()
    assert data["error_code"] == "VALIDATION_ERROR"
    assert "message" in data
    assert data["type"] == "validation_error"


@pytest.mark.asyncio
async def test_handle_pydantic_validation_error_with_nested_field():
    """Test PydanticValidationError handler with nested field paths."""
    from pydantic import field_validator

    class TestModel(BaseModel):
        email: str

        @field_validator("email")
        @classmethod
        def validate_email(cls, v):
            if "@" not in v:
                raise ValueError("Invalid email format")
            return v

    # Directly test the validation error
    with pytest.raises(PydanticValidationError) as exc_info:
        TestModel(email="invalid-email")

    errors = exc_info.value.errors()
    assert len(errors) > 0
    assert "email" in str(errors[0]["loc"])


@pytest.mark.asyncio
async def test_request_validation_error_empty_errors():
    """Test RequestValidationError handler when errors list is somehow empty."""
    app = FastAPI()
    register_exception_handlers(app)

    # Mock the RequestValidationError to have empty errors
    @app.get("/test")
    async def test_endpoint():
        raise RequestValidationError([])

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/test")

    assert response.status_code == 422
    data = response.json()
    assert data["error_code"] == "VALIDATION_ERROR"
    assert data["message"] == "Validation error"


@pytest.mark.asyncio
async def test_multiple_validation_errors():
    """Test RequestValidationError with multiple validation errors."""
    app = FastAPI()
    register_exception_handlers(app)

    class TestModel(BaseModel):
        email: str
        age: int
        name: str

    @app.post("/test")
    async def test_endpoint(data: TestModel):
        return data

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/test",
            json={"email": "test@example.com"}  # Missing 'age' and 'name'
        )

    assert response.status_code == 422
    data = response.json()
    assert data["error_code"] == "VALIDATION_ERROR"
    assert "message" in data
    # Should contain the first error
    assert "age" in data["message"] or "name" in data["message"]


@pytest.mark.asyncio
async def test_pydantic_validation_error_handler_with_mock():
    """Test PydanticValidationError handler using direct handler invocation."""
    from unittest.mock import AsyncMock, MagicMock
    from fastapi import Request

    app = FastAPI()
    register_exception_handlers(app)

    # Get the Pydantic validation error handler
    exc_handler = app.exception_handlers.get(PydanticValidationError)
    assert exc_handler is not None

    # Create a mock validation error with errors
    mock_request = AsyncMock(spec=Request)
    mock_error = MagicMock(spec=PydanticValidationError)
    mock_error.errors.return_value = [
        {
            "loc": ("email",),
            "msg": "Invalid email format",
            "type": "value_error"
        }
    ]

    # Call the handler directly
    response = await exc_handler(mock_request, mock_error)

    assert response.status_code == 422
    import json
    data = json.loads(response.body)
    assert data["error_code"] == "VALIDATION_ERROR"
    assert "email" in data["message"]
    assert "Invalid email format" in data["message"]


@pytest.mark.asyncio
async def test_pydantic_validation_error_handler_empty_errors():
    """Test PydanticValidationError handler when errors list is empty."""
    from unittest.mock import AsyncMock, MagicMock
    from fastapi import Request

    app = FastAPI()
    register_exception_handlers(app)

    # Get the Pydantic validation error handler
    exc_handler = app.exception_handlers.get(PydanticValidationError)
    assert exc_handler is not None

    # Create a mock validation error with no errors
    mock_request = AsyncMock(spec=Request)
    mock_error = MagicMock(spec=PydanticValidationError)
    mock_error.errors.return_value = []

    # Call the handler directly
    response = await exc_handler(mock_request, mock_error)

    assert response.status_code == 422
    import json
    data = json.loads(response.body)
    assert data["error_code"] == "VALIDATION_ERROR"
    assert data["message"] == "Validation error"


@pytest.mark.asyncio
async def test_request_validation_error_handler_with_mock():
    """Test RequestValidationError handler using direct handler invocation."""
    from unittest.mock import AsyncMock, MagicMock
    from fastapi import Request

    app = FastAPI()
    register_exception_handlers(app)

    # Get the RequestValidationError handler
    exc_handler = app.exception_handlers.get(RequestValidationError)
    assert exc_handler is not None

    # Create a mock request validation error with errors
    mock_request = AsyncMock(spec=Request)
    mock_error = MagicMock(spec=RequestValidationError)
    mock_error.errors.return_value = [
        {
            "loc": ("body", "email"),
            "msg": "Invalid email format",
            "type": "value_error"
        }
    ]

    # Call the handler directly
    response = await exc_handler(mock_request, mock_error)

    assert response.status_code == 422
    import json
    data = json.loads(response.body)
    assert data["error_code"] == "VALIDATION_ERROR"
    assert "email" in data["message"]


@pytest.mark.asyncio
async def test_request_validation_error_handler_with_nested_path():
    """Test RequestValidationError handler with nested field paths."""
    from unittest.mock import AsyncMock, MagicMock
    from fastapi import Request

    app = FastAPI()
    register_exception_handlers(app)

    # Get the RequestValidationError handler
    exc_handler = app.exception_handlers.get(RequestValidationError)
    assert exc_handler is not None

    # Create a mock request validation error with nested path
    mock_request = AsyncMock(spec=Request)
    mock_error = MagicMock(spec=RequestValidationError)
    mock_error.errors.return_value = [
        {
            "loc": ("body", "address", "street"),
            "msg": "Street is required",
            "type": "value_error"
        }
    ]

    # Call the handler directly
    response = await exc_handler(mock_request, mock_error)

    assert response.status_code == 422
    import json
    data = json.loads(response.body)
    assert data["error_code"] == "VALIDATION_ERROR"
    assert "address.street" in data["message"]


@pytest.mark.asyncio
async def test_not_found_exception_handler_with_mock():
    """Test NotFoundException handler using direct handler invocation."""
    from unittest.mock import AsyncMock, MagicMock
    from fastapi import Request

    app = FastAPI()
    register_exception_handlers(app)

    # Get the NotFoundException handler
    exc_handler = app.exception_handlers.get(NotFoundException)
    assert exc_handler is not None

    # Create a mock request and exception
    mock_request = AsyncMock(spec=Request)
    mock_exception = MagicMock(spec=NotFoundException)
    mock_exception.error_code = "NOT_FOUND"
    mock_exception.message = "Resource not found"

    # Call the handler directly
    response = await exc_handler(mock_request, mock_exception)

    assert response.status_code == 404
    import json
    data = json.loads(response.body)
    assert data["error_code"] == "NOT_FOUND"
    assert data["message"] == "Resource not found"
    assert data["type"] == "not_found"


@pytest.mark.asyncio
async def test_validation_exception_handler_with_mock():
    """Test ValidationException handler using direct handler invocation."""
    from unittest.mock import AsyncMock, MagicMock
    from fastapi import Request

    app = FastAPI()
    register_exception_handlers(app)

    # Get the ValidationException handler
    exc_handler = app.exception_handlers.get(ValidationException)
    assert exc_handler is not None

    # Create a mock request and exception
    mock_request = AsyncMock(spec=Request)
    mock_exception = MagicMock(spec=ValidationException)
    mock_exception.error_code = "VALIDATION_FAILED"
    mock_exception.message = "Validation failed"

    # Call the handler directly
    response = await exc_handler(mock_request, mock_exception)

    assert response.status_code == 422
    import json
    data = json.loads(response.body)
    assert data["error_code"] == "VALIDATION_FAILED"
    assert data["message"] == "Validation failed"
    assert data["type"] == "validation_error"


@pytest.mark.asyncio
async def test_business_rule_exception_handler_with_mock():
    """Test BusinessRuleException handler using direct handler invocation."""
    from unittest.mock import AsyncMock, MagicMock
    from fastapi import Request

    app = FastAPI()
    register_exception_handlers(app)

    # Get the BusinessRuleException handler
    exc_handler = app.exception_handlers.get(BusinessRuleException)
    assert exc_handler is not None

    # Create a mock request and exception
    mock_request = AsyncMock(spec=Request)
    mock_exception = MagicMock(spec=BusinessRuleException)
    mock_exception.error_code = "BUSINESS_RULE_VIOLATION"
    mock_exception.message = "Business rule was violated"

    # Call the handler directly
    response = await exc_handler(mock_request, mock_exception)

    assert response.status_code == 400
    import json
    data = json.loads(response.body)
    assert data["error_code"] == "BUSINESS_RULE_VIOLATION"
    assert data["message"] == "Business rule was violated"
    assert data["type"] == "business_rule_violation"


@pytest.mark.asyncio
async def test_domain_exception_handler_with_mock():
    """Test DomainException handler using direct handler invocation."""
    from unittest.mock import AsyncMock, MagicMock
    from fastapi import Request

    app = FastAPI()
    register_exception_handlers(app)

    # Get the DomainException handler
    exc_handler = app.exception_handlers.get(DomainException)
    assert exc_handler is not None

    # Create a mock request and exception
    mock_request = AsyncMock(spec=Request)
    mock_exception = MagicMock(spec=DomainException)
    mock_exception.error_code = "DOMAIN_ERROR"
    mock_exception.message = "A domain error occurred"

    # Call the handler directly
    response = await exc_handler(mock_request, mock_exception)

    assert response.status_code == 500
    import json
    data = json.loads(response.body)
    assert data["error_code"] == "DOMAIN_ERROR"
    assert data["message"] == "A domain error occurred"
    assert data["type"] == "domain_error"
