from uuid import UUID

from src.application.ports import VehicleRepositoryPort
from src.domain.exceptions import EntityNotFoundError


class DeleteVehicleUseCase:
    """Use case for deleting (deactivating) a vehicle."""

    def __init__(self, vehicle_repository: VehicleRepositoryPort):
        self._vehicle_repo = vehicle_repository

    async def execute(self, vehicle_id: UUID) -> None:
        """
        Delete (deactivate) a vehicle.

        Args:
            vehicle_id: Vehicle ID

        Raises:
            EntityNotFoundError: If vehicle not found
        """
        vehicle = await self._vehicle_repo.find_by_id(vehicle_id)
        if not vehicle:
            raise EntityNotFoundError("Vehicle", str(vehicle_id))

        await self._vehicle_repo.delete(vehicle_id)
