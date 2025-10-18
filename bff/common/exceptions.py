"""
Custom exception classes for the BFF microservice.

These exceptions provide a type-safe way to handle errors across the application
and allow for centralized error handling in middleware.
"""

from typing import Any, Dict, Optional


class BFFException(Exception):
    """Base exception for all BFF-specific errors."""

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(BFFException):
    """Raised when request validation fails."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=400, details=details)


class ResourceNotFoundError(BFFException):
    """Raised when a requested resource is not found."""

    def __init__(self, resource_type: str, resource_id: Optional[str] = None):
        message = f"{resource_type} not found"
        if resource_id:
            message = f"{resource_type} with id '{resource_id}' not found"
        super().__init__(message, status_code=404)


class MicroserviceError(BFFException):
    """Base exception for errors related to downstream microservices."""

    def __init__(
        self,
        service_name: str,
        message: str,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.service_name = service_name
        super().__init__(message, status_code=status_code, details=details)


class MicroserviceConnectionError(MicroserviceError):
    """Raised when unable to connect to a downstream microservice."""

    def __init__(self, service_name: str, original_error: Optional[str] = None):
        message = f"Unable to connect to {service_name} service"
        details = {"original_error": original_error} if original_error else {}
        super().__init__(service_name, message, status_code=503, details=details)


class MicroserviceTimeoutError(MicroserviceError):
    """Raised when a request to a downstream microservice times out."""

    def __init__(self, service_name: str, timeout_seconds: Optional[float] = None):
        message = f"Request to {service_name} service timed out"
        details = {"timeout_seconds": timeout_seconds} if timeout_seconds else {}
        super().__init__(service_name, message, status_code=504, details=details)


class MicroserviceValidationError(MicroserviceError):
    """Raised when a downstream microservice returns a validation error."""

    def __init__(
        self,
        service_name: str,
        message: str,
        status_code: int = 400,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(service_name, message, status_code=status_code, details=details)


class MicroserviceHTTPError(MicroserviceError):
    """Raised when a downstream microservice returns an HTTP error."""

    def __init__(
        self,
        service_name: str,
        status_code: int,
        response_text: Optional[str] = None,
    ):
        message = f"{service_name} service returned error: {status_code}"
        details = {"response_text": response_text} if response_text else {}
        super().__init__(service_name, message, status_code=status_code, details=details)


class BusinessRuleViolationError(BFFException):
    """Raised when a business rule is violated."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=422, details=details)


class UnauthorizedError(BFFException):
    """Raised when authentication is required but not provided or invalid."""

    def __init__(self, message: str = "Unauthorized"):
        super().__init__(message, status_code=401)


class ForbiddenError(BFFException):
    """Raised when the user doesn't have permission to access a resource."""

    def __init__(self, message: str = "Forbidden"):
        super().__init__(message, status_code=403)
