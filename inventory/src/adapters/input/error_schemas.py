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
                    "message": "country: Invalid country: XYZ",
                    "type": "validation_error"
                }
            ]
        }
