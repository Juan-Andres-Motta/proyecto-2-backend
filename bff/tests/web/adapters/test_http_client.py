"""
Unit tests for HttpClient.

These tests focus on OUR logic:
- Error mapping from httpx exceptions to our custom exceptions
- Correct HTTP method calls
- Proper logging
"""

from unittest.mock import AsyncMock, Mock, patch

import httpx
import pytest

from common.exceptions import (
    MicroserviceConnectionError,
    MicroserviceHTTPError,
    MicroserviceTimeoutError,
    MicroserviceValidationError,
)
from web.adapters.http_client import HttpClient


@pytest.fixture
def http_client():
    """Create an HttpClient instance for testing."""
    return HttpClient(
        base_url="http://test-service:8000",
        timeout=10.0,
        service_name="test-service",
    )


class TestHttpClientErrorMapping:
    """Test HttpClient error mapping logic - THIS IS OUR LOGIC."""

    @pytest.mark.asyncio
    async def test_maps_timeout_to_microservice_timeout_error(self, http_client):
        """Test that httpx.TimeoutException is mapped to MicroserviceTimeoutError."""
        with patch("httpx.AsyncClient") as MockClient:
            mock_instance = AsyncMock()
            mock_instance.__aenter__.return_value.post = AsyncMock(
                side_effect=httpx.TimeoutException("Request timed out")
            )
            MockClient.return_value = mock_instance

            with pytest.raises(MicroserviceTimeoutError) as exc_info:
                await http_client.post("/endpoint", json={})

            assert exc_info.value.service_name == "test-service"
            assert exc_info.value.status_code == 504
            assert exc_info.value.details.get("timeout_seconds") == 10.0

    @pytest.mark.asyncio
    async def test_maps_connect_error_to_connection_error(self, http_client):
        """Test that httpx.ConnectError is mapped to MicroserviceConnectionError."""
        with patch("httpx.AsyncClient") as MockClient:
            mock_instance = AsyncMock()
            mock_instance.__aenter__.return_value.post = AsyncMock(
                side_effect=httpx.ConnectError("Connection refused")
            )
            MockClient.return_value = mock_instance

            with pytest.raises(MicroserviceConnectionError) as exc_info:
                await http_client.post("/endpoint", json={})

            assert exc_info.value.service_name == "test-service"
            assert exc_info.value.status_code == 503
            assert "Connection refused" in exc_info.value.details.get("original_error", "")

    @pytest.mark.asyncio
    async def test_maps_400_to_validation_error(self, http_client):
        """Test that 400 status is mapped to MicroserviceValidationError."""
        with patch("httpx.AsyncClient") as MockClient:
            mock_response = Mock()
            mock_response.status_code = 400
            mock_response.text = "Bad request"

            def raise_http_error():
                raise httpx.HTTPStatusError(
                    "Bad request", request=Mock(), response=mock_response
                )

            mock_response.raise_for_status = raise_http_error

            mock_instance = AsyncMock()
            mock_instance.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )
            MockClient.return_value = mock_instance

            with pytest.raises(MicroserviceValidationError) as exc_info:
                await http_client.post("/endpoint", json={})

            assert exc_info.value.service_name == "test-service"
            assert exc_info.value.status_code == 400
            assert "Bad request" in exc_info.value.message

    @pytest.mark.asyncio
    async def test_maps_422_to_validation_error(self, http_client):
        """Test that 422 status is mapped to MicroserviceValidationError."""
        with patch("httpx.AsyncClient") as MockClient:
            mock_response = Mock()
            mock_response.status_code = 422
            mock_response.text = "Validation failed"

            def raise_http_error():
                raise httpx.HTTPStatusError(
                    "Validation error", request=Mock(), response=mock_response
                )

            mock_response.raise_for_status = raise_http_error

            mock_instance = AsyncMock()
            mock_instance.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )
            MockClient.return_value = mock_instance

            with pytest.raises(MicroserviceValidationError) as exc_info:
                await http_client.post("/endpoint", json={})

            assert exc_info.value.service_name == "test-service"
            assert exc_info.value.status_code == 422

    @pytest.mark.asyncio
    async def test_maps_404_to_http_error(self, http_client):
        """Test that 404 status is mapped to MicroserviceHTTPError."""
        with patch("httpx.AsyncClient") as MockClient:
            mock_response = Mock()
            mock_response.status_code = 404
            mock_response.text = "Not found"

            def raise_http_error():
                raise httpx.HTTPStatusError(
                    "Not found", request=Mock(), response=mock_response
                )

            mock_response.raise_for_status = raise_http_error

            mock_instance = AsyncMock()
            mock_instance.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )
            MockClient.return_value = mock_instance

            with pytest.raises(MicroserviceHTTPError) as exc_info:
                await http_client.post("/endpoint", json={})

            assert exc_info.value.service_name == "test-service"
            assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_maps_500_to_http_error(self, http_client):
        """Test that 500 status is mapped to MicroserviceHTTPError."""
        with patch("httpx.AsyncClient") as MockClient:
            mock_response = Mock()
            mock_response.status_code = 500
            mock_response.text = "Internal server error"

            def raise_http_error():
                raise httpx.HTTPStatusError(
                    "Internal error", request=Mock(), response=mock_response
                )

            mock_response.raise_for_status = raise_http_error

            mock_instance = AsyncMock()
            mock_instance.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )
            MockClient.return_value = mock_instance

            with pytest.raises(MicroserviceHTTPError) as exc_info:
                await http_client.post("/endpoint", json={})

            assert exc_info.value.service_name == "test-service"
            assert exc_info.value.status_code == 500

    @pytest.mark.asyncio
    async def test_includes_response_text_in_error_details(self, http_client):
        """Test that response text is included in error details."""
        with patch("httpx.AsyncClient") as MockClient:
            mock_response = Mock()
            mock_response.status_code = 500
            mock_response.text = "Detailed error message from service"

            def raise_http_error():
                raise httpx.HTTPStatusError(
                    "Error", request=Mock(), response=mock_response
                )

            mock_response.raise_for_status = raise_http_error

            mock_instance = AsyncMock()
            mock_instance.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )
            MockClient.return_value = mock_instance

            with pytest.raises(MicroserviceHTTPError) as exc_info:
                await http_client.post("/endpoint", json={})

            assert "Detailed error message from service" in exc_info.value.details.get(
                "response_text", ""
            )

    @pytest.mark.asyncio
    async def test_error_includes_service_name(self, http_client):
        """Test that all mapped errors include the service name."""
        with patch("httpx.AsyncClient") as MockClient:
            mock_instance = AsyncMock()
            mock_instance.__aenter__.return_value.post = AsyncMock(
                side_effect=httpx.TimeoutException("Timeout")
            )
            MockClient.return_value = mock_instance

            with pytest.raises(MicroserviceTimeoutError) as exc_info:
                await http_client.post("/endpoint", json={})

            assert exc_info.value.service_name == "test-service"
            assert "test-service" in exc_info.value.message.lower()


class TestHttpClientSuccessCases:
    """Test HTTP client successful request cases."""

    @pytest.mark.asyncio
    async def test_successful_get_request(self, http_client):
        """Test successful GET request."""
        with patch("httpx.AsyncClient") as MockClient:
            mock_response = Mock()
            mock_response.json = Mock(return_value={"data": "test"})
            mock_response.raise_for_status = Mock()

            mock_instance = AsyncMock()
            mock_instance.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )
            MockClient.return_value = mock_instance

            result = await http_client.get("/endpoint", params={"key": "value"})

            assert result == {"data": "test"}

    @pytest.mark.asyncio
    async def test_successful_post_request(self, http_client):
        """Test successful POST request."""
        with patch("httpx.AsyncClient") as MockClient:
            mock_response = Mock()
            mock_response.json = Mock(return_value={"id": "123"})
            mock_response.raise_for_status = Mock()

            mock_instance = AsyncMock()
            mock_instance.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )
            MockClient.return_value = mock_instance

            result = await http_client.post("/endpoint", json={"data": "test"})

            assert result == {"id": "123"}

    @pytest.mark.asyncio
    async def test_successful_patch_request(self, http_client):
        """Test successful PATCH request."""
        with patch("httpx.AsyncClient") as MockClient:
            mock_response = Mock()
            mock_response.json = Mock(return_value={"id": "123", "status": "updated"})
            mock_response.raise_for_status = Mock()

            mock_instance = AsyncMock()
            mock_instance.__aenter__.return_value.patch = AsyncMock(
                return_value=mock_response
            )
            MockClient.return_value = mock_instance

            result = await http_client.patch("/endpoint/123", json={"status": "updated"})

            assert result == {"id": "123", "status": "updated"}


class TestHttpClientPatchErrorHandling:
    """Test PATCH method error handling."""

    @pytest.mark.asyncio
    async def test_patch_maps_timeout_to_microservice_timeout_error(self):
        """Test that httpx.TimeoutException is mapped to MicroserviceTimeoutError on PATCH."""
        http_client = HttpClient(
            base_url="http://test-service:8000",
            timeout=10.0,
            service_name="test-service",
        )
        with patch("httpx.AsyncClient") as MockClient:
            mock_instance = AsyncMock()
            mock_instance.__aenter__.return_value.patch = AsyncMock(
                side_effect=httpx.TimeoutException("Request timed out")
            )
            MockClient.return_value = mock_instance

            with pytest.raises(MicroserviceTimeoutError) as exc_info:
                await http_client.patch("/endpoint", json={})

            assert exc_info.value.service_name == "test-service"

    @pytest.mark.asyncio
    async def test_patch_maps_connect_error_to_connection_error(self):
        """Test that httpx.ConnectError is mapped to MicroserviceConnectionError on PATCH."""
        http_client = HttpClient(
            base_url="http://test-service:8000",
            timeout=10.0,
            service_name="test-service",
        )
        with patch("httpx.AsyncClient") as MockClient:
            mock_instance = AsyncMock()
            mock_instance.__aenter__.return_value.patch = AsyncMock(
                side_effect=httpx.ConnectError("Connection refused")
            )
            MockClient.return_value = mock_instance

            with pytest.raises(MicroserviceConnectionError) as exc_info:
                await http_client.patch("/endpoint", json={})

            assert exc_info.value.service_name == "test-service"

    @pytest.mark.asyncio
    async def test_patch_maps_400_to_validation_error(self):
        """Test that 400 status is mapped to MicroserviceValidationError on PATCH."""
        http_client = HttpClient(
            base_url="http://test-service:8000",
            timeout=10.0,
            service_name="test-service",
        )
        with patch("httpx.AsyncClient") as MockClient:
            mock_response = Mock()
            mock_response.status_code = 400
            mock_response.text = "Bad request"

            def raise_http_error():
                raise httpx.HTTPStatusError(
                    "Bad request", request=Mock(), response=mock_response
                )

            mock_response.raise_for_status = raise_http_error

            mock_instance = AsyncMock()
            mock_instance.__aenter__.return_value.patch = AsyncMock(
                return_value=mock_response
            )
            MockClient.return_value = mock_instance

            with pytest.raises(MicroserviceValidationError) as exc_info:
                await http_client.patch("/endpoint", json={})

            assert exc_info.value.service_name == "test-service"
            assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_patch_maps_422_to_validation_error(self):
        """Test that 422 status is mapped to MicroserviceValidationError on PATCH."""
        http_client = HttpClient(
            base_url="http://test-service:8000",
            timeout=10.0,
            service_name="test-service",
        )
        with patch("httpx.AsyncClient") as MockClient:
            mock_response = Mock()
            mock_response.status_code = 422
            mock_response.text = "Validation failed"

            def raise_http_error():
                raise httpx.HTTPStatusError(
                    "Validation error", request=Mock(), response=mock_response
                )

            mock_response.raise_for_status = raise_http_error

            mock_instance = AsyncMock()
            mock_instance.__aenter__.return_value.patch = AsyncMock(
                return_value=mock_response
            )
            MockClient.return_value = mock_instance

            with pytest.raises(MicroserviceValidationError) as exc_info:
                await http_client.patch("/endpoint", json={})

            assert exc_info.value.service_name == "test-service"
            assert exc_info.value.status_code == 422

    @pytest.mark.asyncio
    async def test_patch_maps_404_to_http_error(self):
        """Test that 404 status is mapped to MicroserviceHTTPError on PATCH."""
        http_client = HttpClient(
            base_url="http://test-service:8000",
            timeout=10.0,
            service_name="test-service",
        )
        with patch("httpx.AsyncClient") as MockClient:
            mock_response = Mock()
            mock_response.status_code = 404
            mock_response.text = "Not found"

            def raise_http_error():
                raise httpx.HTTPStatusError(
                    "Not found", request=Mock(), response=mock_response
                )

            mock_response.raise_for_status = raise_http_error

            mock_instance = AsyncMock()
            mock_instance.__aenter__.return_value.patch = AsyncMock(
                return_value=mock_response
            )
            MockClient.return_value = mock_instance

            with pytest.raises(MicroserviceHTTPError) as exc_info:
                await http_client.patch("/endpoint", json={})

            assert exc_info.value.service_name == "test-service"
            assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_patch_maps_409_to_http_error(self):
        """Test that 409 status is mapped to MicroserviceHTTPError on PATCH."""
        http_client = HttpClient(
            base_url="http://test-service:8000",
            timeout=10.0,
            service_name="test-service",
        )
        with patch("httpx.AsyncClient") as MockClient:
            mock_response = Mock()
            mock_response.status_code = 409
            mock_response.text = "Conflict"

            def raise_http_error():
                raise httpx.HTTPStatusError(
                    "Conflict", request=Mock(), response=mock_response
                )

            mock_response.raise_for_status = raise_http_error

            mock_instance = AsyncMock()
            mock_instance.__aenter__.return_value.patch = AsyncMock(
                return_value=mock_response
            )
            MockClient.return_value = mock_instance

            with pytest.raises(MicroserviceHTTPError) as exc_info:
                await http_client.patch("/endpoint", json={})

            assert exc_info.value.service_name == "test-service"
            assert exc_info.value.status_code == 409

    @pytest.mark.asyncio
    async def test_patch_maps_500_to_http_error(self):
        """Test that 500 status is mapped to MicroserviceHTTPError on PATCH."""
        http_client = HttpClient(
            base_url="http://test-service:8000",
            timeout=10.0,
            service_name="test-service",
        )
        with patch("httpx.AsyncClient") as MockClient:
            mock_response = Mock()
            mock_response.status_code = 500
            mock_response.text = "Internal server error"

            def raise_http_error():
                raise httpx.HTTPStatusError(
                    "Internal error", request=Mock(), response=mock_response
                )

            mock_response.raise_for_status = raise_http_error

            mock_instance = AsyncMock()
            mock_instance.__aenter__.return_value.patch = AsyncMock(
                return_value=mock_response
            )
            MockClient.return_value = mock_instance

            with pytest.raises(MicroserviceHTTPError) as exc_info:
                await http_client.patch("/endpoint", json={})

            assert exc_info.value.service_name == "test-service"
            assert exc_info.value.status_code == 500
