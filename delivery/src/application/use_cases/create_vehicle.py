from typing import Optional
from uuid import uuid4

from src.application.ports import VehicleRepositoryPort
from src.domain.entities import Vehicle
from src.domain.exceptions import ValidationError


class CreateVehicleUseCase:
    """Use case for creating a vehicle."""

    def __init__(self, vehicle_repository: VehicleRepositoryPort):
        self._vehicle_repo = vehicle_repository

    async def execute(
        self,
        placa: str,
        driver_name: str,
        driver_phone: Optional[str] = None,
    ) -> Vehicle:
        """
        Create a new vehicle.

        Args:
            placa: Vehicle plate
            driver_name: Driver name
            driver_phone: Driver phone (optional)

        Returns:
            Created vehicle

        Raises:
            ValidationError: If placa already exists
        """
        # Check for duplicate placa
        existing = await self._vehicle_repo.find_by_placa(placa)
        if existing:
            raise ValidationError(f"Vehicle with placa {placa} already exists")

        vehicle = Vehicle(
            id=uuid4(),
            placa=placa,
            driver_name=driver_name,
            driver_phone=driver_phone,
        )

        await self._vehicle_repo.save(vehicle)
        return vehicle
