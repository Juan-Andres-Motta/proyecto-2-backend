import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import httpx

from src.adapters.output.adapters.nominatim_geocoding import NominatimGeocodingService
from src.domain.exceptions import GeocodingError


class TestNominatimGeocodingService:
    @pytest.fixture
    def service(self):
        return NominatimGeocodingService(
            base_url="https://nominatim.openstreetmap.org",
            rate_limit_seconds=0.01,  # Fast for tests
        )

    @pytest.mark.asyncio
    async def test_geocode_address_success(self, service):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {"lat": "4.60971", "lon": "-74.08175"}
        ]

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            lat, lon = await service.geocode_address(
                "Calle 123", "Bogota", "Colombia"
            )

            assert lat == Decimal("4.60971")
            assert lon == Decimal("-74.08175")

    @pytest.mark.asyncio
    async def test_geocode_address_no_results(self, service):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = []

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            with pytest.raises(GeocodingError) as exc_info:
                await service.geocode_address("Invalid", "City", "Country")

            assert "No results" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_geocode_address_api_error(self, service):
        mock_response = MagicMock()
        mock_response.status_code = 500

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            with pytest.raises(GeocodingError) as exc_info:
                await service.geocode_address("Calle 123", "Bogota", "Colombia")

            assert "API error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_geocode_address_timeout(self, service):
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=httpx.TimeoutException("Timeout")
            )

            with pytest.raises(GeocodingError) as exc_info:
                await service.geocode_address("Calle 123", "Bogota", "Colombia")

            assert "Timeout" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_geocode_address_http_error(self, service):
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=httpx.HTTPError("Network error")
            )

            with pytest.raises(GeocodingError) as exc_info:
                await service.geocode_address("Calle 123", "Bogota", "Colombia")

            assert "HTTP error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_geocode_address_invalid_response_key_error(self, service):
        """Test handling of invalid response missing lat/lon keys."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {"invalid": "data"}  # Missing lat/lon
        ]

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            with pytest.raises(GeocodingError) as exc_info:
                await service.geocode_address("Calle 123", "Bogota", "Colombia")

            assert "Invalid response" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_geocode_address_invalid_response_value_error(self, service):
        """Test handling of invalid lat/lon values."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {"lat": "not-a-number", "lon": "also-not"}
        ]

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            with pytest.raises(GeocodingError) as exc_info:
                await service.geocode_address("Calle 123", "Bogota", "Colombia")

            assert "Invalid response" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_geocode_address_rate_limiting(self):
        """Test that rate limiting works when requests are too fast."""
        import time

        # Create service with longer rate limit
        service = NominatimGeocodingService(
            base_url="https://nominatim.openstreetmap.org",
            rate_limit_seconds=0.1,
        )

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {"lat": "4.60971", "lon": "-74.08175"}
        ]

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            # Set last request time to now to trigger rate limiting
            service._last_request_time = time.time()

            start = time.time()
            await service.geocode_address("Calle 123", "Bogota", "Colombia")
            elapsed = time.time() - start

            # Should have waited due to rate limiting
            assert elapsed >= 0.05  # At least some delay
