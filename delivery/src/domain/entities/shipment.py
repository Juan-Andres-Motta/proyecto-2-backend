from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Optional
from uuid import UUID

from ..value_objects import Coordinates, GeocodingStatus, ShipmentStatus


@dataclass
class Shipment:
    """Shipment aggregate root entity."""

    id: UUID
    order_id: UUID
    customer_id: UUID
    direccion_entrega: str
    ciudad_entrega: str
    pais_entrega: str
    fecha_pedido: datetime
    fecha_entrega_estimada: date

    # Optional fields
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None
    geocoding_status: GeocodingStatus = GeocodingStatus.PENDING
    route_id: Optional[UUID] = None
    sequence_in_route: Optional[int] = None
    shipment_status: ShipmentStatus = ShipmentStatus.PENDING

    def __post_init__(self):
        self.validate()

    def validate(self) -> None:
        if not self.direccion_entrega:
            raise ValueError("direccion_entrega is required")
        if not self.ciudad_entrega:
            raise ValueError("ciudad_entrega is required")
        if not self.pais_entrega:
            raise ValueError("pais_entrega is required")

    @classmethod
    def calculate_estimated_delivery(cls, fecha_pedido: datetime) -> date:
        """
        Calculate estimated delivery date.

        Business Rule: fecha_entrega_estimada = fecha_pedido + 1 day
        (at most 2 days after order creation)
        """
        return (fecha_pedido + timedelta(days=1)).date()

    def set_coordinates(self, latitude: Decimal, longitude: Decimal) -> None:
        """Set geocoded coordinates and update status."""
        self.latitude = latitude
        self.longitude = longitude
        self.geocoding_status = GeocodingStatus.SUCCESS

    def mark_geocoding_failed(self) -> None:
        """Mark geocoding as failed."""
        self.geocoding_status = GeocodingStatus.FAILED

    def assign_to_route(self, route_id: UUID, sequence: int) -> None:
        """
        Assign shipment to a route.

        Business Rule: Can only assign if status is PENDING
        """
        if self.shipment_status != ShipmentStatus.PENDING:
            raise ValueError(
                f"Cannot assign shipment to route. "
                f"Current status: {self.shipment_status}"
            )

        self.route_id = route_id
        self.sequence_in_route = sequence
        self.shipment_status = ShipmentStatus.ASSIGNED_TO_ROUTE

    def mark_in_transit(self) -> None:
        """Mark shipment as in transit."""
        if self.shipment_status != ShipmentStatus.ASSIGNED_TO_ROUTE:
            raise ValueError(
                f"Cannot mark as in transit. "
                f"Current status: {self.shipment_status}"
            )
        self.shipment_status = ShipmentStatus.IN_TRANSIT

    def mark_delivered(self) -> None:
        """Mark shipment as delivered."""
        if self.shipment_status != ShipmentStatus.IN_TRANSIT:
            raise ValueError(
                f"Cannot mark as delivered. "
                f"Current status: {self.shipment_status}"
            )
        self.shipment_status = ShipmentStatus.DELIVERED

    @property
    def coordinates(self) -> Optional[Coordinates]:
        """Get coordinates as value object."""
        if self.latitude is not None and self.longitude is not None:
            return Coordinates(self.latitude, self.longitude)
        return None

    @property
    def is_geocoded(self) -> bool:
        """Check if shipment has valid coordinates."""
        return self.geocoding_status == GeocodingStatus.SUCCESS
