from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from src.domain.entities import Vehicle


class VehicleRepositoryPort(ABC):
    """Port for vehicle repository operations."""

    @abstractmethod
    async def save(self, vehicle: Vehicle) -> Vehicle:
        """Save a vehicle."""
        pass

    @abstractmethod
    async def find_by_id(self, vehicle_id: UUID) -> Optional[Vehicle]:
        """Find a vehicle by ID."""
        pass

    @abstractmethod
    async def find_by_placa(self, placa: str) -> Optional[Vehicle]:
        """Find a vehicle by placa."""
        pass

    @abstractmethod
    async def find_by_ids(self, vehicle_ids: List[UUID]) -> List[Vehicle]:
        """Find vehicles by list of IDs."""
        pass

    @abstractmethod
    async def find_all_active(self) -> List[Vehicle]:
        """Find all active vehicles."""
        pass

    @abstractmethod
    async def update(self, vehicle: Vehicle) -> Vehicle:
        """Update a vehicle."""
        pass

    @abstractmethod
    async def delete(self, vehicle_id: UUID) -> None:
        """Delete (deactivate) a vehicle."""
        pass
