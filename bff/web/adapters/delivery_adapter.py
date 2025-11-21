"""
Delivery adapter implementation for web app.

This adapter implements the DeliveryPort interface using HTTP communication
with the Delivery microservice for route, vehicle, and shipment management.
"""

import logging
from datetime import date
from typing import Optional
from uuid import UUID

from common.http_client import HttpClient

from ..ports.delivery_port import DeliveryPort
from ..schemas.delivery_schemas import (
    RouteDetailResponse,
    RouteGenerationRequest,
    RouteGenerationResponse,
    RouteResponse,
    RoutesListResponse,
    ShipmentResponse,
    VehicleCreateRequest,
    VehicleResponse,
    VehiclesListResponse,
    VehicleUpdateRequest,
)

logger = logging.getLogger(__name__)


class DeliveryAdapter(DeliveryPort):
    """
    HTTP adapter for delivery microservice operations (web app).

    This adapter implements the DeliveryPort interface and handles
    communication with the delivery microservice via HTTP for
    route management, vehicle management, and shipment tracking.
    """

    def __init__(self, http_client: HttpClient):
        """
        Initialize the delivery adapter.

        Args:
            http_client: Configured HTTP client for the delivery service
        """
        self.client = http_client

    # Routes Management

    async def generate_routes(
        self, request: RouteGenerationRequest
    ) -> RouteGenerationResponse:
        """Generate delivery routes for a specific date."""
        logger.info(
            f"Generating routes: fecha_entrega_estimada={request.fecha_entrega_estimada}, "
            f"vehicle_count={len(request.vehicle_ids)}"
        )
        response_data = await self.client.post(
            "/delivery/routes/generate",
            json=request.model_dump(mode="json"),
        )
        return RouteGenerationResponse(**response_data)

    async def list_routes(
        self,
        fecha_ruta: Optional[date] = None,
        estado_ruta: Optional[str] = None,
    ) -> RoutesListResponse:
        """Retrieve routes with optional filters."""
        logger.info(f"Listing routes: fecha_ruta={fecha_ruta}, estado_ruta={estado_ruta}")
        params = {}
        if fecha_ruta:
            params["fecha_ruta"] = fecha_ruta.isoformat()
        if estado_ruta:
            params["estado_ruta"] = estado_ruta

        response_data = await self.client.get(
            "/delivery/routes",
            params=params if params else None,
        )
        return RoutesListResponse(**response_data)

    async def get_route(self, route_id: UUID) -> RouteDetailResponse:
        """Get detailed information for a specific route."""
        logger.info(f"Getting route: route_id={route_id}")
        response_data = await self.client.get(
            f"/delivery/routes/{route_id}",
        )
        return RouteDetailResponse(**response_data)

    async def update_route_status(
        self, route_id: UUID, estado_ruta: str
    ) -> RouteResponse:
        """Update the status of a route."""
        logger.info(f"Updating route status: route_id={route_id}, estado_ruta={estado_ruta}")
        response_data = await self.client.patch(
            f"/delivery/routes/{route_id}/status",
            json={"estado_ruta": estado_ruta},
        )
        return RouteResponse(**response_data)

    # Vehicles Management

    async def list_vehicles(self) -> VehiclesListResponse:
        """Retrieve all vehicles."""
        logger.info("Listing vehicles")
        response_data = await self.client.get(
            "/delivery/vehicles",
        )
        return VehiclesListResponse(**response_data)

    async def create_vehicle(self, vehicle_data: VehicleCreateRequest) -> VehicleResponse:
        """Create a new vehicle."""
        logger.info(f"Creating vehicle: placa={vehicle_data.placa}")
        response_data = await self.client.post(
            "/delivery/vehicles",
            json=vehicle_data.model_dump(mode="json"),
        )
        return VehicleResponse(**response_data)

    async def update_vehicle(
        self, vehicle_id: UUID, vehicle_data: VehicleUpdateRequest
    ) -> VehicleResponse:
        """Update an existing vehicle."""
        logger.info(f"Updating vehicle: vehicle_id={vehicle_id}")
        # Only send non-None fields
        update_payload = vehicle_data.model_dump(mode="json", exclude_none=True)
        response_data = await self.client.patch(
            f"/delivery/vehicles/{vehicle_id}",
            json=update_payload,
        )
        return VehicleResponse(**response_data)

    async def delete_vehicle(self, vehicle_id: UUID) -> None:
        """Delete a vehicle."""
        logger.info(f"Deleting vehicle: vehicle_id={vehicle_id}")
        await self.client.delete(
            f"/delivery/vehicles/{vehicle_id}",
        )

    # Shipments Management

    async def update_shipment_status(
        self, order_id: UUID, shipment_status: str
    ) -> ShipmentResponse:
        """Update the status of a shipment by order ID."""
        logger.info(f"Updating shipment status: order_id={order_id}, shipment_status={shipment_status}")
        response_data = await self.client.patch(
            f"/delivery/orders/{order_id}/shipment/status",
            json={"shipment_status": shipment_status},
        )
        return ShipmentResponse(**response_data)
