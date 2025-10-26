import json

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from pydantic import BaseModel, field_validator
from pydantic_core import ValidationError as PydanticValidationError

from src.domain.exceptions import (
    BusinessRuleException,
    DomainException,
    NotFoundException,
    ValidationException,
)
from src.infrastructure.api.exception_handlers import register_exception_handlers


@pytest.mark.asyncio
async def test_not_found_exception():
    """Test NotFoundException returns 404."""
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/test")
    async def test_endpoint():
        raise NotFoundException("Test not found", "TEST_NOT_FOUND")

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/test")

    assert response.status_code == 404
    data = response.json()
    assert data["error_code"] == "TEST_NOT_FOUND"
    assert data["type"] == "not_found"
    assert "not found" in data["message"].lower()


@pytest.mark.asyncio
async def test_validation_exception():
    """Test ValidationException returns 422."""
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/test")
    async def test_endpoint():
        raise ValidationException("Validation failed", "TEST_VALIDATION_ERROR")

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/test")

    assert response.status_code == 422
    data = response.json()
    assert data["error_code"] == "TEST_VALIDATION_ERROR"
    assert data["type"] == "validation_error"
    assert "validation failed" in data["message"].lower()


@pytest.mark.asyncio
async def test_business_rule_exception():
    """Test BusinessRuleException returns 400."""
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/test")
    async def test_endpoint():
        raise BusinessRuleException("Business rule violated", "BUSINESS_RULE_VIOLATION")

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/test")

    assert response.status_code == 400
    data = response.json()
    assert data["error_code"] == "BUSINESS_RULE_VIOLATION"
    assert data["type"] == "business_rule_violation"
    assert "business rule" in data["message"].lower()


@pytest.mark.asyncio
async def test_domain_exception():
    """Test DomainException returns 500."""
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/test")
    async def test_endpoint():
        raise DomainException("Domain error occurred", "DOMAIN_ERROR")

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/test")

    assert response.status_code == 500
    data = response.json()
    assert data["error_code"] == "DOMAIN_ERROR"
    assert data["type"] == "domain_error"
    assert "domain error" in data["message"].lower()


@pytest.mark.asyncio
async def test_pydantic_validation_error():
    """Test Pydantic validation error returns 422 with proper formatting."""
    app = FastAPI()
    register_exception_handlers(app)

    class TestModel(BaseModel):
        email: str

        @field_validator('email')
        @classmethod
        def validate_email(cls, v):
            if '@' not in v:
                raise ValueError('Invalid email format')
            return v

    @app.post("/test")
    async def test_endpoint(data: TestModel):
        return {"ok": True}

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post("/test", json={"email": "invalid-email"})

    assert response.status_code == 422
    data = response.json()
    assert data["error_code"] == "VALIDATION_ERROR"
    assert data["type"] == "validation_error"
    assert "email" in data["message"].lower()


@pytest.mark.asyncio
async def test_request_validation_error_empty_errors():
    """Test RequestValidationError handler with empty errors list."""
    from fastapi.exceptions import RequestValidationError
    from unittest.mock import MagicMock

    app = FastAPI()
    register_exception_handlers(app)

    # Get the RequestValidationError handler
    handler = app.exception_handlers.get(RequestValidationError)
    assert handler is not None

    # Create mock request and exception with empty errors
    mock_request = MagicMock()
    mock_exc = MagicMock(spec=RequestValidationError)
    mock_exc.errors.return_value = []  # Empty errors list to hit line 48

    # Call handler directly
    response = await handler(mock_request, mock_exc)

    assert response.status_code == 422
    data = json.loads(response.body.decode())
    assert data["error_code"] == "VALIDATION_ERROR"
    assert data["type"] == "validation_error"
    assert data["message"] == "Validation error"  # Default message when errors is empty


@pytest.mark.asyncio
async def test_pydantic_validation_error_empty_errors():
    """Test PydanticValidationError handler with empty errors list."""
    from pydantic_core import ValidationError as PydanticValidationError
    from unittest.mock import MagicMock

    app = FastAPI()
    register_exception_handlers(app)

    # Get the PydanticValidationError handler
    handler = app.exception_handlers.get(PydanticValidationError)
    assert handler is not None

    # Create mock request and exception with empty errors
    mock_request = MagicMock()
    mock_exc = MagicMock(spec=PydanticValidationError)
    mock_exc.errors.return_value = []  # Empty errors list to hit line 80

    # Call handler directly
    response = await handler(mock_request, mock_exc)

    assert response.status_code == 422
    data = json.loads(response.body.decode())
    assert data["error_code"] == "VALIDATION_ERROR"
    assert data["type"] == "validation_error"
    assert data["message"] == "Validation error"  # Default message when errors is empty


@pytest.mark.asyncio
async def test_pydantic_validation_error_with_errors():
    """Test PydanticValidationError handler with actual errors."""
    from pydantic_core import ValidationError as PydanticValidationError
    from unittest.mock import MagicMock

    app = FastAPI()
    register_exception_handlers(app)

    # Get the PydanticValidationError handler
    handler = app.exception_handlers.get(PydanticValidationError)
    assert handler is not None

    # Create mock request and exception with errors to hit lines 76-78
    mock_request = MagicMock()
    mock_exc = MagicMock(spec=PydanticValidationError)
    mock_exc.errors.return_value = [
        {
            "loc": ("email",),
            "msg": "field required",
            "type": "value_error.missing"
        }
    ]

    # Call handler directly
    response = await handler(mock_request, mock_exc)

    assert response.status_code == 422
    data = json.loads(response.body.decode())
    assert data["error_code"] == "VALIDATION_ERROR"
    assert data["type"] == "validation_error"
    assert "email" in data["message"]
    assert "field required" in data["message"]


@pytest.mark.asyncio
async def test_generic_exception_handler():
    """Test generic exception handler returns 500 for unexpected exceptions."""
    from src.infrastructure.api.exception_handlers import register_exception_handlers
    from unittest.mock import MagicMock

    app = FastAPI()

    # Get the handler by registering and checking the exception_handlers dict
    register_exception_handlers(app)

    # Get the generic Exception handler
    handler = app.exception_handlers.get(Exception)
    assert handler is not None, "Generic exception handler should be registered"

    # Create a mock request and exception
    mock_request = MagicMock()
    test_exception = Exception("Unexpected database error")

    # Call the handler directly
    response = await handler(mock_request, test_exception)

    assert response.status_code == 500
    # Access the body content directly from the response
    data = json.loads(response.body.decode())

    assert data["error_code"] == "INTERNAL_SERVER_ERROR"
    assert data["type"] == "system_error"
    assert "unexpected error" in data["message"].lower()
