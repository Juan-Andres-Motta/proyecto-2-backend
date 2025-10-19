"""Error response schemas for OpenAPI documentation."""
from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    """Standard error response format for all errors."""
    error_code: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable error message")
    type: str = Field(..., description="Error type category")

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "error_code": "VALIDATION_ERROR",
                    "message": "total_quantity: Input should be greater than or equal to 0",
                    "type": "validation_error"
                }
            ]
        }


class ValidationErrorResponse(ErrorResponse):
    """Validation error response (422)."""
    error_code: str = "VALIDATION_ERROR"
    type: str = "validation_error"

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "error_code": "VALIDATION_ERROR",
                    "message": "limit: Input should be less than or equal to 100",
                    "type": "validation_error"
                }
            ]
        }


class NotFoundErrorResponse(ErrorResponse):
    """Not found error response (404)."""
    type: str = "not_found"

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "error_code": "PRODUCT_NOT_FOUND",
                    "message": "Product with ID '550e8400-e29b-41d4-a716-446655440000' not found",
                    "type": "not_found"
                }
            ]
        }


class ServiceUnavailableErrorResponse(ErrorResponse):
    """Service unavailable error response (503)."""
    type: str = "service_unavailable"

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "error_code": "SERVICE_UNAVAILABLE",
                    "message": "Catalog service is unavailable",
                    "type": "service_unavailable"
                }
            ]
        }


class GatewayTimeoutErrorResponse(ErrorResponse):
    """Gateway timeout error response (504)."""
    type: str = "gateway_timeout"

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "error_code": "GATEWAY_TIMEOUT",
                    "message": "Request to Inventory service timed out",
                    "type": "gateway_timeout"
                }
            ]
        }
