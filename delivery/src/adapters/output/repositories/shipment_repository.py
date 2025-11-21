from datetime import date
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.ports import ShipmentRepositoryPort
from src.domain.entities import Shipment
from src.domain.value_objects import GeocodingStatus, ShipmentStatus
from src.infrastructure.database.models import ShipmentModel


class SQLAlchemyShipmentRepository(ShipmentRepositoryPort):
    """SQLAlchemy implementation of shipment repository."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def save(self, shipment: Shipment) -> Shipment:
        """Save a shipment."""
        model = ShipmentModel(
            id=shipment.id,
            order_id=shipment.order_id,
            customer_id=shipment.customer_id,
            direccion_entrega=shipment.direccion_entrega,
            ciudad_entrega=shipment.ciudad_entrega,
            pais_entrega=shipment.pais_entrega,
            latitude=shipment.latitude,
            longitude=shipment.longitude,
            geocoding_status=shipment.geocoding_status.value,
            route_id=shipment.route_id,
            sequence_in_route=shipment.sequence_in_route,
            fecha_pedido=shipment.fecha_pedido,
            fecha_entrega_estimada=shipment.fecha_entrega_estimada,
            shipment_status=shipment.shipment_status.value,
        )
        self._session.add(model)
        await self._session.flush()
        return shipment

    async def find_by_id(self, shipment_id: UUID) -> Optional[Shipment]:
        """Find a shipment by ID."""
        result = await self._session.execute(
            select(ShipmentModel).where(ShipmentModel.id == shipment_id)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def find_by_order_id(self, order_id: UUID) -> Optional[Shipment]:
        """Find a shipment by order ID."""
        result = await self._session.execute(
            select(ShipmentModel).where(ShipmentModel.order_id == order_id)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def find_pending_by_date(self, fecha_entrega_estimada: date) -> List[Shipment]:
        """Find all pending shipments for a specific delivery date."""
        result = await self._session.execute(
            select(ShipmentModel)
            .where(ShipmentModel.fecha_entrega_estimada == fecha_entrega_estimada)
            .where(ShipmentModel.shipment_status == ShipmentStatus.PENDING.value)
            .order_by(ShipmentModel.created_at)
        )
        models = result.scalars().all()
        return [self._to_entity(m) for m in models]

    async def find_by_route_id(self, route_id: UUID) -> List[Shipment]:
        """Find all shipments for a route."""
        result = await self._session.execute(
            select(ShipmentModel)
            .where(ShipmentModel.route_id == route_id)
            .order_by(ShipmentModel.sequence_in_route)
        )
        models = result.scalars().all()
        return [self._to_entity(m) for m in models]

    async def update(self, shipment: Shipment) -> Shipment:
        """Update a shipment."""
        result = await self._session.execute(
            select(ShipmentModel).where(ShipmentModel.id == shipment.id)
        )
        model = result.scalar_one_or_none()
        if model:
            model.latitude = shipment.latitude
            model.longitude = shipment.longitude
            model.geocoding_status = shipment.geocoding_status.value
            model.route_id = shipment.route_id
            model.sequence_in_route = shipment.sequence_in_route
            model.shipment_status = shipment.shipment_status.value
            await self._session.flush()
        return shipment

    async def update_many(self, shipments: List[Shipment]) -> List[Shipment]:
        """Update multiple shipments."""
        for shipment in shipments:
            await self.update(shipment)
        return shipments

    def _to_entity(self, model: ShipmentModel) -> Shipment:
        """Convert model to entity."""
        return Shipment(
            id=model.id,
            order_id=model.order_id,
            customer_id=model.customer_id,
            direccion_entrega=model.direccion_entrega,
            ciudad_entrega=model.ciudad_entrega,
            pais_entrega=model.pais_entrega,
            latitude=model.latitude,
            longitude=model.longitude,
            geocoding_status=GeocodingStatus(model.geocoding_status),
            route_id=model.route_id,
            sequence_in_route=model.sequence_in_route,
            fecha_pedido=model.fecha_pedido,
            fecha_entrega_estimada=model.fecha_entrega_estimada,
            shipment_status=ShipmentStatus(model.shipment_status),
        )
