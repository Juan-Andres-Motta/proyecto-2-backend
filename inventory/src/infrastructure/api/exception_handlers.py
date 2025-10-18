"""Global exception handlers for FastAPI (like Spring @ControllerAdvice)."""
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from src.domain.exceptions import (
    BusinessRuleException,
    DomainException,
    NotFoundException,
    ValidationException,
)


def register_exception_handlers(app: FastAPI) -> None:
    """Register all domain exception handlers to the FastAPI app."""

    @app.exception_handler(NotFoundException)
    async def handle_not_found_exception(
        request: Request, exc: NotFoundException
    ) -> JSONResponse:
        """Handle NotFoundException (404)."""
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "error_code": exc.error_code,
                "message": exc.message,
                "type": "not_found",
            },
        )

    @app.exception_handler(ValidationException)
    async def handle_validation_exception(
        request: Request, exc: ValidationException
    ) -> JSONResponse:
        """Handle ValidationException (422)."""
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error_code": exc.error_code,
                "message": exc.message,
                "type": "validation_error",
            },
        )

    @app.exception_handler(BusinessRuleException)
    async def handle_business_rule_exception(
        request: Request, exc: BusinessRuleException
    ) -> JSONResponse:
        """Handle BusinessRuleException (400)."""
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error_code": exc.error_code,
                "message": exc.message,
                "type": "business_rule_violation",
            },
        )

    @app.exception_handler(DomainException)
    async def handle_domain_exception(
        request: Request, exc: DomainException
    ) -> JSONResponse:
        """Handle generic DomainException (500)."""
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error_code": exc.error_code,
                "message": exc.message,
                "type": "domain_error",
            },
        )
