"""
Generic middleware for exception handling across all BFF modules.

This middleware can be used in web, client_app, sellers_app, and any other modules.
"""

import logging
from typing import Callable

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError as PydanticValidationError
from starlette.middleware.base import BaseHTTPMiddleware

from .exceptions import BFFException, MicroserviceError

logger = logging.getLogger(__name__)


class ExceptionHandlerMiddleware(BaseHTTPMiddleware):
    """
    Generic exception handling middleware that converts exceptions into
    standardized JSON error responses.

    This middleware can be registered in any FastAPI app to provide
    consistent error handling across all endpoints.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            response = await call_next(request)
            return response
        except BFFException as exc:
            # Handle our custom exceptions
            return self._handle_bff_exception(exc, request)
        except PydanticValidationError as exc:
            # Handle Pydantic validation errors
            return self._handle_validation_error(exc, request)
        except Exception as exc:
            # Handle unexpected exceptions
            return self._handle_unexpected_exception(exc, request)

    def _handle_bff_exception(self, exc: BFFException, request: Request) -> JSONResponse:
        """Handle custom BFF exceptions."""
        logger.warning(
            f"BFF exception: {exc.message}",
            extra={
                "path": request.url.path,
                "method": request.method,
                "status_code": exc.status_code,
                "details": exc.details,
            },
        )

        response_body = {
            "error": {
                "message": exc.message,
                "status_code": exc.status_code,
            }
        }

        # Add service_name for microservice errors
        if isinstance(exc, MicroserviceError):
            response_body["error"]["service"] = exc.service_name

        # Add details if available
        if exc.details:
            response_body["error"]["details"] = exc.details

        return JSONResponse(
            status_code=exc.status_code,
            content=response_body,
        )

    def _handle_validation_error(
        self, exc: PydanticValidationError, request: Request
    ) -> JSONResponse:
        """Handle Pydantic validation errors."""
        logger.warning(
            f"Validation error: {exc}",
            extra={
                "path": request.url.path,
                "method": request.method,
            },
        )

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": {
                    "message": "Validation error",
                    "status_code": 422,
                    "details": exc.errors(),
                }
            },
        )

    def _handle_unexpected_exception(
        self, exc: Exception, request: Request
    ) -> JSONResponse:
        """Handle unexpected exceptions."""
        logger.error(
            f"Unexpected exception: {str(exc)}",
            exc_info=True,
            extra={
                "path": request.url.path,
                "method": request.method,
            },
        )

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "message": "An unexpected error occurred",
                    "status_code": 500,
                }
            },
        )


def setup_exception_handlers(app):
    """
    Convenience function to set up exception handlers for a FastAPI app.

    Usage:
        from common.middleware import setup_exception_handlers

        app = FastAPI()
        setup_exception_handlers(app)
    """
    app.add_middleware(ExceptionHandlerMiddleware)
    logger.info("Exception handler middleware registered")
