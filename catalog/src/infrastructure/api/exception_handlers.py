"""Global exception handlers for domain exceptions.

Similar to Spring Boot's @ControllerAdvice and @ExceptionHandler.
"""
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from src.domain.exceptions import (
    BusinessRuleException,
    DomainException,
    NotFoundException,
    ValidationException,
)


def register_exception_handlers(app: FastAPI) -> None:
    """Register all domain exception handlers to the FastAPI app.

    This is the equivalent of Spring Boot's @ControllerAdvice.

    Args:
        app: FastAPI application instance
    """

    @app.exception_handler(NotFoundException)
    async def handle_not_found_exception(
        request: Request,
        exc: NotFoundException
    ) -> JSONResponse:
        """Handle entity not found exceptions (404).

        Args:
            request: HTTP request
            exc: NotFoundException instance

        Returns:
            JSON response with 404 status
        """
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
        """Handle validation exceptions (422).

        Args:
            request: HTTP request
            exc: ValidationException instance

        Returns:
            JSON response with 422 status
        """
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
        """Handle business rule violations (400).

        Args:
            request: HTTP request
            exc: BusinessRuleException instance

        Returns:
            JSON response with 400 status
        """
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
        """Handle generic domain exceptions (500).

        Catch-all for domain exceptions not caught by more specific handlers.

        Args:
            request: HTTP request
            exc: DomainException instance

        Returns:
            JSON response with 500 status
        """
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
        """Handle unexpected exceptions (500).

        Catch-all for any exception not handled by domain exception handlers.

        Args:
            request: HTTP request
            exc: Exception instance

        Returns:
            JSON response with 500 status
        """
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error_code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred",
                "type": "system_error"
            }
        )
