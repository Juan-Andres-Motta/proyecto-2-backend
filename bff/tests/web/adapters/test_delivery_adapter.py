"""Unit tests for DeliveryAdapter.

Tests OUR logic:
- Calling correct HTTP endpoints
- Passing correct data to HTTP client
- Response parsing to Pydantic models
"""

from datetime import date, datetime
from unittest.mock import AsyncMock, Mock
from uuid import UUID, uuid4

import pytest

from common.http_client import HttpClient
from web.adapters.delivery_adapter import DeliveryAdapter
from web.schemas.delivery_schemas import (
    RouteDetailResponse,
    RouteGenerationRequest,
    RouteGenerationResponse,
    RouteResponse,
    RoutesListResponse,
    ShipmentInRoute,
    ShipmentResponse,
    VehicleCreateRequest,
    VehicleInRoute,
    VehicleResponse,
    VehiclesListResponse,
    VehicleUpdateRequest,
)


@pytest.fixture
def mock_http_client():
    """Create a mock HTTP client."""
    return Mock(spec=HttpClient)


@pytest.fixture
def delivery_adapter(mock_http_client):
    """Create a delivery adapter with mock HTTP client."""
    return DeliveryAdapter(mock_http_client)


# Route Generation Tests


class TestGenerateRoutes:
    """Test generate_routes calls correct endpoint."""

    @pytest.mark.asyncio
    async def test_calls_correct_endpoint(self, delivery_adapter, mock_http_client):
        """Test that POST /delivery/routes/generate is called."""
        vehicle_id_1 = uuid4()
        vehicle_id_2 = uuid4()

        request_data = RouteGenerationRequest(
            fecha_entrega_estimada=date(2025, 1, 15),
            vehicle_ids=[vehicle_id_1, vehicle_id_2],
        )

        response_data = {
            "message": "Route generation job accepted",
            "fecha_entrega_estimada": date(2025, 1, 15),
            "vehicle_count": 2,
        }

        mock_http_client.post = AsyncMock(return_value=response_data)

        result = await delivery_adapter.generate_routes(request_data)

        mock_http_client.post.assert_called_once()
        call_args = mock_http_client.post.call_args
        assert call_args.args[0] == "/delivery/routes/generate"
        assert "json" in call_args.kwargs
        assert isinstance(result, RouteGenerationResponse)
        assert result.vehicle_count == 2

    @pytest.mark.asyncio
    async def test_request_data_serialization(self, delivery_adapter, mock_http_client):
        """Test that request data is properly serialized."""
        vehicle_id = uuid4()

        request_data = RouteGenerationRequest(
            fecha_entrega_estimada=date(2025, 1, 20),
            vehicle_ids=[vehicle_id],
        )

        mock_http_client.post = AsyncMock(
            return_value={
                "message": "Job accepted",
                "fecha_entrega_estimada": date(2025, 1, 20),
                "vehicle_count": 1,
            }
        )

        await delivery_adapter.generate_routes(request_data)

        call_kwargs = mock_http_client.post.call_args.kwargs
        assert "json" in call_kwargs
        json_data = call_kwargs["json"]
        assert str(json_data["vehicle_ids"][0]) == str(vehicle_id)


# Routes List Tests


class TestListRoutes:
    """Test list_routes calls correct endpoint."""

    @pytest.mark.asyncio
    async def test_calls_correct_endpoint_no_filters(
        self, delivery_adapter, mock_http_client
    ):
        """Test that GET /delivery/routes is called without filters."""
        route_id = uuid4()
        vehicle_id = uuid4()

        response_data = {
            "items": [
                {
                    "id": str(route_id),
                    "fecha_ruta": date(2025, 1, 15),
                    "estado_ruta": "pendiente",
                    "vehicle_id": str(vehicle_id),
                }
            ],
            "total": 1,
        }

        mock_http_client.get = AsyncMock(return_value=response_data)

        result = await delivery_adapter.list_routes()

        mock_http_client.get.assert_called_once()
        call_args = mock_http_client.get.call_args
        assert call_args.args[0] == "/delivery/routes"
        # When no filters, params should be None or empty
        assert call_args.kwargs.get("params") is None
        assert isinstance(result, RoutesListResponse)
        assert result.total == 1

    @pytest.mark.asyncio
    async def test_calls_correct_endpoint_with_date_filter(
        self, delivery_adapter, mock_http_client
    ):
        """Test that GET /delivery/routes is called with date filter."""
        filter_date = date(2025, 1, 15)
        route_id = uuid4()
        vehicle_id = uuid4()

        response_data = {
            "items": [
                {
                    "id": str(route_id),
                    "fecha_ruta": filter_date,
                    "estado_ruta": "en_progreso",
                    "vehicle_id": str(vehicle_id),
                }
            ],
            "total": 1,
        }

        mock_http_client.get = AsyncMock(return_value=response_data)

        result = await delivery_adapter.list_routes(fecha_ruta=filter_date)

        mock_http_client.get.assert_called_once()
        call_args = mock_http_client.get.call_args
        assert call_args.args[0] == "/delivery/routes"
        assert "params" in call_args.kwargs
        assert call_args.kwargs["params"]["fecha_ruta"] == filter_date.isoformat()
        assert result.total == 1

    @pytest.mark.asyncio
    async def test_calls_correct_endpoint_with_status_filter(
        self, delivery_adapter, mock_http_client
    ):
        """Test that GET /delivery/routes is called with status filter."""
        route_id = uuid4()
        vehicle_id = uuid4()

        response_data = {
            "items": [
                {
                    "id": str(route_id),
                    "fecha_ruta": date(2025, 1, 15),
                    "estado_ruta": "completada",
                    "vehicle_id": str(vehicle_id),
                }
            ],
            "total": 1,
        }

        mock_http_client.get = AsyncMock(return_value=response_data)

        result = await delivery_adapter.list_routes(estado_ruta="completada")

        mock_http_client.get.assert_called_once()
        call_args = mock_http_client.get.call_args
        assert call_args.kwargs["params"]["estado_ruta"] == "completada"
        assert result.items[0].estado_ruta == "completada"

    @pytest.mark.asyncio
    async def test_calls_correct_endpoint_with_both_filters(
        self, delivery_adapter, mock_http_client
    ):
        """Test that GET /delivery/routes is called with both filters."""
        filter_date = date(2025, 1, 15)
        route_id = uuid4()
        vehicle_id = uuid4()

        response_data = {
            "items": [
                {
                    "id": str(route_id),
                    "fecha_ruta": filter_date,
                    "estado_ruta": "completada",
                    "vehicle_id": str(vehicle_id),
                }
            ],
            "total": 1,
        }

        mock_http_client.get = AsyncMock(return_value=response_data)

        result = await delivery_adapter.list_routes(
            fecha_ruta=filter_date, estado_ruta="completada"
        )

        call_args = mock_http_client.get.call_args
        params = call_args.kwargs["params"]
        assert params["fecha_ruta"] == filter_date.isoformat()
        assert params["estado_ruta"] == "completada"

    @pytest.mark.asyncio
    async def test_returns_empty_list(self, delivery_adapter, mock_http_client):
        """Test that empty list is properly parsed."""
        response_data = {"items": [], "total": 0}

        mock_http_client.get = AsyncMock(return_value=response_data)

        result = await delivery_adapter.list_routes()

        assert isinstance(result, RoutesListResponse)
        assert result.total == 0
        assert len(result.items) == 0


# Get Route Tests


class TestGetRoute:
    """Test get_route calls correct endpoint."""

    @pytest.mark.asyncio
    async def test_calls_correct_endpoint(self, delivery_adapter, mock_http_client):
        """Test that GET /delivery/routes/{id} is called."""
        route_id = uuid4()
        vehicle_id = uuid4()
        shipment_id = uuid4()
        order_id = uuid4()

        response_data = {
            "id": str(route_id),
            "fecha_ruta": date(2025, 1, 15),
            "estado_ruta": "en_progreso",
            "vehicle_id": str(vehicle_id),
            "vehicle": {
                "id": str(vehicle_id),
                "placa": "ABC-1234",
                "driver_name": "John Doe",
                "driver_phone": "+1234567890",
            },
            "shipments": [
                {
                    "id": str(shipment_id),
                    "order_id": str(order_id),
                    "shipment_status": "en_ruta",
                    "delivery_sequence": 1,
                }
            ],
        }

        mock_http_client.get = AsyncMock(return_value=response_data)

        result = await delivery_adapter.get_route(route_id)

        mock_http_client.get.assert_called_once()
        call_args = mock_http_client.get.call_args
        assert call_args.args[0] == f"/delivery/routes/{route_id}"
        assert isinstance(result, RouteDetailResponse)
        assert result.id == route_id
        assert result.estado_ruta == "en_progreso"
        assert len(result.shipments) == 1
        assert result.vehicle is not None
        assert result.vehicle.placa == "ABC-1234"

    @pytest.mark.asyncio
    async def test_parses_route_with_multiple_shipments(
        self, delivery_adapter, mock_http_client
    ):
        """Test parsing route with multiple shipments."""
        route_id = uuid4()
        vehicle_id = uuid4()

        response_data = {
            "id": str(route_id),
            "fecha_ruta": date(2025, 1, 15),
            "estado_ruta": "en_progreso",
            "vehicle_id": str(vehicle_id),
            "shipments": [
                {
                    "id": str(uuid4()),
                    "order_id": str(uuid4()),
                    "shipment_status": "pendiente",
                    "delivery_sequence": 1,
                },
                {
                    "id": str(uuid4()),
                    "order_id": str(uuid4()),
                    "shipment_status": "en_ruta",
                    "delivery_sequence": 2,
                },
                {
                    "id": str(uuid4()),
                    "order_id": str(uuid4()),
                    "shipment_status": "entregado",
                    "delivery_sequence": 3,
                },
            ],
        }

        mock_http_client.get = AsyncMock(return_value=response_data)

        result = await delivery_adapter.get_route(route_id)

        assert len(result.shipments) == 3
        assert result.shipments[0].delivery_sequence == 1
        assert result.shipments[2].shipment_status == "entregado"


# Update Route Status Tests


class TestUpdateRouteStatus:
    """Test update_route_status calls correct endpoint."""

    @pytest.mark.asyncio
    async def test_calls_correct_endpoint(self, delivery_adapter, mock_http_client):
        """Test that PATCH /delivery/routes/{id}/status is called."""
        route_id = uuid4()
        vehicle_id = uuid4()

        response_data = {
            "id": str(route_id),
            "fecha_ruta": date(2025, 1, 15),
            "estado_ruta": "completada",
            "vehicle_id": str(vehicle_id),
        }

        mock_http_client.patch = AsyncMock(return_value=response_data)

        result = await delivery_adapter.update_route_status(route_id, "completada")

        mock_http_client.patch.assert_called_once()
        call_args = mock_http_client.patch.call_args
        assert call_args.args[0] == f"/delivery/routes/{route_id}/status"
        assert "json" in call_args.kwargs
        assert call_args.kwargs["json"]["estado_ruta"] == "completada"
        assert isinstance(result, RouteResponse)
        assert result.estado_ruta == "completada"

    @pytest.mark.asyncio
    async def test_sends_correct_status_payload(self, delivery_adapter, mock_http_client):
        """Test that the status is properly sent in payload."""
        route_id = uuid4()

        mock_http_client.patch = AsyncMock(
            return_value={
                "id": str(route_id),
                "fecha_ruta": date(2025, 1, 15),
                "estado_ruta": "cancelada",
                "vehicle_id": str(uuid4()),
            }
        )

        await delivery_adapter.update_route_status(route_id, "cancelada")

        call_kwargs = mock_http_client.patch.call_args.kwargs
        assert call_kwargs["json"]["estado_ruta"] == "cancelada"


# List Vehicles Tests


class TestListVehicles:
    """Test list_vehicles calls correct endpoint."""

    @pytest.mark.asyncio
    async def test_calls_correct_endpoint(self, delivery_adapter, mock_http_client):
        """Test that GET /delivery/vehicles is called."""
        vehicle_id_1 = uuid4()
        vehicle_id_2 = uuid4()

        response_data = {
            "items": [
                {
                    "id": str(vehicle_id_1),
                    "placa": "ABC-1234",
                    "driver_name": "John Doe",
                    "driver_phone": "+1234567890",
                    "is_active": True,
                },
                {
                    "id": str(vehicle_id_2),
                    "placa": "XYZ-5678",
                    "driver_name": "Jane Smith",
                    "driver_phone": "+0987654321",
                    "is_active": True,
                },
            ],
            "total": 2,
        }

        mock_http_client.get = AsyncMock(return_value=response_data)

        result = await delivery_adapter.list_vehicles()

        mock_http_client.get.assert_called_once()
        call_args = mock_http_client.get.call_args
        assert call_args.args[0] == "/delivery/vehicles"
        assert isinstance(result, VehiclesListResponse)
        assert result.total == 2
        assert len(result.items) == 2

    @pytest.mark.asyncio
    async def test_returns_empty_list(self, delivery_adapter, mock_http_client):
        """Test that empty vehicle list is properly parsed."""
        response_data = {"items": [], "total": 0}

        mock_http_client.get = AsyncMock(return_value=response_data)

        result = await delivery_adapter.list_vehicles()

        assert isinstance(result, VehiclesListResponse)
        assert result.total == 0
        assert len(result.items) == 0

    @pytest.mark.asyncio
    async def test_vehicle_without_phone(self, delivery_adapter, mock_http_client):
        """Test parsing vehicle without phone number."""
        vehicle_id = uuid4()

        response_data = {
            "items": [
                {
                    "id": str(vehicle_id),
                    "placa": "ABC-1234",
                    "driver_name": "John Doe",
                    "is_active": True,
                }
            ],
            "total": 1,
        }

        mock_http_client.get = AsyncMock(return_value=response_data)

        result = await delivery_adapter.list_vehicles()

        assert result.items[0].driver_phone is None
        assert result.items[0].placa == "ABC-1234"


# Create Vehicle Tests


class TestCreateVehicle:
    """Test create_vehicle calls correct endpoint."""

    @pytest.mark.asyncio
    async def test_calls_correct_endpoint(self, delivery_adapter, mock_http_client):
        """Test that POST /delivery/vehicles is called."""
        vehicle_id = uuid4()

        request_data = VehicleCreateRequest(
            placa="ABC-1234",
            driver_name="John Doe",
            driver_phone="+1234567890",
        )

        response_data = {
            "id": str(vehicle_id),
            "placa": "ABC-1234",
            "driver_name": "John Doe",
            "driver_phone": "+1234567890",
            "is_active": True,
        }

        mock_http_client.post = AsyncMock(return_value=response_data)

        result = await delivery_adapter.create_vehicle(request_data)

        mock_http_client.post.assert_called_once()
        call_args = mock_http_client.post.call_args
        assert call_args.args[0] == "/delivery/vehicles"
        assert "json" in call_args.kwargs
        assert isinstance(result, VehicleResponse)
        assert result.placa == "ABC-1234"
        assert result.id == vehicle_id

    @pytest.mark.asyncio
    async def test_request_data_serialization(self, delivery_adapter, mock_http_client):
        """Test that request data is properly serialized."""
        vehicle_id = uuid4()

        request_data = VehicleCreateRequest(
            placa="XYZ-5678",
            driver_name="Jane Smith",
            driver_phone="+0987654321",
        )

        mock_http_client.post = AsyncMock(
            return_value={
                "id": str(vehicle_id),
                "placa": "XYZ-5678",
                "driver_name": "Jane Smith",
                "driver_phone": "+0987654321",
                "is_active": True,
            }
        )

        await delivery_adapter.create_vehicle(request_data)

        call_kwargs = mock_http_client.post.call_args.kwargs
        json_data = call_kwargs["json"]
        assert json_data["placa"] == "XYZ-5678"
        assert json_data["driver_name"] == "Jane Smith"
        assert json_data["driver_phone"] == "+0987654321"

    @pytest.mark.asyncio
    async def test_create_vehicle_without_phone(self, delivery_adapter, mock_http_client):
        """Test creating vehicle without phone number."""
        vehicle_id = uuid4()

        request_data = VehicleCreateRequest(
            placa="ABC-1234",
            driver_name="John Doe",
        )

        response_data = {
            "id": str(vehicle_id),
            "placa": "ABC-1234",
            "driver_name": "John Doe",
            "is_active": True,
        }

        mock_http_client.post = AsyncMock(return_value=response_data)

        result = await delivery_adapter.create_vehicle(request_data)

        call_kwargs = mock_http_client.post.call_args.kwargs
        json_data = call_kwargs["json"]
        # Phone may be None or omitted in the JSON
        assert result.driver_phone is None


# Update Vehicle Tests


class TestUpdateVehicle:
    """Test update_vehicle calls correct endpoint."""

    @pytest.mark.asyncio
    async def test_calls_correct_endpoint(self, delivery_adapter, mock_http_client):
        """Test that PATCH /delivery/vehicles/{id} is called."""
        vehicle_id = uuid4()

        request_data = VehicleUpdateRequest(
            driver_name="Jane Smith",
            driver_phone="+0987654321",
        )

        response_data = {
            "id": str(vehicle_id),
            "placa": "ABC-1234",
            "driver_name": "Jane Smith",
            "driver_phone": "+0987654321",
            "is_active": True,
        }

        mock_http_client.patch = AsyncMock(return_value=response_data)

        result = await delivery_adapter.update_vehicle(vehicle_id, request_data)

        mock_http_client.patch.assert_called_once()
        call_args = mock_http_client.patch.call_args
        assert call_args.args[0] == f"/delivery/vehicles/{vehicle_id}"
        assert "json" in call_args.kwargs
        assert isinstance(result, VehicleResponse)
        assert result.driver_name == "Jane Smith"

    @pytest.mark.asyncio
    async def test_sends_only_non_none_fields(self, delivery_adapter, mock_http_client):
        """Test that only non-None fields are sent in update."""
        vehicle_id = uuid4()

        request_data = VehicleUpdateRequest(
            driver_name="John Smith",
            driver_phone=None,
        )

        mock_http_client.patch = AsyncMock(
            return_value={
                "id": str(vehicle_id),
                "placa": "ABC-1234",
                "driver_name": "John Smith",
                "driver_phone": "+1234567890",
                "is_active": True,
            }
        )

        await delivery_adapter.update_vehicle(vehicle_id, request_data)

        call_kwargs = mock_http_client.patch.call_args.kwargs
        json_data = call_kwargs["json"]
        assert "driver_name" in json_data
        assert json_data["driver_name"] == "John Smith"
        # driver_phone should be excluded when None
        assert "driver_phone" not in json_data

    @pytest.mark.asyncio
    async def test_update_only_phone(self, delivery_adapter, mock_http_client):
        """Test updating only phone number."""
        vehicle_id = uuid4()

        request_data = VehicleUpdateRequest(
            driver_name=None,
            driver_phone="+0987654321",
        )

        mock_http_client.patch = AsyncMock(
            return_value={
                "id": str(vehicle_id),
                "placa": "ABC-1234",
                "driver_name": "John Doe",
                "driver_phone": "+0987654321",
                "is_active": True,
            }
        )

        await delivery_adapter.update_vehicle(vehicle_id, request_data)

        call_kwargs = mock_http_client.patch.call_args.kwargs
        json_data = call_kwargs["json"]
        assert "driver_phone" in json_data
        assert "driver_name" not in json_data


# Delete Vehicle Tests


class TestDeleteVehicle:
    """Test delete_vehicle calls correct endpoint."""

    @pytest.mark.asyncio
    async def test_calls_correct_endpoint(self, delivery_adapter, mock_http_client):
        """Test that DELETE /delivery/vehicles/{id} is called."""
        vehicle_id = uuid4()

        mock_http_client.delete = AsyncMock(return_value=None)

        result = await delivery_adapter.delete_vehicle(vehicle_id)

        mock_http_client.delete.assert_called_once()
        call_args = mock_http_client.delete.call_args
        assert call_args.args[0] == f"/delivery/vehicles/{vehicle_id}"
        # delete_vehicle returns None
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_returns_none(self, delivery_adapter, mock_http_client):
        """Test that delete returns None on success."""
        vehicle_id = uuid4()

        mock_http_client.delete = AsyncMock(return_value=None)

        result = await delivery_adapter.delete_vehicle(vehicle_id)

        assert result is None


# Update Shipment Status Tests


class TestUpdateShipmentStatus:
    """Test update_shipment_status calls correct endpoint."""

    @pytest.mark.asyncio
    async def test_calls_correct_endpoint(self, delivery_adapter, mock_http_client):
        """Test that PATCH /delivery/orders/{id}/shipment/status is called."""
        order_id = uuid4()
        shipment_id = uuid4()

        response_data = {
            "id": str(shipment_id),
            "order_id": str(order_id),
            "route_id": str(uuid4()),
            "shipment_status": "entregado",
            "delivery_sequence": 1,
            "fecha_entrega_estimada": date(2025, 1, 15),
        }

        mock_http_client.patch = AsyncMock(return_value=response_data)

        result = await delivery_adapter.update_shipment_status(order_id, "entregado")

        mock_http_client.patch.assert_called_once()
        call_args = mock_http_client.patch.call_args
        assert call_args.args[0] == f"/delivery/orders/{order_id}/shipment/status"
        assert "json" in call_args.kwargs
        assert isinstance(result, ShipmentResponse)
        assert result.shipment_status == "entregado"
        assert result.order_id == order_id

    @pytest.mark.asyncio
    async def test_sends_correct_status_payload(self, delivery_adapter, mock_http_client):
        """Test that the status is properly sent in payload."""
        order_id = uuid4()

        mock_http_client.patch = AsyncMock(
            return_value={
                "id": str(uuid4()),
                "order_id": str(order_id),
                "shipment_status": "en_ruta",
            }
        )

        await delivery_adapter.update_shipment_status(order_id, "en_ruta")

        call_kwargs = mock_http_client.patch.call_args.kwargs
        assert call_kwargs["json"]["shipment_status"] == "en_ruta"

    @pytest.mark.asyncio
    async def test_parses_response_with_optional_fields(
        self, delivery_adapter, mock_http_client
    ):
        """Test parsing response with optional fields."""
        order_id = uuid4()
        shipment_id = uuid4()

        response_data = {
            "id": str(shipment_id),
            "order_id": str(order_id),
            "shipment_status": "fallido",
        }

        mock_http_client.patch = AsyncMock(return_value=response_data)

        result = await delivery_adapter.update_shipment_status(order_id, "fallido")

        assert result.id == shipment_id
        assert result.shipment_status == "fallido"
        assert result.route_id is None
        assert result.delivery_sequence is None

    @pytest.mark.asyncio
    async def test_parses_response_with_all_fields(self, delivery_adapter, mock_http_client):
        """Test parsing response with all fields populated."""
        order_id = uuid4()
        shipment_id = uuid4()
        route_id = uuid4()
        updated_at = datetime(2025, 1, 15, 10, 30, 0)

        response_data = {
            "id": str(shipment_id),
            "order_id": str(order_id),
            "route_id": str(route_id),
            "shipment_status": "entregado",
            "delivery_sequence": 3,
            "fecha_entrega_estimada": date(2025, 1, 15),
            "updated_at": updated_at,
        }

        mock_http_client.patch = AsyncMock(return_value=response_data)

        result = await delivery_adapter.update_shipment_status(order_id, "entregado")

        assert result.id == shipment_id
        assert result.order_id == order_id
        assert result.route_id == route_id
        assert result.shipment_status == "entregado"
        assert result.delivery_sequence == 3
        assert result.fecha_entrega_estimada == date(2025, 1, 15)
