from uuid import UUID

from src.application.ports import RouteRepositoryPort, VehicleRepositoryPort
from src.domain.exceptions import EntityNotFoundError


class GetRouteUseCase:
    """Use case for getting route details."""

    def __init__(
        self,
        route_repository: RouteRepositoryPort,
        vehicle_repository: VehicleRepositoryPort,
    ):
        self._route_repo = route_repository
        self._vehicle_repo = vehicle_repository

    async def execute(self, route_id: UUID) -> dict:
        """
        Get route details with shipments and vehicle info.

        Returns:
            Route details with shipments

        Raises:
            EntityNotFoundError: If route not found
        """
        route = await self._route_repo.find_by_id(route_id)
        if not route:
            raise EntityNotFoundError("Route", str(route_id))

        vehicle = await self._vehicle_repo.find_by_id(route.vehicle_id)

        shipments = [
            {
                "id": s.id,
                "order_id": s.order_id,
                "direccion_entrega": s.direccion_entrega,
                "ciudad_entrega": s.ciudad_entrega,
                "sequence_in_route": s.sequence_in_route,
                "shipment_status": s.shipment_status.value,
            }
            for s in route.shipments
        ]

        return {
            "id": route.id,
            "vehicle_id": route.vehicle_id,
            "vehicle_plate": vehicle.placa if vehicle else None,
            "driver_name": vehicle.driver_name if vehicle else None,
            "driver_phone": vehicle.driver_phone if vehicle else None,
            "fecha_ruta": route.fecha_ruta,
            "estado_ruta": route.estado_ruta.value,
            "duracion_estimada_minutos": route.duracion_estimada_minutos,
            "total_distance_km": float(route.total_distance_km),
            "total_orders": route.total_orders,
            "shipments": shipments,
        }
