"""
Port interface for Delivery microservice operations (web app).

This defines the contract for route management, vehicle management,
and shipment tracking operations without specifying how the communication is implemented.
"""

from abc import ABC, abstractmethod
from datetime import date
from typing import Optional
from uuid import UUID

from web.schemas.delivery_schemas import (
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


class DeliveryPort(ABC):
    """
    Abstract port interface for web app delivery operations.

    Implementations of this port handle communication with the delivery
    microservice for route management, vehicle management, and shipment tracking.
    """

    # Routes Management

    @abstractmethod
    async def generate_routes(
        self, request: RouteGenerationRequest
    ) -> RouteGenerationResponse:
        """
        Trigger route generation for a specific date.

        Args:
            request: Route generation parameters

        Returns:
            RouteGenerationResponse with generation result

        Raises:
            MicroserviceValidationError: If the request data is invalid
            MicroserviceConnectionError: If unable to connect to delivery service
            MicroserviceHTTPError: If delivery service returns an error
        """
        pass

    @abstractmethod
    async def list_routes(
        self,
        fecha_ruta: Optional[date] = None,
        estado_ruta: Optional[str] = None,
    ) -> RoutesListResponse:
        """
        Retrieve routes with optional filters.

        Args:
            fecha_ruta: Optional date filter
            estado_ruta: Optional status filter

        Returns:
            RoutesListResponse with list of routes

        Raises:
            MicroserviceConnectionError: If unable to connect to delivery service
            MicroserviceHTTPError: If delivery service returns an error
        """
        pass

    @abstractmethod
    async def get_route(self, route_id: UUID) -> RouteDetailResponse:
        """
        Get detailed information for a specific route.

        Args:
            route_id: The route UUID

        Returns:
            RouteDetailResponse with route details and shipments

        Raises:
            MicroserviceConnectionError: If unable to connect to delivery service
            MicroserviceHTTPError: If delivery service returns an error (404 if not found)
        """
        pass

    @abstractmethod
    async def update_route_status(
        self, route_id: UUID, estado_ruta: str
    ) -> RouteResponse:
        """
        Update the status of a route.

        Args:
            route_id: The route UUID
            estado_ruta: New route status

        Returns:
            RouteResponse with updated route

        Raises:
            MicroserviceValidationError: If the status is invalid
            MicroserviceConnectionError: If unable to connect to delivery service
            MicroserviceHTTPError: If delivery service returns an error
        """
        pass

    # Vehicles Management

    @abstractmethod
    async def list_vehicles(self) -> VehiclesListResponse:
        """
        Retrieve all vehicles.

        Returns:
            VehiclesListResponse with list of vehicles

        Raises:
            MicroserviceConnectionError: If unable to connect to delivery service
            MicroserviceHTTPError: If delivery service returns an error
        """
        pass

    @abstractmethod
    async def create_vehicle(self, vehicle_data: VehicleCreateRequest) -> VehicleResponse:
        """
        Create a new vehicle.

        Args:
            vehicle_data: Vehicle creation data

        Returns:
            VehicleResponse with created vehicle

        Raises:
            MicroserviceValidationError: If the vehicle data is invalid
            MicroserviceConnectionError: If unable to connect to delivery service
            MicroserviceHTTPError: If delivery service returns an error
        """
        pass

    @abstractmethod
    async def update_vehicle(
        self, vehicle_id: UUID, vehicle_data: VehicleUpdateRequest
    ) -> VehicleResponse:
        """
        Update an existing vehicle.

        Args:
            vehicle_id: The vehicle UUID
            vehicle_data: Vehicle update data

        Returns:
            VehicleResponse with updated vehicle

        Raises:
            MicroserviceValidationError: If the vehicle data is invalid
            MicroserviceConnectionError: If unable to connect to delivery service
            MicroserviceHTTPError: If delivery service returns an error
        """
        pass

    @abstractmethod
    async def delete_vehicle(self, vehicle_id: UUID) -> None:
        """
        Delete a vehicle.

        Args:
            vehicle_id: The vehicle UUID

        Raises:
            MicroserviceConnectionError: If unable to connect to delivery service
            MicroserviceHTTPError: If delivery service returns an error (404 if not found)
        """
        pass

    # Shipments Management

    @abstractmethod
    async def update_shipment_status(
        self, order_id: UUID, shipment_status: str
    ) -> ShipmentResponse:
        """
        Update the status of a shipment by order ID.

        Args:
            order_id: The order UUID
            shipment_status: New shipment status

        Returns:
            ShipmentResponse with updated shipment

        Raises:
            MicroserviceValidationError: If the status is invalid
            MicroserviceConnectionError: If unable to connect to delivery service
            MicroserviceHTTPError: If delivery service returns an error
        """
        pass
