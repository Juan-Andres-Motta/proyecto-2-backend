import asyncio
import logging
from decimal import Decimal, InvalidOperation
from typing import Tuple

import httpx

from src.application.ports import GeocodingPort
from src.domain.exceptions import GeocodingError

logger = logging.getLogger(__name__)


class NominatimGeocodingService(GeocodingPort):
    """Nominatim geocoding service implementation."""

    def __init__(self, base_url: str, rate_limit_seconds: float = 1.0):
        self._base_url = base_url.rstrip("/")
        self._rate_limit = rate_limit_seconds
        self._last_request_time = 0.0

    async def geocode_address(
        self,
        address: str,
        city: str,
        country: str,
    ) -> Tuple[Decimal, Decimal]:
        """
        Geocode an address to coordinates using Nominatim.

        Args:
            address: Street address
            city: City name
            country: Country name

        Returns:
            Tuple of (latitude, longitude)

        Raises:
            GeocodingError: If geocoding fails
        """
        # Rate limiting
        import time
        current_time = time.time()
        time_since_last = current_time - self._last_request_time
        if time_since_last < self._rate_limit:
            await asyncio.sleep(self._rate_limit - time_since_last)

        # Build query
        query = f"{address}, {city}, {country}"
        url = f"{self._base_url}/search"
        params = {
            "q": query,
            "format": "json",
            "limit": 1,
        }
        headers = {
            "User-Agent": "MediSupply-DeliveryService/1.0",
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params, headers=headers, timeout=10.0)
                self._last_request_time = time.time()

                if response.status_code != 200:
                    raise GeocodingError(
                        f"Nominatim API error: {response.status_code}"
                    )

                results = response.json()
                if not results:
                    raise GeocodingError(f"No results for address: {query}")

                result = results[0]
                latitude = Decimal(result["lat"])
                longitude = Decimal(result["lon"])

                logger.info(f"Geocoded '{query}' to ({latitude}, {longitude})")
                return latitude, longitude

        except httpx.TimeoutException:
            raise GeocodingError(f"Timeout geocoding address: {query}")
        except httpx.HTTPError as e:
            raise GeocodingError(f"HTTP error geocoding address: {e}")
        except (KeyError, ValueError, InvalidOperation) as e:
            raise GeocodingError(f"Invalid response from Nominatim: {e}")
