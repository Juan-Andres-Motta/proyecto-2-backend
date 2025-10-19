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
                    "message": "category: Input should be 'medicamentos_especiales', 'insumos_quirurgicos', 'reactivos_diagnosticos', 'equipos_biomedicos' or 'otros'",
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
                    "message": "price: Input should be greater than 0",
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


class BusinessRuleErrorResponse(ErrorResponse):
    """Business rule violation error response (400)."""
    type: str = "business_rule_violation"

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "error_code": "DUPLICATE_SKU",
                    "message": "Product with SKU 'PROD-001' already exists",
                    "type": "business_rule_violation"
                }
            ]
        }
