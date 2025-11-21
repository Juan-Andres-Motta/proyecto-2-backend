from abc import ABC, abstractmethod
from datetime import date
from typing import List, Optional
from uuid import UUID

from src.domain.entities import Shipment


class ShipmentRepositoryPort(ABC):
    """Port for shipment repository operations."""

    @abstractmethod
    async def save(self, shipment: Shipment) -> Shipment:
        """Save a shipment."""
        pass

    @abstractmethod
    async def find_by_id(self, shipment_id: UUID) -> Optional[Shipment]:
        """Find a shipment by ID."""
        pass

    @abstractmethod
    async def find_by_order_id(self, order_id: UUID) -> Optional[Shipment]:
        """Find a shipment by order ID."""
        pass

    @abstractmethod
    async def find_pending_by_date(self, fecha_entrega_estimada: date) -> List[Shipment]:
        """Find all pending shipments for a specific delivery date."""
        pass

    @abstractmethod
    async def find_by_route_id(self, route_id: UUID) -> List[Shipment]:
        """Find all shipments for a route."""
        pass

    @abstractmethod
    async def update(self, shipment: Shipment) -> Shipment:
        """Update a shipment."""
        pass

    @abstractmethod
    async def update_many(self, shipments: List[Shipment]) -> List[Shipment]:
        """Update multiple shipments."""
        pass
