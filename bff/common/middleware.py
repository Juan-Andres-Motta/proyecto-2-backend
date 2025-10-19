"""
Generic middleware for exception handling across all BFF modules.

This middleware can be used in web, client_app, sellers_app, and any other modules.
"""

import logging
from typing import Callable

from fastapi import Request, Response, status
from fastapi.exceptions import RequestValidationError
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
        except RequestValidationError as exc:
            # Handle FastAPI request validation errors
            return self._handle_request_validation_error(exc, request)
        except PydanticValidationError as exc:
            # Handle Pydantic validation errors
            return self._handle_pydantic_validation_error(exc, request)
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

    def _handle_request_validation_error(
        self, exc: RequestValidationError, request: Request
    ) -> JSONResponse:
        """Handle FastAPI/Pydantic validation errors (422)."""
        errors = exc.errors()
        if errors:
            first_error = errors[0]
            field = ".".join(str(loc) for loc in first_error["loc"][1:])  # Skip 'body'
            message = f"{field}: {first_error['msg']}" if field else first_error['msg']
        else:
            message = "Validation error"

        logger.warning(
            f"Request validation error: {message}",
            extra={
                "path": request.url.path,
                "method": request.method,
            },
        )

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error_code": "VALIDATION_ERROR",
                "message": message,
                "type": "validation_error"
            }
        )

    def _handle_pydantic_validation_error(
        self, exc: PydanticValidationError, request: Request
    ) -> JSONResponse:
        """Handle Pydantic validation errors (422)."""
        errors = exc.errors()
        if errors:
            first_error = errors[0]
            field = ".".join(str(loc) for loc in first_error["loc"])
            message = f"{field}: {first_error['msg']}"
        else:
            message = "Validation error"

        logger.warning(
            f"Pydantic validation error: {message}",
            extra={
                "path": request.url.path,
                "method": request.method,
            },
        )

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error_code": "VALIDATION_ERROR",
                "message": message,
                "type": "validation_error"
            }
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
                "error_code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred",
                "type": "system_error",
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
