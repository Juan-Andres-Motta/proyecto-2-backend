"""Unit tests for delivery controller."""

from datetime import date, datetime
from unittest.mock import AsyncMock, Mock
from uuid import UUID, uuid4

import pytest
from fastapi import HTTPException

from common.exceptions import (
    MicroserviceConnectionError,
    MicroserviceHTTPError,
    MicroserviceValidationError,
)
from web.controllers.delivery_controller import (
    delete_vehicle,
    generate_routes,
    get_route,
    get_routes,
    get_vehicles,
    create_vehicle,
    update_route_status,
    update_shipment_status,
    update_vehicle,
)
from web.ports.delivery_port import DeliveryPort
from web.schemas.delivery_schemas import (
    RouteDetailResponse,
    RouteGenerationRequest,
    RouteGenerationResponse,
    RouteResponse,
    RoutesListResponse,
    RouteStatusUpdateRequest,
    ShipmentInRoute,
    ShipmentResponse,
    ShipmentStatusUpdateRequest,
    VehicleCreateRequest,
    VehicleInRoute,
    VehicleResponse,
    VehiclesListResponse,
    VehicleUpdateRequest,
)


@pytest.fixture
def mock_delivery_port():
    """Create a mock delivery port."""
    return Mock(spec=DeliveryPort)


@pytest.fixture
def mock_web_user():
    """Mock authenticated web admin user."""
    return {
        "sub": str(uuid4()),
        "email": "admin@medisupply.com",
        "cognito:groups": ["web_users"],
    }


# Route Generation Endpoint Tests


class TestGenerateRoutes:
    """Test generate_routes endpoint."""

    @pytest.mark.asyncio
    async def test_generate_routes_success(self, mock_delivery_port, mock_web_user):
        """Test successful route generation."""
        request_data = RouteGenerationRequest(
            fecha_entrega_estimada=date(2025, 1, 15),
            vehicle_ids=[uuid4(), uuid4()],
        )

        response = RouteGenerationResponse(
            message="Route generation job accepted",
            fecha_entrega_estimada=date(2025, 1, 15),
            num_vehicles=2,
            num_pending_shipments=5,
        )

        mock_delivery_port.generate_routes = AsyncMock(return_value=response)

        result = await generate_routes(request_data, mock_delivery_port, mock_web_user)

        assert result.message == "Route generation job accepted"
        assert result.num_vehicles == 2
        assert result.fecha_entrega_estimada == date(2025, 1, 15)
        mock_delivery_port.generate_routes.assert_called_once_with(request_data)

    @pytest.mark.asyncio
    async def test_generate_routes_validation_error(self, mock_delivery_port, mock_web_user):
        """Test generate_routes with validation error."""
        request_data = RouteGenerationRequest(
            fecha_entrega_estimada=date(2025, 1, 15),
            vehicle_ids=[uuid4()],
        )

        mock_delivery_port.generate_routes = AsyncMock(
            side_effect=MicroserviceValidationError(
                service_name="Delivery",
                message="Invalid vehicle IDs",
                status_code=400,
            )
        )

        with pytest.raises(HTTPException) as exc_info:
            await generate_routes(request_data, mock_delivery_port, mock_web_user)

        assert exc_info.value.status_code == 400
        assert "Invalid data" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_generate_routes_connection_error(self, mock_delivery_port, mock_web_user):
        """Test generate_routes with connection error."""
        request_data = RouteGenerationRequest(
            fecha_entrega_estimada=date(2025, 1, 15),
            vehicle_ids=[uuid4()],
        )

        mock_delivery_port.generate_routes = AsyncMock(
            side_effect=MicroserviceConnectionError(
                service_name="Delivery",
                original_error="Connection timeout",
            )
        )

        with pytest.raises(HTTPException) as exc_info:
            await generate_routes(request_data, mock_delivery_port, mock_web_user)

        assert exc_info.value.status_code == 503
        assert "unavailable" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_generate_routes_http_error_500(self, mock_delivery_port, mock_web_user):
        """Test generate_routes with HTTP 500 error."""
        request_data = RouteGenerationRequest(
            fecha_entrega_estimada=date(2025, 1, 15),
            vehicle_ids=[uuid4()],
        )

        mock_delivery_port.generate_routes = AsyncMock(
            side_effect=MicroserviceHTTPError(
                service_name="Delivery",
                status_code=500,
                response_text="Internal server error",
            )
        )

        with pytest.raises(HTTPException) as exc_info:
            await generate_routes(request_data, mock_delivery_port, mock_web_user)

        assert exc_info.value.status_code == 500
        assert "Delivery service error" in exc_info.value.detail


# Routes List Endpoint Tests


class TestGetRoutes:
    """Test get_routes endpoint."""

    @pytest.mark.asyncio
    async def test_get_routes_success_no_filters(self, mock_delivery_port, mock_web_user):
        """Test retrieving routes without filters."""
        route_id = uuid4()
        vehicle_id = uuid4()

        response = RoutesListResponse(
            items=[
                RouteResponse(
                    id=route_id,
                    fecha_ruta=date(2025, 1, 15),
                    estado_ruta="pendiente",
                    vehicle_id=vehicle_id,
                )
            ],
            total=1,
        )

        mock_delivery_port.list_routes = AsyncMock(return_value=response)

        result = await get_routes(
            fecha_ruta=None,
            estado_ruta=None,
            port=mock_delivery_port,
            user=mock_web_user,
        )

        assert result.total == 1
        assert len(result.items) == 1
        assert result.items[0].estado_ruta == "pendiente"
        mock_delivery_port.list_routes.assert_called_once_with(
            fecha_ruta=None, estado_ruta=None
        )

    @pytest.mark.asyncio
    async def test_get_routes_with_date_filter(self, mock_delivery_port, mock_web_user):
        """Test retrieving routes with date filter."""
        route_id = uuid4()
        vehicle_id = uuid4()
        filter_date = date(2025, 1, 15)

        response = RoutesListResponse(
            items=[
                RouteResponse(
                    id=route_id,
                    fecha_ruta=filter_date,
                    estado_ruta="en_progreso",
                    vehicle_id=vehicle_id,
                )
            ],
            total=1,
        )

        mock_delivery_port.list_routes = AsyncMock(return_value=response)

        result = await get_routes(
            fecha_ruta=filter_date,
            estado_ruta=None,
            port=mock_delivery_port,
            user=mock_web_user,
        )

        assert result.total == 1
        mock_delivery_port.list_routes.assert_called_once_with(
            fecha_ruta=filter_date, estado_ruta=None
        )

    @pytest.mark.asyncio
    async def test_get_routes_with_status_filter(self, mock_delivery_port, mock_web_user):
        """Test retrieving routes with status filter."""
        route_id = uuid4()
        vehicle_id = uuid4()

        response = RoutesListResponse(
            items=[
                RouteResponse(
                    id=route_id,
                    fecha_ruta=date(2025, 1, 15),
                    estado_ruta="completada",
                    vehicle_id=vehicle_id,
                )
            ],
            total=1,
        )

        mock_delivery_port.list_routes = AsyncMock(return_value=response)

        result = await get_routes(
            fecha_ruta=None,
            estado_ruta="completada",
            port=mock_delivery_port,
            user=mock_web_user,
        )

        assert result.total == 1
        assert result.items[0].estado_ruta == "completada"
        mock_delivery_port.list_routes.assert_called_once_with(
            fecha_ruta=None, estado_ruta="completada"
        )

    @pytest.mark.asyncio
    async def test_get_routes_empty_list(self, mock_delivery_port, mock_web_user):
        """Test retrieving routes when none exist."""
        response = RoutesListResponse(items=[], total=0)

        mock_delivery_port.list_routes = AsyncMock(return_value=response)

        result = await get_routes(
            fecha_ruta=None,
            estado_ruta=None,
            port=mock_delivery_port,
            user=mock_web_user,
        )

        assert result.total == 0
        assert len(result.items) == 0

    @pytest.mark.asyncio
    async def test_get_routes_validation_error(self, mock_delivery_port, mock_web_user):
        """Test get_routes with validation error."""
        mock_delivery_port.list_routes = AsyncMock(
            side_effect=MicroserviceValidationError(
                service_name="Delivery",
                message="Invalid date format",
                status_code=400,
                details={"field": "fecha_ruta", "message": "Invalid date format"},
            )
        )

        with pytest.raises(HTTPException) as exc_info:
            await get_routes(
                fecha_ruta=None,
                estado_ruta=None,
                port=mock_delivery_port,
                user=mock_web_user,
            )

        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_get_routes_connection_error(self, mock_delivery_port, mock_web_user):
        """Test get_routes with connection error."""
        mock_delivery_port.list_routes = AsyncMock(
            side_effect=MicroserviceConnectionError(
                service_name="Delivery",
                original_error="Connection timeout",
            )
        )

        with pytest.raises(HTTPException) as exc_info:
            await get_routes(
                fecha_ruta=None,
                estado_ruta=None,
                port=mock_delivery_port,
                user=mock_web_user,
            )

        assert exc_info.value.status_code == 503

    @pytest.mark.asyncio
    async def test_get_routes_http_error(self, mock_delivery_port, mock_web_user):
        """Test get_routes with HTTP error."""
        mock_delivery_port.list_routes = AsyncMock(
            side_effect=MicroserviceHTTPError(
                service_name="Delivery",
                status_code=400,
                response_text="Bad request",
            )
        )

        with pytest.raises(HTTPException) as exc_info:
            await get_routes(
                fecha_ruta=None,
                estado_ruta=None,
                port=mock_delivery_port,
                user=mock_web_user,
            )

        assert exc_info.value.status_code == 400


# Route Detail Endpoint Tests


class TestGetRoute:
    """Test get_route endpoint."""

    @pytest.mark.asyncio
    async def test_get_route_success(self, mock_delivery_port, mock_web_user):
        """Test retrieving a specific route with details."""
        route_id = uuid4()
        vehicle_id = uuid4()

        shipment_1 = ShipmentInRoute(
            id=uuid4(),
            order_id=uuid4(),
            shipment_status="pendiente",
            delivery_sequence=1,
        )
        shipment_2 = ShipmentInRoute(
            id=uuid4(),
            order_id=uuid4(),
            shipment_status="en_ruta",
            delivery_sequence=2,
        )

        vehicle = VehicleInRoute(
            id=vehicle_id,
            placa="ABC-1234",
            driver_name="John Doe",
            driver_phone="+1234567890",
        )

        response = RouteDetailResponse(
            id=route_id,
            fecha_ruta=date(2025, 1, 15),
            estado_ruta="en_progreso",
            vehicle_id=vehicle_id,
            vehicle=vehicle,
            shipments=[shipment_1, shipment_2],
        )

        mock_delivery_port.get_route = AsyncMock(return_value=response)

        result = await get_route(route_id, mock_delivery_port, mock_web_user)

        assert result.id == route_id
        assert result.estado_ruta == "en_progreso"
        assert len(result.shipments) == 2
        assert result.vehicle is not None
        assert result.vehicle.placa == "ABC-1234"
        mock_delivery_port.get_route.assert_called_once_with(route_id)

    @pytest.mark.asyncio
    async def test_get_route_validation_error(self, mock_delivery_port, mock_web_user):
        """Test get_route with validation error."""
        route_id = uuid4()

        mock_delivery_port.get_route = AsyncMock(
            side_effect=MicroserviceValidationError(
                service_name="Delivery",
                message="Invalid UUID format",
                status_code=400,
                details={"field": "route_id", "message": "Invalid UUID format"},
            )
        )

        with pytest.raises(HTTPException) as exc_info:
            await get_route(route_id, mock_delivery_port, mock_web_user)

        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_get_route_not_found(self, mock_delivery_port, mock_web_user):
        """Test retrieving non-existent route."""
        route_id = uuid4()

        mock_delivery_port.get_route = AsyncMock(
            side_effect=MicroserviceHTTPError(
                service_name="Delivery",
                status_code=404,
                response_text="Route not found",
            )
        )

        with pytest.raises(HTTPException) as exc_info:
            await get_route(route_id, mock_delivery_port, mock_web_user)

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_get_route_connection_error(self, mock_delivery_port, mock_web_user):
        """Test get_route with connection error."""
        route_id = uuid4()

        mock_delivery_port.get_route = AsyncMock(
            side_effect=MicroserviceConnectionError(
                service_name="Delivery",
                original_error="Service unavailable",
            )
        )

        with pytest.raises(HTTPException) as exc_info:
            await get_route(route_id, mock_delivery_port, mock_web_user)

        assert exc_info.value.status_code == 503


# Route Status Update Endpoint Tests


class TestUpdateRouteStatus:
    """Test update_route_status endpoint."""

    @pytest.mark.asyncio
    async def test_update_route_status_success(self, mock_delivery_port, mock_web_user):
        """Test successful route status update."""
        route_id = uuid4()
        vehicle_id = uuid4()

        request_data = RouteStatusUpdateRequest(estado_ruta="completada")

        response = RouteResponse(
            id=route_id,
            fecha_ruta=date(2025, 1, 15),
            estado_ruta="completada",
            vehicle_id=vehicle_id,
        )

        mock_delivery_port.update_route_status = AsyncMock(return_value=response)

        result = await update_route_status(
            route_id, request_data, mock_delivery_port, mock_web_user
        )

        assert result.id == route_id
        assert result.estado_ruta == "completada"
        mock_delivery_port.update_route_status.assert_called_once_with(
            route_id, "completada"
        )

    @pytest.mark.asyncio
    async def test_update_route_status_invalid_status(
        self, mock_delivery_port, mock_web_user
    ):
        """Test route status update with invalid status."""
        route_id = uuid4()
        request_data = RouteStatusUpdateRequest(estado_ruta="invalid_status")

        mock_delivery_port.update_route_status = AsyncMock(
            side_effect=MicroserviceValidationError(
                service_name="Delivery",
                message="Invalid status value",
                status_code=400,
            )
        )

        with pytest.raises(HTTPException) as exc_info:
            await update_route_status(
                route_id, request_data, mock_delivery_port, mock_web_user
            )

        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_update_route_status_not_found(self, mock_delivery_port, mock_web_user):
        """Test updating non-existent route."""
        route_id = uuid4()
        request_data = RouteStatusUpdateRequest(estado_ruta="completada")

        mock_delivery_port.update_route_status = AsyncMock(
            side_effect=MicroserviceHTTPError(
                service_name="Delivery",
                status_code=404,
                response_text="Route not found",
            )
        )

        with pytest.raises(HTTPException) as exc_info:
            await update_route_status(
                route_id, request_data, mock_delivery_port, mock_web_user
            )

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_update_route_status_connection_error(
        self, mock_delivery_port, mock_web_user
    ):
        """Test update_route_status with connection error."""
        route_id = uuid4()
        request_data = RouteStatusUpdateRequest(estado_ruta="completada")

        mock_delivery_port.update_route_status = AsyncMock(
            side_effect=MicroserviceConnectionError(
                service_name="Delivery",
                original_error="Service unavailable",
            )
        )

        with pytest.raises(HTTPException) as exc_info:
            await update_route_status(
                route_id, request_data, mock_delivery_port, mock_web_user
            )

        assert exc_info.value.status_code == 503


# Vehicles List Endpoint Tests


class TestGetVehicles:
    """Test get_vehicles endpoint."""

    @pytest.mark.asyncio
    async def test_get_vehicles_success(self, mock_delivery_port, mock_web_user):
        """Test retrieving all vehicles."""
        vehicle_1_id = uuid4()
        vehicle_2_id = uuid4()

        response = VehiclesListResponse(
            items=[
                VehicleResponse(
                    id=vehicle_1_id,
                    placa="ABC-1234",
                    driver_name="John Doe",
                    driver_phone="+1234567890",
                    is_active=True,
                ),
                VehicleResponse(
                    id=vehicle_2_id,
                    placa="XYZ-5678",
                    driver_name="Jane Smith",
                    driver_phone="+0987654321",
                    is_active=True,
                ),
            ],
            total=2,
        )

        mock_delivery_port.list_vehicles = AsyncMock(return_value=response)

        result = await get_vehicles(mock_delivery_port, mock_web_user)

        assert result.total == 2
        assert len(result.items) == 2
        assert result.items[0].placa == "ABC-1234"
        assert result.items[1].placa == "XYZ-5678"
        mock_delivery_port.list_vehicles.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_vehicles_empty_list(self, mock_delivery_port, mock_web_user):
        """Test retrieving vehicles when none exist."""
        response = VehiclesListResponse(items=[], total=0)

        mock_delivery_port.list_vehicles = AsyncMock(return_value=response)

        result = await get_vehicles(mock_delivery_port, mock_web_user)

        assert result.total == 0
        assert len(result.items) == 0

    @pytest.mark.asyncio
    async def test_get_vehicles_validation_error(self, mock_delivery_port, mock_web_user):
        """Test get_vehicles with validation error."""
        mock_delivery_port.list_vehicles = AsyncMock(
            side_effect=MicroserviceValidationError(
                service_name="Delivery",
                message="Invalid request parameters",
                status_code=400,
                details={"message": "Invalid request parameters"},
            )
        )

        with pytest.raises(HTTPException) as exc_info:
            await get_vehicles(mock_delivery_port, mock_web_user)

        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_get_vehicles_connection_error(self, mock_delivery_port, mock_web_user):
        """Test get_vehicles with connection error."""
        mock_delivery_port.list_vehicles = AsyncMock(
            side_effect=MicroserviceConnectionError(
                service_name="Delivery",
                original_error="Connection timeout",
            )
        )

        with pytest.raises(HTTPException) as exc_info:
            await get_vehicles(mock_delivery_port, mock_web_user)

        assert exc_info.value.status_code == 503

    @pytest.mark.asyncio
    async def test_get_vehicles_http_error(self, mock_delivery_port, mock_web_user):
        """Test get_vehicles with HTTP error."""
        mock_delivery_port.list_vehicles = AsyncMock(
            side_effect=MicroserviceHTTPError(
                service_name="Delivery",
                status_code=500,
                response_text="Internal server error",
            )
        )

        with pytest.raises(HTTPException) as exc_info:
            await get_vehicles(mock_delivery_port, mock_web_user)

        assert exc_info.value.status_code == 500


# Vehicle Creation Endpoint Tests


class TestCreateVehicle:
    """Test create_vehicle endpoint."""

    @pytest.mark.asyncio
    async def test_create_vehicle_success(self, mock_delivery_port, mock_web_user):
        """Test successful vehicle creation."""
        vehicle_id = uuid4()

        request_data = VehicleCreateRequest(
            placa="ABC-1234",
            driver_name="John Doe",
            driver_phone="+1234567890",
        )

        response = VehicleResponse(
            id=vehicle_id,
            placa="ABC-1234",
            driver_name="John Doe",
            driver_phone="+1234567890",
            is_active=True,
        )

        mock_delivery_port.create_vehicle = AsyncMock(return_value=response)

        result = await create_vehicle(request_data, mock_delivery_port, mock_web_user)

        assert result.id == vehicle_id
        assert result.placa == "ABC-1234"
        assert result.driver_name == "John Doe"
        assert result.is_active is True
        mock_delivery_port.create_vehicle.assert_called_once_with(request_data)

    @pytest.mark.asyncio
    async def test_create_vehicle_without_phone(self, mock_delivery_port, mock_web_user):
        """Test vehicle creation without phone number."""
        vehicle_id = uuid4()

        request_data = VehicleCreateRequest(
            placa="XYZ-5678",
            driver_name="Jane Smith",
        )

        response = VehicleResponse(
            id=vehicle_id,
            placa="XYZ-5678",
            driver_name="Jane Smith",
            is_active=True,
        )

        mock_delivery_port.create_vehicle = AsyncMock(return_value=response)

        result = await create_vehicle(request_data, mock_delivery_port, mock_web_user)

        assert result.placa == "XYZ-5678"
        assert result.driver_phone is None

    @pytest.mark.asyncio
    async def test_create_vehicle_validation_error(self, mock_delivery_port, mock_web_user):
        """Test vehicle creation with validation error."""
        request_data = VehicleCreateRequest(
            placa="ABC-1234",
            driver_name="John Doe",
        )

        mock_delivery_port.create_vehicle = AsyncMock(
            side_effect=MicroserviceValidationError(
                service_name="Delivery",
                message="Invalid vehicle data",
                status_code=400,
            )
        )

        with pytest.raises(HTTPException) as exc_info:
            await create_vehicle(request_data, mock_delivery_port, mock_web_user)

        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_create_vehicle_connection_error(self, mock_delivery_port, mock_web_user):
        """Test create_vehicle with connection error."""
        request_data = VehicleCreateRequest(
            placa="ABC-1234",
            driver_name="John Doe",
        )

        mock_delivery_port.create_vehicle = AsyncMock(
            side_effect=MicroserviceConnectionError(
                service_name="Delivery",
                original_error="Service unavailable",
            )
        )

        with pytest.raises(HTTPException) as exc_info:
            await create_vehicle(request_data, mock_delivery_port, mock_web_user)

        assert exc_info.value.status_code == 503

    @pytest.mark.asyncio
    async def test_create_vehicle_http_error(self, mock_delivery_port, mock_web_user):
        """Test create_vehicle with HTTP error (e.g., duplicate plate)."""
        request_data = VehicleCreateRequest(
            placa="ABC-1234",
            driver_name="John Doe",
        )

        mock_delivery_port.create_vehicle = AsyncMock(
            side_effect=MicroserviceHTTPError(
                service_name="Delivery",
                status_code=409,
                response_text="Vehicle with this plate already exists",
            )
        )

        with pytest.raises(HTTPException) as exc_info:
            await create_vehicle(request_data, mock_delivery_port, mock_web_user)

        assert exc_info.value.status_code == 409


# Vehicle Update Endpoint Tests


class TestUpdateVehicle:
    """Test update_vehicle endpoint."""

    @pytest.mark.asyncio
    async def test_update_vehicle_success_full_update(
        self, mock_delivery_port, mock_web_user
    ):
        """Test successful vehicle update with all fields."""
        vehicle_id = uuid4()

        request_data = VehicleUpdateRequest(
            driver_name="Jane Smith",
            driver_phone="+0987654321",
        )

        response = VehicleResponse(
            id=vehicle_id,
            placa="ABC-1234",
            driver_name="Jane Smith",
            driver_phone="+0987654321",
            is_active=True,
        )

        mock_delivery_port.update_vehicle = AsyncMock(return_value=response)

        result = await update_vehicle(vehicle_id, request_data, mock_delivery_port, mock_web_user)

        assert result.driver_name == "Jane Smith"
        assert result.driver_phone == "+0987654321"
        mock_delivery_port.update_vehicle.assert_called_once_with(vehicle_id, request_data)

    @pytest.mark.asyncio
    async def test_update_vehicle_partial_update(self, mock_delivery_port, mock_web_user):
        """Test vehicle update with only driver name."""
        vehicle_id = uuid4()

        request_data = VehicleUpdateRequest(
            driver_name="John Smith",
        )

        response = VehicleResponse(
            id=vehicle_id,
            placa="ABC-1234",
            driver_name="John Smith",
            driver_phone="+1234567890",
            is_active=True,
        )

        mock_delivery_port.update_vehicle = AsyncMock(return_value=response)

        result = await update_vehicle(vehicle_id, request_data, mock_delivery_port, mock_web_user)

        assert result.driver_name == "John Smith"

    @pytest.mark.asyncio
    async def test_update_vehicle_not_found(self, mock_delivery_port, mock_web_user):
        """Test updating non-existent vehicle."""
        vehicle_id = uuid4()

        request_data = VehicleUpdateRequest(
            driver_name="Jane Smith",
        )

        mock_delivery_port.update_vehicle = AsyncMock(
            side_effect=MicroserviceHTTPError(
                service_name="Delivery",
                status_code=404,
                response_text="Vehicle not found",
            )
        )

        with pytest.raises(HTTPException) as exc_info:
            await update_vehicle(vehicle_id, request_data, mock_delivery_port, mock_web_user)

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_update_vehicle_validation_error(self, mock_delivery_port, mock_web_user):
        """Test vehicle update with validation error."""
        vehicle_id = uuid4()

        request_data = VehicleUpdateRequest(
            driver_name="",  # Invalid empty name
        )

        mock_delivery_port.update_vehicle = AsyncMock(
            side_effect=MicroserviceValidationError(
                service_name="Delivery",
                message="Invalid vehicle data",
                status_code=400,
            )
        )

        with pytest.raises(HTTPException) as exc_info:
            await update_vehicle(vehicle_id, request_data, mock_delivery_port, mock_web_user)

        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_update_vehicle_connection_error(self, mock_delivery_port, mock_web_user):
        """Test update_vehicle with connection error."""
        vehicle_id = uuid4()

        request_data = VehicleUpdateRequest(
            driver_name="Jane Smith",
        )

        mock_delivery_port.update_vehicle = AsyncMock(
            side_effect=MicroserviceConnectionError(
                service_name="Delivery",
                original_error="Connection timeout",
            )
        )

        with pytest.raises(HTTPException) as exc_info:
            await update_vehicle(vehicle_id, request_data, mock_delivery_port, mock_web_user)

        assert exc_info.value.status_code == 503


# Vehicle Deletion Endpoint Tests


class TestDeleteVehicle:
    """Test delete_vehicle endpoint."""

    @pytest.mark.asyncio
    async def test_delete_vehicle_success(self, mock_delivery_port, mock_web_user):
        """Test successful vehicle deletion."""
        vehicle_id = uuid4()

        mock_delivery_port.delete_vehicle = AsyncMock(return_value=None)

        result = await delete_vehicle(vehicle_id, mock_delivery_port, mock_web_user)

        assert result.status_code == 204
        mock_delivery_port.delete_vehicle.assert_called_once_with(vehicle_id)

    @pytest.mark.asyncio
    async def test_delete_vehicle_not_found(self, mock_delivery_port, mock_web_user):
        """Test deleting non-existent vehicle."""
        vehicle_id = uuid4()

        mock_delivery_port.delete_vehicle = AsyncMock(
            side_effect=MicroserviceHTTPError(
                service_name="Delivery",
                status_code=404,
                response_text="Vehicle not found",
            )
        )

        with pytest.raises(HTTPException) as exc_info:
            await delete_vehicle(vehicle_id, mock_delivery_port, mock_web_user)

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_vehicle_validation_error(self, mock_delivery_port, mock_web_user):
        """Test delete_vehicle with validation error."""
        vehicle_id = uuid4()

        mock_delivery_port.delete_vehicle = AsyncMock(
            side_effect=MicroserviceValidationError(
                service_name="Delivery",
                message="Cannot delete vehicle with active routes",
                status_code=400,
            )
        )

        with pytest.raises(HTTPException) as exc_info:
            await delete_vehicle(vehicle_id, mock_delivery_port, mock_web_user)

        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_delete_vehicle_connection_error(self, mock_delivery_port, mock_web_user):
        """Test delete_vehicle with connection error."""
        vehicle_id = uuid4()

        mock_delivery_port.delete_vehicle = AsyncMock(
            side_effect=MicroserviceConnectionError(
                service_name="Delivery",
                original_error="Service unavailable",
            )
        )

        with pytest.raises(HTTPException) as exc_info:
            await delete_vehicle(vehicle_id, mock_delivery_port, mock_web_user)

        assert exc_info.value.status_code == 503


# Shipment Status Update Endpoint Tests


class TestUpdateShipmentStatus:
    """Test update_shipment_status endpoint."""

    @pytest.mark.asyncio
    async def test_update_shipment_status_success(self, mock_delivery_port, mock_web_user):
        """Test successful shipment status update."""
        order_id = uuid4()

        request_data = ShipmentStatusUpdateRequest(shipment_status="entregado")

        response = ShipmentResponse(
            id=uuid4(),
            order_id=order_id,
            route_id=uuid4(),
            shipment_status="entregado",
            delivery_sequence=1,
            fecha_entrega_estimada=date(2025, 1, 15),
            updated_at=datetime.now(),
        )

        mock_delivery_port.update_shipment_status = AsyncMock(return_value=response)

        result = await update_shipment_status(
            order_id, request_data, mock_delivery_port, mock_web_user
        )

        assert result.shipment_status == "entregado"
        assert result.order_id == order_id
        mock_delivery_port.update_shipment_status.assert_called_once_with(
            order_id, "entregado"
        )

    @pytest.mark.asyncio
    async def test_update_shipment_status_in_route(self, mock_delivery_port, mock_web_user):
        """Test updating shipment to in_route status."""
        order_id = uuid4()

        request_data = ShipmentStatusUpdateRequest(shipment_status="en_ruta")

        response = ShipmentResponse(
            id=uuid4(),
            order_id=order_id,
            shipment_status="en_ruta",
        )

        mock_delivery_port.update_shipment_status = AsyncMock(return_value=response)

        result = await update_shipment_status(
            order_id, request_data, mock_delivery_port, mock_web_user
        )

        assert result.shipment_status == "en_ruta"

    @pytest.mark.asyncio
    async def test_update_shipment_status_invalid(self, mock_delivery_port, mock_web_user):
        """Test shipment status update with invalid status."""
        order_id = uuid4()

        request_data = ShipmentStatusUpdateRequest(shipment_status="invalid_status")

        mock_delivery_port.update_shipment_status = AsyncMock(
            side_effect=MicroserviceValidationError(
                service_name="Delivery",
                message="Invalid shipment status",
                status_code=400,
            )
        )

        with pytest.raises(HTTPException) as exc_info:
            await update_shipment_status(
                order_id, request_data, mock_delivery_port, mock_web_user
            )

        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_update_shipment_status_not_found(self, mock_delivery_port, mock_web_user):
        """Test updating non-existent shipment."""
        order_id = uuid4()

        request_data = ShipmentStatusUpdateRequest(shipment_status="entregado")

        mock_delivery_port.update_shipment_status = AsyncMock(
            side_effect=MicroserviceHTTPError(
                service_name="Delivery",
                status_code=404,
                response_text="Shipment not found",
            )
        )

        with pytest.raises(HTTPException) as exc_info:
            await update_shipment_status(
                order_id, request_data, mock_delivery_port, mock_web_user
            )

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_update_shipment_status_connection_error(
        self, mock_delivery_port, mock_web_user
    ):
        """Test update_shipment_status with connection error."""
        order_id = uuid4()

        request_data = ShipmentStatusUpdateRequest(shipment_status="entregado")

        mock_delivery_port.update_shipment_status = AsyncMock(
            side_effect=MicroserviceConnectionError(
                service_name="Delivery",
                original_error="Service unavailable",
            )
        )

        with pytest.raises(HTTPException) as exc_info:
            await update_shipment_status(
                order_id, request_data, mock_delivery_port, mock_web_user
            )

        assert exc_info.value.status_code == 503
