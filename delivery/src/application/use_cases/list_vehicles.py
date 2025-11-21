from typing import List

from src.application.ports import VehicleRepositoryPort
from src.domain.entities import Vehicle


class ListVehiclesUseCase:
    """Use case for listing active vehicles."""

    def __init__(self, vehicle_repository: VehicleRepositoryPort):
        self._vehicle_repo = vehicle_repository

    async def execute(self) -> List[Vehicle]:
        """
        List all active vehicles.

        Returns:
            List of active vehicles
        """
        return await self._vehicle_repo.find_all_active()
