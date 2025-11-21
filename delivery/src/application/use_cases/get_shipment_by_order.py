from typing import Optional
from uuid import UUID

from src.application.ports import ShipmentRepositoryPort, VehicleRepositoryPort, RouteRepositoryPort
from src.domain.entities import Shipment
from src.domain.exceptions import EntityNotFoundError


class GetShipmentByOrderUseCase:
    """Use case for getting shipment information by order ID."""

    def __init__(
        self,
        shipment_repository: ShipmentRepositoryPort,
        vehicle_repository: VehicleRepositoryPort,
        route_repository: RouteRepositoryPort,
    ):
        self._shipment_repo = shipment_repository
        self._vehicle_repo = vehicle_repository
        self._route_repo = route_repository

    async def execute(self, order_id: UUID) -> dict:
        """
        Get shipment information for Order Service enrichment.

        Args:
            order_id: Order ID

        Returns:
            Shipment info with vehicle details

        Raises:
            EntityNotFoundError: If shipment not found
        """
        shipment = await self._shipment_repo.find_by_order_id(order_id)
        if not shipment:
            raise EntityNotFoundError("Shipment", str(order_id))

        # Get vehicle info if assigned to route
        vehicle_plate = None
        driver_name = None

        if shipment.route_id:
            route = await self._route_repo.find_by_id(shipment.route_id)
            if route:
                vehicle = await self._vehicle_repo.find_by_id(route.vehicle_id)
                if vehicle:
                    vehicle_plate = vehicle.placa
                    driver_name = vehicle.driver_name

        return {
            "shipment_id": shipment.id,
            "order_id": shipment.order_id,
            "shipment_status": shipment.shipment_status.value,
            "vehicle_plate": vehicle_plate,
            "driver_name": driver_name,
            "fecha_entrega_estimada": shipment.fecha_entrega_estimada,
            "route_id": shipment.route_id,
        }
