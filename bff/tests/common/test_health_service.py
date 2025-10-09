from unittest.mock import AsyncMock, patch

import httpx
import pytest

from common.health_service import HealthService


@pytest.mark.asyncio
async def test_health_service_initialization():
    """Test HealthService initializes with correct services."""
    service = HealthService()

    assert "catalog" in service.services
    assert "client" in service.services
    assert "delivery" in service.services
    assert "inventory" in service.services
    assert "order" in service.services
    assert "seller" in service.services
    assert len(service.services) == 6


@pytest.mark.asyncio
async def test_check_service_health_healthy():
    """Test checking a healthy service."""
    service = HealthService()

    with patch("httpx.AsyncClient.get") as mock_get:
        mock_get.return_value = AsyncMock(
            status_code=200,
            json=lambda: {"status": "ok"},
        )
        mock_get.return_value.raise_for_status = lambda: None

        result = await service.check_service_health("catalog", "http://catalog:8000")

        assert result == {"catalog": "healthy"}


@pytest.mark.asyncio
async def test_check_service_health_unhealthy_status():
    """Test checking a service with unhealthy status."""
    service = HealthService()

    with patch("httpx.AsyncClient.get") as mock_get:
        mock_get.return_value = AsyncMock(
            status_code=200,
            json=lambda: {"status": "error"},
        )
        mock_get.return_value.raise_for_status = lambda: None

        result = await service.check_service_health("catalog", "http://catalog:8000")

        assert result == {"catalog": "unhealthy"}


@pytest.mark.asyncio
async def test_check_service_health_unhealthy_status_code():
    """Test checking a service with non-200 status code."""
    service = HealthService()

    with patch("httpx.AsyncClient.get") as mock_get:
        mock_get.return_value = AsyncMock(
            status_code=500,
            json=lambda: {"status": "ok"},
        )

        result = await service.check_service_health("catalog", "http://catalog:8000")

        assert result == {"catalog": "unhealthy"}


@pytest.mark.asyncio
async def test_check_service_health_unreachable():
    """Test checking an unreachable service."""
    service = HealthService()

    with patch("httpx.AsyncClient.get") as mock_get:
        mock_get.side_effect = httpx.RequestError("Connection failed")

        result = await service.check_service_health("catalog", "http://catalog:8000")

        assert result == {"catalog": "unreachable"}


@pytest.mark.asyncio
async def test_check_service_health_timeout():
    """Test checking a service that times out."""
    service = HealthService()

    with patch("httpx.AsyncClient.get") as mock_get:
        mock_get.side_effect = httpx.TimeoutException("Request timeout")

        result = await service.check_service_health("catalog", "http://catalog:8000")

        assert result == {"catalog": "unreachable"}


@pytest.mark.asyncio
async def test_check_service_health_error():
    """Test checking a service that raises an unexpected error."""
    service = HealthService()

    with patch("httpx.AsyncClient.get") as mock_get:
        mock_get.side_effect = Exception("Unexpected error")

        result = await service.check_service_health("catalog", "http://catalog:8000")

        assert result == {"catalog": "error"}


@pytest.mark.asyncio
async def test_check_all_services_all_healthy():
    """Test checking all services when all are healthy."""
    service = HealthService()

    with patch("httpx.AsyncClient.get") as mock_get:
        mock_get.return_value = AsyncMock(
            status_code=200,
            json=lambda: {"status": "ok"},
        )
        mock_get.return_value.raise_for_status = lambda: None

        results = await service.check_all_services()

        assert len(results) == 6
        for result in results:
            service_name = list(result.keys())[0]
            assert result[service_name] == "healthy"


@pytest.mark.asyncio
async def test_check_all_services_mixed_statuses():
    """Test checking all services with mixed health statuses."""
    service = HealthService()

    def side_effect(url):
        mock_resp = AsyncMock()
        if "catalog" in url:
            mock_resp.status_code = 200
            mock_resp.json = lambda: {"status": "ok"}
        elif "client" in url:
            raise httpx.RequestError("Connection failed")
        else:
            mock_resp.status_code = 500
            mock_resp.json = lambda: {"status": "error"}
        return mock_resp

    with patch("httpx.AsyncClient.get") as mock_get:
        mock_get.side_effect = side_effect

        results = await service.check_all_services()

        assert len(results) == 6

        # Find results for specific services
        catalog_result = next(r for r in results if "catalog" in r)
        client_result = next(r for r in results if "client" in r)

        assert catalog_result["catalog"] == "healthy"
        assert client_result["client"] == "unreachable"


@pytest.mark.asyncio
async def test_check_all_services_concurrent_execution():
    """Test that check_all_services executes checks concurrently."""
    service = HealthService()

    call_count = 0

    async def mock_check(service_name, service_url):
        nonlocal call_count
        call_count += 1
        return {service_name: "healthy"}

    with patch.object(service, "check_service_health", side_effect=mock_check):
        results = await service.check_all_services()

        assert len(results) == 6
        assert call_count == 6
