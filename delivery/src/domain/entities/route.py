from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from ..value_objects import RouteStatus, ShipmentStatus
from .shipment import Shipment


@dataclass
class Route:
    """Route aggregate root entity."""

    id: UUID
    vehicle_id: UUID
    fecha_ruta: date

    # Calculated fields
    estado_ruta: RouteStatus = RouteStatus.PLANEADA
    duracion_estimada_minutos: int = 0
    total_distance_km: Decimal = Decimal("0.00")
    total_orders: int = 0

    # Relationships
    _shipments: List[Shipment] = field(default_factory=list)

    def add_shipment(self, shipment: Shipment, sequence: int) -> None:
        """Add a shipment to this route."""
        shipment.assign_to_route(self.id, sequence)
        self._shipments.append(shipment)
        self.total_orders = len(self._shipments)

    @property
    def shipments(self) -> List[Shipment]:
        """Get ordered list of shipments."""
        return sorted(self._shipments, key=lambda s: s.sequence_in_route or 0)

    def set_shipments(self, shipments: List[Shipment]) -> None:
        """Set shipments directly (used when loading from database)."""
        self._shipments = shipments
        self.total_orders = len(shipments)

    def start(self) -> None:
        """Start the route delivery."""
        if self.estado_ruta != RouteStatus.PLANEADA:
            raise ValueError(
                f"Cannot start route. Current status: {self.estado_ruta}"
            )
        self.estado_ruta = RouteStatus.EN_PROGRESO

        # Mark all shipments as in transit
        for shipment in self._shipments:
            if shipment.shipment_status == ShipmentStatus.ASSIGNED_TO_ROUTE:
                shipment.mark_in_transit()

    def complete(self) -> None:
        """Complete the route."""
        if self.estado_ruta != RouteStatus.EN_PROGRESO:
            raise ValueError(
                f"Cannot complete route. Current status: {self.estado_ruta}"
            )
        self.estado_ruta = RouteStatus.COMPLETADA

    def cancel(self) -> None:
        """Cancel the route."""
        if self.estado_ruta not in [RouteStatus.PLANEADA, RouteStatus.EN_PROGRESO]:
            raise ValueError(
                f"Cannot cancel route. Current status: {self.estado_ruta}"
            )
        self.estado_ruta = RouteStatus.CANCELADA
