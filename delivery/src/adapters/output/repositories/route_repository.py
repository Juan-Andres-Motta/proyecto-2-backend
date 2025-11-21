from datetime import date
from typing import List, Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.application.ports import RouteRepositoryPort
from src.domain.entities import Route, Shipment
from src.domain.value_objects import GeocodingStatus, RouteStatus, ShipmentStatus
from src.infrastructure.database.models import RouteModel, ShipmentModel


class SQLAlchemyRouteRepository(RouteRepositoryPort):
    """SQLAlchemy implementation of route repository."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def save(self, route: Route) -> Route:
        """Save a route with its shipments."""
        model = RouteModel(
            id=route.id,
            vehicle_id=route.vehicle_id,
            fecha_ruta=route.fecha_ruta,
            estado_ruta=route.estado_ruta.value,
            duracion_estimada_minutos=route.duracion_estimada_minutos,
            total_distance_km=route.total_distance_km,
            total_orders=route.total_orders,
        )
        self._session.add(model)
        await self._session.flush()
        return route

    async def find_by_id(self, route_id: UUID) -> Optional[Route]:
        """Find a route by ID with shipments."""
        result = await self._session.execute(
            select(RouteModel)
            .options(selectinload(RouteModel.shipments))
            .where(RouteModel.id == route_id)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def find_by_date(self, fecha_ruta: date) -> List[Route]:
        """Find all routes for a specific date."""
        result = await self._session.execute(
            select(RouteModel)
            .options(selectinload(RouteModel.shipments))
            .where(RouteModel.fecha_ruta == fecha_ruta)
            .order_by(RouteModel.created_at)
        )
        models = result.scalars().all()
        return [self._to_entity(m) for m in models]

    async def find_by_date_and_status(
        self, fecha_ruta: date, estado_ruta: str
    ) -> List[Route]:
        """Find routes by date and status."""
        result = await self._session.execute(
            select(RouteModel)
            .options(selectinload(RouteModel.shipments))
            .where(RouteModel.fecha_ruta == fecha_ruta)
            .where(RouteModel.estado_ruta == estado_ruta)
            .order_by(RouteModel.created_at)
        )
        models = result.scalars().all()
        return [self._to_entity(m) for m in models]

    async def find_all(
        self,
        fecha_ruta: Optional[date] = None,
        estado_ruta: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[List[Route], int]:
        """Find routes with pagination and filters."""
        query = select(RouteModel).options(selectinload(RouteModel.shipments))
        count_query = select(func.count(RouteModel.id))

        if fecha_ruta:
            query = query.where(RouteModel.fecha_ruta == fecha_ruta)
            count_query = count_query.where(RouteModel.fecha_ruta == fecha_ruta)

        if estado_ruta:
            query = query.where(RouteModel.estado_ruta == estado_ruta)
            count_query = count_query.where(RouteModel.estado_ruta == estado_ruta)

        # Get total count
        count_result = await self._session.execute(count_query)
        total = count_result.scalar() or 0

        # Apply pagination
        offset = (page - 1) * page_size
        query = query.order_by(RouteModel.fecha_ruta.desc(), RouteModel.created_at.desc())
        query = query.offset(offset).limit(page_size)

        result = await self._session.execute(query)
        models = result.scalars().all()

        return [self._to_entity(m) for m in models], total

    async def update(self, route: Route) -> Route:
        """Update a route."""
        result = await self._session.execute(
            select(RouteModel).where(RouteModel.id == route.id)
        )
        model = result.scalar_one_or_none()
        if model:
            model.estado_ruta = route.estado_ruta.value
            model.duracion_estimada_minutos = route.duracion_estimada_minutos
            model.total_distance_km = route.total_distance_km
            model.total_orders = route.total_orders
            await self._session.flush()
        return route

    def _to_entity(self, model: RouteModel) -> Route:
        """Convert model to entity."""
        route = Route(
            id=model.id,
            vehicle_id=model.vehicle_id,
            fecha_ruta=model.fecha_ruta,
            estado_ruta=RouteStatus(model.estado_ruta),
            duracion_estimada_minutos=model.duracion_estimada_minutos,
            total_distance_km=model.total_distance_km,
            total_orders=model.total_orders,
        )

        # Load shipments if available
        if model.shipments:
            shipments = [
                Shipment(
                    id=s.id,
                    order_id=s.order_id,
                    customer_id=s.customer_id,
                    direccion_entrega=s.direccion_entrega,
                    ciudad_entrega=s.ciudad_entrega,
                    pais_entrega=s.pais_entrega,
                    latitude=s.latitude,
                    longitude=s.longitude,
                    geocoding_status=GeocodingStatus(s.geocoding_status),
                    route_id=s.route_id,
                    sequence_in_route=s.sequence_in_route,
                    fecha_pedido=s.fecha_pedido,
                    fecha_entrega_estimada=s.fecha_entrega_estimada,
                    shipment_status=ShipmentStatus(s.shipment_status),
                )
                for s in model.shipments
            ]
            route.set_shipments(shipments)

        return route
