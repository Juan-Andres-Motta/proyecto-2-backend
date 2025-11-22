from datetime import date
from typing import List, Optional, Tuple

from src.application.ports import RouteRepositoryPort, VehicleRepositoryPort
from src.domain.entities import Route


class ListRoutesUseCase:
    """Use case for listing routes with pagination."""

    def __init__(
        self,
        route_repository: RouteRepositoryPort,
        vehicle_repository: VehicleRepositoryPort,
    ):
        self._route_repo = route_repository
        self._vehicle_repo = vehicle_repository

    async def execute(
        self,
        fecha_ruta: Optional[date] = None,
        estado_ruta: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[dict], int]:
        """
        List routes with pagination and filters.

        Returns:
            Tuple of (routes with vehicle info, total count)
        """
        routes, total = await self._route_repo.find_all(
            fecha_ruta=fecha_ruta,
            estado_ruta=estado_ruta,
            page=page,
            page_size=page_size,
        )

        # Enrich with vehicle info
        result = []
        for route in routes:
            vehicle = await self._vehicle_repo.find_by_id(route.vehicle_id)
            result.append({
                "id": route.id,
                "vehicle_id": route.vehicle_id,
                "vehicle_plate": vehicle.placa if vehicle else None,
                "driver_name": vehicle.driver_name if vehicle else None,
                "fecha_ruta": route.fecha_ruta,
                "estado_ruta": route.estado_ruta.value,
                "duracion_estimada_minutos": route.duracion_estimada_minutos,
                "total_distance_km": float(route.total_distance_km),
                "total_orders": route.total_orders,
            })

        return result, total
