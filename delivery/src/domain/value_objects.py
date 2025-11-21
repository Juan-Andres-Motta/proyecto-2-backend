from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from math import atan2, cos, radians, sin, sqrt


class ShipmentStatus(str, Enum):
    PENDING = "pending"
    ASSIGNED_TO_ROUTE = "assigned_to_route"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"


class RouteStatus(str, Enum):
    PLANEADA = "planeada"
    EN_PROGRESO = "en_progreso"
    COMPLETADA = "completada"
    CANCELADA = "cancelada"


class GeocodingStatus(str, Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"


@dataclass(frozen=True)
class Coordinates:
    """Immutable value object for geographic coordinates."""

    latitude: Decimal
    longitude: Decimal

    def distance_to(self, other: "Coordinates") -> float:
        """
        Calculate distance to another coordinate using Haversine formula.

        Returns:
            Distance in kilometers
        """
        R = 6371  # Earth's radius in km

        lat1 = radians(float(self.latitude))
        lat2 = radians(float(other.latitude))
        dlat = radians(float(other.latitude - self.latitude))
        dlon = radians(float(other.longitude - self.longitude))

        a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))

        return R * c
