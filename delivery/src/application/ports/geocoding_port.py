from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Tuple


class GeocodingPort(ABC):
    """Port for geocoding service."""

    @abstractmethod
    async def geocode_address(
        self,
        address: str,
        city: str,
        country: str,
    ) -> Tuple[Decimal, Decimal]:
        """
        Geocode an address to coordinates.

        Args:
            address: Street address
            city: City name
            country: Country name

        Returns:
            Tuple of (latitude, longitude)

        Raises:
            GeocodingError: If geocoding fails
        """
        pass
