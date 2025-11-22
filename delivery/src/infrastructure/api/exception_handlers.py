"""Global exception handlers for FastAPI (like Spring @ControllerAdvice)."""
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError as PydanticValidationError


def register_exception_handlers(app: FastAPI) -> None:
    """Register all domain exception handlers to the FastAPI app."""

    @app.exception_handler(RequestValidationError)
    async def handle_request_validation_error(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        """Handle FastAPI/Pydantic validation errors (422)."""
        # Extract first error message for simplicity
        errors = exc.errors()
        if errors:
            first_error = errors[0]
            field = ".".join(
                str(loc) for loc in first_error["loc"][1:]
            )  # Skip 'body'
            message = f"{field}: {first_error['msg']}"
        else:
            message = "Validation error"

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error_code": "VALIDATION_ERROR",
                "message": message,
                "type": "validation_error",
            },
        )

    @app.exception_handler(PydanticValidationError)
    async def handle_pydantic_validation_error(
        request: Request, exc: PydanticValidationError
    ) -> JSONResponse:
        """Handle Pydantic validation errors (422)."""
        # Extract first error message for simplicity
        errors = exc.errors()
        if errors:
            first_error = errors[0]
            field = ".".join(str(loc) for loc in first_error["loc"])
            message = f"{field}: {first_error['msg']}"
        else:
            message = "Validation error"

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error_code": "VALIDATION_ERROR",
                "message": message,
                "type": "validation_error",
            },
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_exception(
        request: Request, exc: Exception
    ) -> JSONResponse:
        """Handle unexpected exceptions (500)."""
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error_code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred",
                "type": "system_error",
            },
        )
