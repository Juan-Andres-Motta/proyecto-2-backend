from typing import Optional
from uuid import UUID

from src.application.ports import VehicleRepositoryPort
from src.domain.entities import Vehicle
from src.domain.exceptions import EntityNotFoundError


class UpdateVehicleUseCase:
    """Use case for updating a vehicle."""

    def __init__(self, vehicle_repository: VehicleRepositoryPort):
        self._vehicle_repo = vehicle_repository

    async def execute(
        self,
        vehicle_id: UUID,
        driver_name: Optional[str] = None,
        driver_phone: Optional[str] = None,
    ) -> Vehicle:
        """
        Update a vehicle.

        Args:
            vehicle_id: Vehicle ID
            driver_name: New driver name (optional)
            driver_phone: New driver phone (optional)

        Returns:
            Updated vehicle

        Raises:
            EntityNotFoundError: If vehicle not found
        """
        vehicle = await self._vehicle_repo.find_by_id(vehicle_id)
        if not vehicle:
            raise EntityNotFoundError("Vehicle", str(vehicle_id))

        vehicle.update(driver_name=driver_name, driver_phone=driver_phone)
        await self._vehicle_repo.update(vehicle)
        return vehicle
