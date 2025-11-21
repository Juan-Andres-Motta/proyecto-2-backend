from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.ports import VehicleRepositoryPort
from src.domain.entities import Vehicle
from src.infrastructure.database.models import VehicleModel


class SQLAlchemyVehicleRepository(VehicleRepositoryPort):
    """SQLAlchemy implementation of vehicle repository."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def save(self, vehicle: Vehicle) -> Vehicle:
        """Save a vehicle."""
        model = VehicleModel(
            id=vehicle.id,
            placa=vehicle.placa,
            driver_name=vehicle.driver_name,
            driver_phone=vehicle.driver_phone,
            is_active=vehicle.is_active,
        )
        self._session.add(model)
        await self._session.flush()
        return vehicle

    async def find_by_id(self, vehicle_id: UUID) -> Optional[Vehicle]:
        """Find a vehicle by ID."""
        result = await self._session.execute(
            select(VehicleModel).where(VehicleModel.id == vehicle_id)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def find_by_placa(self, placa: str) -> Optional[Vehicle]:
        """Find a vehicle by placa."""
        result = await self._session.execute(
            select(VehicleModel).where(VehicleModel.placa == placa)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def find_by_ids(self, vehicle_ids: List[UUID]) -> List[Vehicle]:
        """Find vehicles by list of IDs."""
        if not vehicle_ids:
            return []
        result = await self._session.execute(
            select(VehicleModel).where(VehicleModel.id.in_(vehicle_ids))
        )
        models = result.scalars().all()
        return [self._to_entity(m) for m in models]

    async def find_all_active(self) -> List[Vehicle]:
        """Find all active vehicles."""
        result = await self._session.execute(
            select(VehicleModel)
            .where(VehicleModel.is_active == True)
            .order_by(VehicleModel.placa)
        )
        models = result.scalars().all()
        return [self._to_entity(m) for m in models]

    async def update(self, vehicle: Vehicle) -> Vehicle:
        """Update a vehicle."""
        result = await self._session.execute(
            select(VehicleModel).where(VehicleModel.id == vehicle.id)
        )
        model = result.scalar_one_or_none()
        if model:
            model.placa = vehicle.placa
            model.driver_name = vehicle.driver_name
            model.driver_phone = vehicle.driver_phone
            model.is_active = vehicle.is_active
            await self._session.flush()
        return vehicle

    async def delete(self, vehicle_id: UUID) -> None:
        """Delete (deactivate) a vehicle."""
        result = await self._session.execute(
            select(VehicleModel).where(VehicleModel.id == vehicle_id)
        )
        model = result.scalar_one_or_none()
        if model:
            model.is_active = False
            await self._session.flush()

    def _to_entity(self, model: VehicleModel) -> Vehicle:
        """Convert model to entity."""
        return Vehicle(
            id=model.id,
            placa=model.placa,
            driver_name=model.driver_name,
            driver_phone=model.driver_phone,
            is_active=model.is_active,
        )
