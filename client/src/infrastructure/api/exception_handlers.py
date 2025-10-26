"""Global exception handlers for domain exceptions."""
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError as PydanticValidationError

from src.domain.exceptions import (
    BusinessRuleException,
    DomainException,
    NotFoundException,
    ValidationException,
)


def register_exception_handlers(app: FastAPI) -> None:
    """Register all domain exception handlers to the FastAPI app."""

    @app.exception_handler(RequestValidationError)
    async def handle_request_validation_error(
        request: Request,
        exc: RequestValidationError
    ) -> JSONResponse:
        """Handle FastAPI/Pydantic validation errors (422)."""
        errors = exc.errors()
        if errors:
            first_error = errors[0]
            field = ".".join(str(loc) for loc in first_error["loc"][1:])
            message = f"{field}: {first_error['msg']}" if field else first_error['msg']
        else:
            message = "Validation error"

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error_code": "VALIDATION_ERROR",
                "message": message,
                "type": "validation_error"
            }
        )

    @app.exception_handler(PydanticValidationError)
    async def handle_pydantic_validation_error(
        request: Request,
        exc: PydanticValidationError
    ) -> JSONResponse:
        """Handle Pydantic validation errors (422)."""
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
                "type": "validation_error"
            }
        )

    @app.exception_handler(NotFoundException)
    async def handle_not_found_exception(
        request: Request,
        exc: NotFoundException
    ) -> JSONResponse:
        """Handle entity not found exceptions (404)."""
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "error_code": exc.error_code,
                "message": exc.message,
                "type": "not_found"
            }
        )

    @app.exception_handler(ValidationException)
    async def handle_validation_exception(
        request: Request,
        exc: ValidationException
    ) -> JSONResponse:
        """Handle validation exceptions (422)."""
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error_code": exc.error_code,
                "message": exc.message,
                "type": "validation_error"
            }
        )

    @app.exception_handler(BusinessRuleException)
    async def handle_business_rule_exception(
        request: Request,
        exc: BusinessRuleException
    ) -> JSONResponse:
        """Handle business rule violations (400)."""
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error_code": exc.error_code,
                "message": exc.message,
                "type": "business_rule_violation"
            }
        )

    @app.exception_handler(DomainException)
    async def handle_domain_exception(
        request: Request,
        exc: DomainException
    ) -> JSONResponse:
        """Handle generic domain exceptions (500)."""
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error_code": exc.error_code,
                "message": exc.message,
                "type": "domain_error"
            }
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_exception(
        request: Request,
        exc: Exception
    ) -> JSONResponse:
        """Handle unexpected exceptions (500)."""
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error_code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred",
                "type": "system_error"
            }
        )
