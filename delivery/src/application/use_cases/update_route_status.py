from uuid import UUID

from src.application.ports import RouteRepositoryPort, ShipmentRepositoryPort
from src.domain.entities import Route
from src.domain.exceptions import EntityNotFoundError, InvalidStatusTransitionError
from src.domain.value_objects import RouteStatus


class UpdateRouteStatusUseCase:
    """Use case for updating route status."""

    def __init__(
        self,
        route_repository: RouteRepositoryPort,
        shipment_repository: ShipmentRepositoryPort,
    ):
        self._route_repo = route_repository
        self._shipment_repo = shipment_repository

    async def execute(self, route_id: UUID, new_status: str) -> Route:
        """
        Update route status.

        Args:
            route_id: Route ID
            new_status: New status value

        Returns:
            Updated route

        Raises:
            EntityNotFoundError: If route not found
            InvalidStatusTransitionError: If transition is invalid
        """
        route = await self._route_repo.find_by_id(route_id)
        if not route:
            raise EntityNotFoundError("Route", str(route_id))

        target_status = RouteStatus(new_status)

        # Apply status transition
        if target_status == RouteStatus.EN_PROGRESO:
            route.start()
            # Update shipments to in_transit
            for shipment in route.shipments:
                await self._shipment_repo.update(shipment)
        elif target_status == RouteStatus.COMPLETADA:
            route.complete()
        elif target_status == RouteStatus.CANCELADA:
            route.cancel()
        else:
            raise InvalidStatusTransitionError(
                "Route",
                route.estado_ruta.value,
                new_status,
            )

        await self._route_repo.update(route)
        return route
