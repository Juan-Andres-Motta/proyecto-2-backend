import pytest
from unittest.mock import AsyncMock
from uuid import uuid4
from datetime import date, datetime
from decimal import Decimal

from src.application.use_cases.get_route import GetRouteUseCase
from src.domain.entities import Route, Vehicle, Shipment
from src.domain.value_objects import RouteStatus, ShipmentStatus
from src.domain.exceptions import EntityNotFoundError


class TestGetRouteUseCase:
    """Test suite for GetRouteUseCase."""

    @pytest.fixture
    def mock_route_repository(self):
        """Create a mock route repository."""
        return AsyncMock()

    @pytest.fixture
    def mock_vehicle_repository(self):
        """Create a mock vehicle repository."""
        return AsyncMock()

    @pytest.fixture
    def use_case(self, mock_route_repository, mock_vehicle_repository):
        """Create a GetRouteUseCase instance with mocked dependencies."""
        return GetRouteUseCase(
            route_repository=mock_route_repository,
            vehicle_repository=mock_vehicle_repository,
        )

    def _create_shipment(self, order_id=None, route_id=None, sequence=1, status=ShipmentStatus.ASSIGNED_TO_ROUTE):
        """Helper to create a shipment for testing."""
        shipment = Shipment(
            id=uuid4(),
            order_id=order_id or uuid4(),
            customer_id=uuid4(),
            direccion_entrega="123 Main St",
            ciudad_entrega="City",
            pais_entrega="Country",
            fecha_pedido=datetime(2024, 1, 14, 10, 0, 0),
            fecha_entrega_estimada=date(2024, 1, 15),
        )
        if route_id:
            shipment.route_id = route_id
            shipment.sequence_in_route = sequence
            shipment.shipment_status = status
        return shipment

    @pytest.mark.asyncio
    async def test_execute_returns_route_details_with_shipments(
        self, use_case, mock_route_repository, mock_vehicle_repository
    ):
        """Test successful retrieval of route with shipments and vehicle info."""
        # Arrange
        vehicle_id = uuid4()
        route_id = uuid4()
        order_id = uuid4()

        shipment = self._create_shipment(order_id=order_id, route_id=route_id, sequence=1)

        route = Route(
            id=route_id,
            vehicle_id=vehicle_id,
            fecha_ruta=date(2024, 1, 15),
            estado_ruta=RouteStatus.PLANEADA,
            duracion_estimada_minutos=120,
            total_distance_km=Decimal("45.5"),
            total_orders=1,
        )
        route.set_shipments([shipment])

        vehicle = Vehicle(
            id=vehicle_id,
            placa="ABC123",
            driver_name="John Doe",
            driver_phone="+1234567890",
        )

        mock_route_repository.find_by_id.return_value = route
        mock_vehicle_repository.find_by_id.return_value = vehicle

        # Act
        result = await use_case.execute(route_id=route_id)

        # Assert
        assert result["id"] == route_id
        assert result["vehicle_id"] == vehicle_id
        assert result["vehicle_plate"] == "ABC123"
        assert result["driver_name"] == "John Doe"
        assert result["driver_phone"] == "+1234567890"
        assert result["fecha_ruta"] == date(2024, 1, 15)
        assert result["estado_ruta"] == "planeada"
        assert result["duracion_estimada_minutos"] == 120
        assert result["total_distance_km"] == 45.5
        assert result["total_orders"] == 1
        assert len(result["shipments"]) == 1

        shipment_data = result["shipments"][0]
        assert shipment_data["id"] == shipment.id
        assert shipment_data["order_id"] == order_id
        assert shipment_data["direccion_entrega"] == "123 Main St"
        assert shipment_data["ciudad_entrega"] == "City"
        assert shipment_data["sequence_in_route"] == 1
        assert shipment_data["shipment_status"] == "assigned_to_route"

        mock_route_repository.find_by_id.assert_called_once_with(route_id)
        mock_vehicle_repository.find_by_id.assert_called_once_with(vehicle_id)

    @pytest.mark.asyncio
    async def test_execute_route_not_found_raises_error(
        self, use_case, mock_route_repository, mock_vehicle_repository
    ):
        """Test that EntityNotFoundError is raised when route not found."""
        # Arrange
        route_id = uuid4()
        mock_route_repository.find_by_id.return_value = None

        # Act & Assert
        with pytest.raises(EntityNotFoundError) as exc_info:
            await use_case.execute(route_id=route_id)

        assert exc_info.value.entity_type == "Route"
        assert exc_info.value.entity_id == str(route_id)
        mock_route_repository.find_by_id.assert_called_once_with(route_id)
        mock_vehicle_repository.find_by_id.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_handles_vehicle_not_found(
        self, use_case, mock_route_repository, mock_vehicle_repository
    ):
        """Test handling when vehicle is not found."""
        # Arrange
        vehicle_id = uuid4()
        route_id = uuid4()

        route = Route(
            id=route_id,
            vehicle_id=vehicle_id,
            fecha_ruta=date(2024, 1, 15),
            estado_ruta=RouteStatus.PLANEADA,
            duracion_estimada_minutos=60,
            total_distance_km=Decimal("20.0"),
            total_orders=0,
        )

        mock_route_repository.find_by_id.return_value = route
        mock_vehicle_repository.find_by_id.return_value = None

        # Act
        result = await use_case.execute(route_id=route_id)

        # Assert
        assert result["vehicle_plate"] is None
        assert result["driver_name"] is None
        assert result["driver_phone"] is None

    @pytest.mark.asyncio
    async def test_execute_multiple_shipments(
        self, use_case, mock_route_repository, mock_vehicle_repository
    ):
        """Test route with multiple shipments."""
        # Arrange
        vehicle_id = uuid4()
        route_id = uuid4()

        shipments = [
            self._create_shipment(route_id=route_id, sequence=1),
            self._create_shipment(route_id=route_id, sequence=2),
            self._create_shipment(route_id=route_id, sequence=3),
        ]

        route = Route(
            id=route_id,
            vehicle_id=vehicle_id,
            fecha_ruta=date(2024, 1, 15),
            estado_ruta=RouteStatus.PLANEADA,
            duracion_estimada_minutos=180,
            total_distance_km=Decimal("75.0"),
            total_orders=3,
        )
        route.set_shipments(shipments)

        vehicle = Vehicle(id=vehicle_id, placa="ABC123", driver_name="John Doe")

        mock_route_repository.find_by_id.return_value = route
        mock_vehicle_repository.find_by_id.return_value = vehicle

        # Act
        result = await use_case.execute(route_id=route_id)

        # Assert
        assert len(result["shipments"]) == 3
        assert result["shipments"][0]["sequence_in_route"] == 1
        assert result["shipments"][1]["sequence_in_route"] == 2
        assert result["shipments"][2]["sequence_in_route"] == 3

    @pytest.mark.asyncio
    async def test_execute_route_with_no_shipments(
        self, use_case, mock_route_repository, mock_vehicle_repository
    ):
        """Test route with no shipments."""
        # Arrange
        vehicle_id = uuid4()
        route_id = uuid4()

        route = Route(
            id=route_id,
            vehicle_id=vehicle_id,
            fecha_ruta=date(2024, 1, 15),
            estado_ruta=RouteStatus.PLANEADA,
            duracion_estimada_minutos=0,
            total_distance_km=Decimal("0.0"),
            total_orders=0,
        )

        vehicle = Vehicle(id=vehicle_id, placa="ABC123", driver_name="John Doe")

        mock_route_repository.find_by_id.return_value = route
        mock_vehicle_repository.find_by_id.return_value = vehicle

        # Act
        result = await use_case.execute(route_id=route_id)

        # Assert
        assert result["shipments"] == []
        assert result["total_orders"] == 0

    @pytest.mark.asyncio
    async def test_execute_converts_decimal_to_float(
        self, use_case, mock_route_repository, mock_vehicle_repository
    ):
        """Test that total_distance_km is converted to float."""
        # Arrange
        vehicle_id = uuid4()
        route_id = uuid4()

        route = Route(
            id=route_id,
            vehicle_id=vehicle_id,
            fecha_ruta=date(2024, 1, 15),
            estado_ruta=RouteStatus.PLANEADA,
            duracion_estimada_minutos=60,
            total_distance_km=Decimal("123.456789"),
            total_orders=0,
        )

        vehicle = Vehicle(id=vehicle_id, placa="ABC123", driver_name="Test")

        mock_route_repository.find_by_id.return_value = route
        mock_vehicle_repository.find_by_id.return_value = vehicle

        # Act
        result = await use_case.execute(route_id=route_id)

        # Assert
        assert isinstance(result["total_distance_km"], float)
        assert result["total_distance_km"] == 123.456789

    @pytest.mark.asyncio
    async def test_execute_different_route_statuses(
        self, use_case, mock_route_repository, mock_vehicle_repository
    ):
        """Test routes with different status values."""
        # Arrange
        vehicle_id = uuid4()
        vehicle = Vehicle(id=vehicle_id, placa="ABC123", driver_name="Driver")

        for status in [RouteStatus.PLANEADA, RouteStatus.EN_PROGRESO,
                       RouteStatus.COMPLETADA, RouteStatus.CANCELADA]:
            route_id = uuid4()
            route = Route(
                id=route_id,
                vehicle_id=vehicle_id,
                fecha_ruta=date(2024, 1, 15),
                estado_ruta=status,
                duracion_estimada_minutos=60,
                total_distance_km=Decimal("20.0"),
                total_orders=0,
            )

            mock_route_repository.find_by_id.return_value = route
            mock_vehicle_repository.find_by_id.return_value = vehicle

            # Act
            result = await use_case.execute(route_id=route_id)

            # Assert
            assert result["estado_ruta"] == status.value

    @pytest.mark.asyncio
    async def test_execute_different_shipment_statuses(
        self, use_case, mock_route_repository, mock_vehicle_repository
    ):
        """Test shipments with different status values."""
        # Arrange
        vehicle_id = uuid4()
        route_id = uuid4()

        shipments = []
        for i, status in enumerate([ShipmentStatus.ASSIGNED_TO_ROUTE,
                                    ShipmentStatus.IN_TRANSIT,
                                    ShipmentStatus.DELIVERED], 1):
            shipment = self._create_shipment(route_id=route_id, sequence=i, status=status)
            shipments.append(shipment)

        route = Route(
            id=route_id,
            vehicle_id=vehicle_id,
            fecha_ruta=date(2024, 1, 15),
            estado_ruta=RouteStatus.EN_PROGRESO,
            duracion_estimada_minutos=120,
            total_distance_km=Decimal("50.0"),
            total_orders=3,
        )
        route.set_shipments(shipments)

        vehicle = Vehicle(id=vehicle_id, placa="ABC123", driver_name="Driver")

        mock_route_repository.find_by_id.return_value = route
        mock_vehicle_repository.find_by_id.return_value = vehicle

        # Act
        result = await use_case.execute(route_id=route_id)

        # Assert
        assert result["shipments"][0]["shipment_status"] == "assigned_to_route"
        assert result["shipments"][1]["shipment_status"] == "in_transit"
        assert result["shipments"][2]["shipment_status"] == "delivered"

    @pytest.mark.asyncio
    async def test_execute_repository_error_propagates(
        self, use_case, mock_route_repository, mock_vehicle_repository
    ):
        """Test that repository errors are propagated correctly."""
        # Arrange
        route_id = uuid4()
        mock_route_repository.find_by_id.side_effect = Exception("Database error")

        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            await use_case.execute(route_id=route_id)

        assert "Database error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_execute_vehicle_repository_error_propagates(
        self, use_case, mock_route_repository, mock_vehicle_repository
    ):
        """Test that vehicle repository errors are propagated."""
        # Arrange
        vehicle_id = uuid4()
        route_id = uuid4()

        route = Route(
            id=route_id,
            vehicle_id=vehicle_id,
            fecha_ruta=date(2024, 1, 15),
            estado_ruta=RouteStatus.PLANEADA,
            duracion_estimada_minutos=60,
            total_distance_km=Decimal("20.0"),
            total_orders=0,
        )

        mock_route_repository.find_by_id.return_value = route
        mock_vehicle_repository.find_by_id.side_effect = Exception("Vehicle error")

        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            await use_case.execute(route_id=route_id)

        assert "Vehicle error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_execute_vehicle_without_phone(
        self, use_case, mock_route_repository, mock_vehicle_repository
    ):
        """Test route with vehicle that has no phone number."""
        # Arrange
        vehicle_id = uuid4()
        route_id = uuid4()

        route = Route(
            id=route_id,
            vehicle_id=vehicle_id,
            fecha_ruta=date(2024, 1, 15),
            estado_ruta=RouteStatus.PLANEADA,
            duracion_estimada_minutos=60,
            total_distance_km=Decimal("20.0"),
            total_orders=0,
        )

        vehicle = Vehicle(
            id=vehicle_id,
            placa="ABC123",
            driver_name="John Doe",
            driver_phone=None,
        )

        mock_route_repository.find_by_id.return_value = route
        mock_vehicle_repository.find_by_id.return_value = vehicle

        # Act
        result = await use_case.execute(route_id=route_id)

        # Assert
        assert result["driver_phone"] is None
        assert result["vehicle_plate"] == "ABC123"
        assert result["driver_name"] == "John Doe"
