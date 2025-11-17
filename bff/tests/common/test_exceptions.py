"""
Unit tests for custom exception classes.

Tests exception creation, message formatting, and initialization.
"""

import pytest
from common.exceptions import (
    BFFException,
    ValidationError,
    ResourceNotFoundError,
    MicroserviceError,
    MicroserviceConnectionError,
    MicroserviceTimeoutError,
    MicroserviceValidationError,
    MicroserviceHTTPError,
    BusinessRuleViolationError,
    UnauthorizedError,
    ForbiddenError,
)


class TestBFFException:
    """Tests for the base BFFException class."""

    def test_bff_exception_with_defaults(self):
        """Test BFFException creation with default status code."""
        exc = BFFException("Test error message")
        assert exc.message == "Test error message"
        assert exc.status_code == 500
        assert exc.details == {}
        assert str(exc) == "Test error message"

    def test_bff_exception_with_custom_status_code(self):
        """Test BFFException creation with custom status code."""
        exc = BFFException("Test error", status_code=400)
        assert exc.message == "Test error"
        assert exc.status_code == 400

    def test_bff_exception_with_details(self):
        """Test BFFException creation with details dictionary."""
        details = {"field": "email", "error": "invalid format"}
        exc = BFFException("Validation failed", details=details)
        assert exc.details == details


class TestValidationError:
    """Tests for ValidationError exception."""

    def test_validation_error_defaults(self):
        """Test ValidationError with default parameters."""
        exc = ValidationError("Invalid input")
        assert exc.message == "Invalid input"
        assert exc.status_code == 400
        assert exc.details == {}

    def test_validation_error_with_details(self):
        """Test ValidationError with details."""
        details = {"fields": ["email", "password"]}
        exc = ValidationError("Multiple validation errors", details=details)
        assert exc.details == details
        assert exc.status_code == 400


class TestResourceNotFoundError:
    """Tests for ResourceNotFoundError exception."""

    def test_resource_not_found_without_id(self):
        """Test ResourceNotFoundError without resource ID."""
        exc = ResourceNotFoundError("User")
        assert exc.message == "User not found"
        assert exc.status_code == 404

    def test_resource_not_found_with_id(self):
        """Test ResourceNotFoundError with resource ID."""
        exc = ResourceNotFoundError("User", "123-456-789")
        assert exc.message == "User with id '123-456-789' not found"
        assert exc.status_code == 404

    def test_resource_not_found_with_none_id(self):
        """Test ResourceNotFoundError with None ID parameter."""
        exc = ResourceNotFoundError("Product", None)
        assert exc.message == "Product not found"
        assert exc.status_code == 404


class TestMicroserviceError:
    """Tests for MicroserviceError exception."""

    def test_microservice_error_basic(self):
        """Test MicroserviceError creation."""
        exc = MicroserviceError("inventory", "Service unavailable")
        assert exc.service_name == "inventory"
        assert exc.message == "Service unavailable"
        assert exc.status_code == 500

    def test_microservice_error_with_custom_status_code(self):
        """Test MicroserviceError with custom status code."""
        exc = MicroserviceError(
            "catalog",
            "Not found",
            status_code=404
        )
        assert exc.status_code == 404
        assert exc.service_name == "catalog"

    def test_microservice_error_with_details(self):
        """Test MicroserviceError with details."""
        details = {"error_type": "timeout"}
        exc = MicroserviceError(
            "order",
            "Request failed",
            details=details
        )
        assert exc.details == details


class TestMicroserviceConnectionError:
    """Tests for MicroserviceConnectionError exception."""

    def test_connection_error_without_original_error(self):
        """Test MicroserviceConnectionError without original error."""
        exc = MicroserviceConnectionError("inventory")
        assert exc.service_name == "inventory"
        assert exc.message == "Unable to connect to inventory service"
        assert exc.status_code == 503
        assert exc.details == {}

    def test_connection_error_with_original_error(self):
        """Test MicroserviceConnectionError with original error message."""
        exc = MicroserviceConnectionError(
            "catalog",
            original_error="Connection refused"
        )
        assert exc.service_name == "catalog"
        assert exc.status_code == 503
        assert exc.details == {"original_error": "Connection refused"}

    def test_connection_error_with_none_original_error(self):
        """Test MicroserviceConnectionError with None original error."""
        exc = MicroserviceConnectionError("order", None)
        assert exc.details == {}


class TestMicroserviceTimeoutError:
    """Tests for MicroserviceTimeoutError exception."""

    def test_timeout_error_without_timeout_seconds(self):
        """Test MicroserviceTimeoutError without timeout_seconds."""
        exc = MicroserviceTimeoutError("inventory")
        assert exc.service_name == "inventory"
        assert exc.message == "Request to inventory service timed out"
        assert exc.status_code == 504
        assert exc.details == {}

    def test_timeout_error_with_timeout_seconds(self):
        """Test MicroserviceTimeoutError with timeout_seconds."""
        exc = MicroserviceTimeoutError("seller", timeout_seconds=10.5)
        assert exc.service_name == "seller"
        assert exc.status_code == 504
        assert exc.details == {"timeout_seconds": 10.5}

    def test_timeout_error_with_none_timeout_seconds(self):
        """Test MicroserviceTimeoutError with None timeout_seconds."""
        exc = MicroserviceTimeoutError("client", None)
        assert exc.details == {}


class TestMicroserviceValidationError:
    """Tests for MicroserviceValidationError exception."""

    def test_validation_error_basic(self):
        """Test MicroserviceValidationError creation."""
        exc = MicroserviceValidationError(
            "order",
            "Invalid product ID"
        )
        assert exc.service_name == "order"
        assert exc.message == "Invalid product ID"
        assert exc.status_code == 400

    def test_validation_error_with_custom_status_code(self):
        """Test MicroserviceValidationError with custom status code."""
        exc = MicroserviceValidationError(
            "catalog",
            "Invalid request",
            status_code=422
        )
        assert exc.status_code == 422

    def test_validation_error_with_details(self):
        """Test MicroserviceValidationError with details."""
        details = {"field": "quantity", "error": "must be positive"}
        exc = MicroserviceValidationError(
            "inventory",
            "Validation failed",
            details=details
        )
        assert exc.details == details


class TestMicroserviceHTTPError:
    """Tests for MicroserviceHTTPError exception."""

    def test_http_error_without_response_text(self):
        """Test MicroserviceHTTPError without response text."""
        exc = MicroserviceHTTPError("inventory", 500)
        assert exc.service_name == "inventory"
        assert exc.message == "inventory service returned error: 500"
        assert exc.status_code == 500
        assert exc.details == {}

    def test_http_error_with_response_text(self):
        """Test MicroserviceHTTPError with response text."""
        exc = MicroserviceHTTPError(
            "catalog",
            404,
            response_text="Resource not found"
        )
        assert exc.service_name == "catalog"
        assert exc.status_code == 404
        assert exc.details == {"response_text": "Resource not found"}

    def test_http_error_with_none_response_text(self):
        """Test MicroserviceHTTPError with None response text."""
        exc = MicroserviceHTTPError("order", 503, None)
        assert exc.details == {}


class TestBusinessRuleViolationError:
    """Tests for BusinessRuleViolationError exception."""

    def test_business_rule_violation_basic(self):
        """Test BusinessRuleViolationError creation."""
        exc = BusinessRuleViolationError("Cannot cancel completed order")
        assert exc.message == "Cannot cancel completed order"
        assert exc.status_code == 422
        assert exc.details == {}

    def test_business_rule_violation_with_details(self):
        """Test BusinessRuleViolationError with details."""
        details = {"order_id": "123", "status": "completed"}
        exc = BusinessRuleViolationError(
            "Invalid operation",
            details=details
        )
        assert exc.details == details
        assert exc.status_code == 422


class TestUnauthorizedError:
    """Tests for UnauthorizedError exception."""

    def test_unauthorized_error_default_message(self):
        """Test UnauthorizedError with default message."""
        exc = UnauthorizedError()
        assert exc.message == "Unauthorized"
        assert exc.status_code == 401
        assert exc.details == {}

    def test_unauthorized_error_custom_message(self):
        """Test UnauthorizedError with custom message."""
        exc = UnauthorizedError("Invalid token")
        assert exc.message == "Invalid token"
        assert exc.status_code == 401


class TestForbiddenError:
    """Tests for ForbiddenError exception."""

    def test_forbidden_error_default_message(self):
        """Test ForbiddenError with default message."""
        exc = ForbiddenError()
        assert exc.message == "Forbidden"
        assert exc.status_code == 403
        assert exc.details == {}

    def test_forbidden_error_custom_message(self):
        """Test ForbiddenError with custom message."""
        exc = ForbiddenError("You do not have permission to access this resource")
        assert exc.message == "You do not have permission to access this resource"
        assert exc.status_code == 403
