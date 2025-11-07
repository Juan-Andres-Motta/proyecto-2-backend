"""
HTTP client abstraction for communicating with microservices.

This module provides a unified HTTP client that handles error mapping,
timeouts, and connection management.
"""

import logging
from typing import Any, Dict, Optional

import httpx

from common.exceptions import (
    MicroserviceConnectionError,
    MicroserviceHTTPError,
    MicroserviceTimeoutError,
    MicroserviceValidationError,
)

logger = logging.getLogger(__name__)


class HttpClient:
    """
    Abstraction layer for HTTP communication with microservices.

    This client handles:
    - Connection management
    - Error mapping to domain exceptions
    - Timeout configuration
    - Request/response logging
    """

    def __init__(self, base_url: str, timeout: float = 10.0, service_name: str = "unknown"):
        """
        Initialize the HTTP client.

        Args:
            base_url: Base URL for the microservice
            timeout: Request timeout in seconds
            service_name: Name of the service (for logging and error messages)
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.service_name = service_name

    async def post(
        self,
        path: str,
        json: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Send a POST request to the microservice.

        Args:
            path: API endpoint path (relative to base_url)
            json: JSON payload to send
            **kwargs: Additional arguments to pass to httpx

        Returns:
            JSON response from the service

        Raises:
            MicroserviceConnectionError: If unable to connect
            MicroserviceTimeoutError: If request times out
            MicroserviceValidationError: If validation fails (400-level errors)
            MicroserviceHTTPError: For other HTTP errors
        """
        url = f"{self.base_url}/{path.lstrip('/')}"

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                logger.debug(f"POST {url}", extra={"service": self.service_name})

                response = await client.post(url, json=json, **kwargs)

                # Log the response
                logger.debug(
                    f"Response {response.status_code} from {self.service_name}",
                    extra={"status_code": response.status_code, "url": url},
                )

                # Raise for HTTP errors
                response.raise_for_status()

                return response.json()

        except httpx.TimeoutException as e:
            logger.error(
                f"Timeout connecting to {self.service_name}",
                extra={"url": url, "timeout": self.timeout},
            )
            raise MicroserviceTimeoutError(self.service_name, self.timeout) from e

        except httpx.ConnectError as e:
            logger.error(
                f"Connection error to {self.service_name}",
                extra={"url": url, "error": str(e)},
            )
            raise MicroserviceConnectionError(self.service_name, str(e)) from e

        except httpx.HTTPStatusError as e:
            # Map HTTP status codes to appropriate exceptions
            status_code = e.response.status_code
            response_text = e.response.text

            logger.warning(
                f"HTTP {status_code} from {self.service_name}",
                extra={
                    "status_code": status_code,
                    "url": url,
                    "response": response_text,
                },
            )

            # Validation errors (400-level)
            if 400 <= status_code < 500:
                if status_code == 422:
                    raise MicroserviceValidationError(
                        self.service_name,
                        "Validation error",
                        status_code=422,
                        details={"response": response_text},
                    ) from e
                elif status_code == 400:
                    raise MicroserviceValidationError(
                        self.service_name,
                        "Bad request",
                        details={"response": response_text},
                    ) from e
                elif status_code == 404:
                    raise MicroserviceHTTPError(
                        self.service_name, status_code, response_text
                    ) from e
                else:
                    raise MicroserviceHTTPError(
                        self.service_name, status_code, response_text
                    ) from e

            # Server errors (500-level)
            raise MicroserviceHTTPError(
                self.service_name, status_code, response_text
            ) from e

    async def get(
        self,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Send a GET request to the microservice.

        Args:
            path: API endpoint path (relative to base_url)
            params: Query parameters
            **kwargs: Additional arguments to pass to httpx

        Returns:
            JSON response from the service

        Raises:
            MicroserviceConnectionError: If unable to connect
            MicroserviceTimeoutError: If request times out
            MicroserviceHTTPError: For HTTP errors
        """
        url = f"{self.base_url}/{path.lstrip('/')}"

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                logger.debug(
                    f"GET {url}",
                    extra={"service": self.service_name, "params": params},
                )

                response = await client.get(url, params=params, **kwargs)

                logger.debug(
                    f"Response {response.status_code} from {self.service_name}",
                    extra={"status_code": response.status_code, "url": url},
                )

                response.raise_for_status()

                return response.json()

        except httpx.TimeoutException as e:
            logger.error(
                f"Timeout connecting to {self.service_name}",
                extra={"url": url, "timeout": self.timeout},
            )
            raise MicroserviceTimeoutError(self.service_name, self.timeout) from e

        except httpx.ConnectError as e:
            logger.error(
                f"Connection error to {self.service_name}",
                extra={"url": url, "error": str(e)},
            )
            raise MicroserviceConnectionError(self.service_name, str(e)) from e

        except httpx.HTTPStatusError as e:
            status_code = e.response.status_code
            response_text = e.response.text

            logger.warning(
                f"HTTP {status_code} from {self.service_name}",
                extra={
                    "status_code": status_code,
                    "url": url,
                    "response": response_text,
                },
            )

            raise MicroserviceHTTPError(
                self.service_name, status_code, response_text
            ) from e

    async def patch(
        self,
        path: str,
        json: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Send a PATCH request to the microservice.

        Args:
            path: API endpoint path (relative to base_url)
            json: JSON payload to send
            **kwargs: Additional arguments to pass to httpx

        Returns:
            JSON response from the service

        Raises:
            MicroserviceConnectionError: If unable to connect
            MicroserviceTimeoutError: If request times out
            MicroserviceValidationError: If validation fails (400-level errors)
            MicroserviceHTTPError: For other HTTP errors
        """
        url = f"{self.base_url}/{path.lstrip('/')}"

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                logger.debug(f"PATCH {url}", extra={"service": self.service_name})

                response = await client.patch(url, json=json, **kwargs)

                # Log the response
                logger.debug(
                    f"Response {response.status_code} from {self.service_name}",
                    extra={"status_code": response.status_code, "url": url},
                )

                # Raise for HTTP errors
                response.raise_for_status()

                return response.json()

        except httpx.TimeoutException as e:
            logger.error(
                f"Timeout connecting to {self.service_name}",
                extra={"url": url, "timeout": self.timeout},
            )
            raise MicroserviceTimeoutError(self.service_name, self.timeout) from e

        except httpx.ConnectError as e:
            logger.error(
                f"Connection error to {self.service_name}",
                extra={"url": url, "error": str(e)},
            )
            raise MicroserviceConnectionError(self.service_name, str(e)) from e

        except httpx.HTTPStatusError as e:
            # Map HTTP status codes to appropriate exceptions
            status_code = e.response.status_code
            response_text = e.response.text

            logger.warning(
                f"HTTP {status_code} from {self.service_name}",
                extra={
                    "status_code": status_code,
                    "url": url,
                    "response": response_text,
                },
            )

            # Validation errors (400-level)
            if 400 <= status_code < 500:
                if status_code == 422:
                    raise MicroserviceValidationError(
                        self.service_name,
                        "Validation error",
                        status_code=422,
                        details={"response": response_text},
                    ) from e
                elif status_code == 400:
                    raise MicroserviceValidationError(
                        self.service_name,
                        "Bad request",
                        details={"response": response_text},
                    ) from e
                elif status_code == 404:
                    raise MicroserviceHTTPError(
                        self.service_name, status_code, response_text
                    ) from e
                elif status_code == 409:
                    raise MicroserviceHTTPError(
                        self.service_name, status_code, response_text
                    ) from e
                else:
                    raise MicroserviceHTTPError(
                        self.service_name, status_code, response_text
                    ) from e

            # Server errors (500-level)
            raise MicroserviceHTTPError(
                self.service_name, status_code, response_text
            ) from e
