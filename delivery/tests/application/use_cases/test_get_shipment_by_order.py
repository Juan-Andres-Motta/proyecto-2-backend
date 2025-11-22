import pytest
from unittest.mock import AsyncMock
from uuid import uuid4
from datetime import date, datetime
from decimal import Decimal

from src.application.use_cases.get_shipment_by_order import GetShipmentByOrderUseCase
from src.domain.entities import Shipment, Route, Vehicle
from src.domain.value_objects import ShipmentStatus, RouteStatus
from src.domain.exceptions import EntityNotFoundError


class TestGetShipmentByOrderUseCase:
    """Test suite for GetShipmentByOrderUseCase."""

    @pytest.fixture
    def mock_shipment_repository(self):
        """Create a mock shipment repository."""
        return AsyncMock()

    @pytest.fixture
    def mock_vehicle_repository(self):
        """Create a mock vehicle repository."""
        return AsyncMock()

    @pytest.fixture
    def mock_route_repository(self):
        """Create a mock route repository."""
        return AsyncMock()

    @pytest.fixture
    def use_case(
        self, mock_shipment_repository, mock_vehicle_repository, mock_route_repository
    ):
        """Create a GetShipmentByOrderUseCase instance with mocked dependencies."""
        return GetShipmentByOrderUseCase(
            shipment_repository=mock_shipment_repository,
            vehicle_repository=mock_vehicle_repository,
            route_repository=mock_route_repository,
        )

    def _create_shipment(
        self, order_id=None, route_id=None, status=ShipmentStatus.PENDING
    ):
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
            shipment_status=status,
        )
        if route_id:
            shipment.route_id = route_id
            shipment.sequence_in_route = 1
        return shipment

    @pytest.mark.asyncio
    async def test_execute_returns_shipment_with_vehicle_info(
        self,
        use_case,
        mock_shipment_repository,
        mock_vehicle_repository,
        mock_route_repository,
    ):
        """Test successful retrieval of shipment with vehicle information."""
        # Arrange
        order_id = uuid4()
        route_id = uuid4()
        vehicle_id = uuid4()

        shipment = self._create_shipment(
            order_id=order_id,
            route_id=route_id,
            status=ShipmentStatus.ASSIGNED_TO_ROUTE,
        )

        route = Route(
            id=route_id,
            vehicle_id=vehicle_id,
            fecha_ruta=date(2024, 1, 15),
            estado_ruta=RouteStatus.PLANEADA,
            duracion_estimada_minutos=120,
            total_distance_km=Decimal("45.5"),
            total_orders=1,
        )

        vehicle = Vehicle(
            id=vehicle_id,
            placa="ABC123",
            driver_name="John Doe",
        )

        mock_shipment_repository.find_by_order_id.return_value = shipment
        mock_route_repository.find_by_id.return_value = route
        mock_vehicle_repository.find_by_id.return_value = vehicle

        # Act
        result = await use_case.execute(order_id=order_id)

        # Assert
        assert result["shipment_id"] == shipment.id
        assert result["order_id"] == order_id
        assert result["shipment_status"] == "assigned_to_route"
        assert result["vehicle_plate"] == "ABC123"
        assert result["driver_name"] == "John Doe"
        assert result["fecha_entrega_estimada"] == date(2024, 1, 15)
        assert result["route_id"] == route_id

        mock_shipment_repository.find_by_order_id.assert_called_once_with(order_id)
        mock_route_repository.find_by_id.assert_called_once_with(route_id)
        mock_vehicle_repository.find_by_id.assert_called_once_with(vehicle_id)

    @pytest.mark.asyncio
    async def test_execute_shipment_not_found_raises_error(
        self,
        use_case,
        mock_shipment_repository,
        mock_vehicle_repository,
        mock_route_repository,
    ):
        """Test that EntityNotFoundError is raised when shipment not found."""
        # Arrange
        order_id = uuid4()
        mock_shipment_repository.find_by_order_id.return_value = None

        # Act & Assert
        with pytest.raises(EntityNotFoundError) as exc_info:
            await use_case.execute(order_id=order_id)

        assert exc_info.value.entity_type == "Shipment"
        assert exc_info.value.entity_id == str(order_id)
        mock_shipment_repository.find_by_order_id.assert_called_once_with(order_id)
        mock_route_repository.find_by_id.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_shipment_without_route(
        self,
        use_case,
        mock_shipment_repository,
        mock_vehicle_repository,
        mock_route_repository,
    ):
        """Test retrieval of shipment that is not assigned to a route."""
        # Arrange
        order_id = uuid4()
        shipment = self._create_shipment(order_id=order_id, route_id=None)

        mock_shipment_repository.find_by_order_id.return_value = shipment

        # Act
        result = await use_case.execute(order_id=order_id)

        # Assert
        assert result["shipment_id"] == shipment.id
        assert result["order_id"] == order_id
        assert result["vehicle_plate"] is None
        assert result["driver_name"] is None
        assert result["route_id"] is None

        mock_route_repository.find_by_id.assert_not_called()
        mock_vehicle_repository.find_by_id.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_route_not_found(
        self,
        use_case,
        mock_shipment_repository,
        mock_vehicle_repository,
        mock_route_repository,
    ):
        """Test handling when route is not found."""
        # Arrange
        order_id = uuid4()
        route_id = uuid4()

        shipment = self._create_shipment(
            order_id=order_id,
            route_id=route_id,
            status=ShipmentStatus.ASSIGNED_TO_ROUTE,
        )

        mock_shipment_repository.find_by_order_id.return_value = shipment
        mock_route_repository.find_by_id.return_value = None

        # Act
        result = await use_case.execute(order_id=order_id)

        # Assert
        assert result["vehicle_plate"] is None
        assert result["driver_name"] is None
        assert result["route_id"] == route_id

    @pytest.mark.asyncio
    async def test_execute_vehicle_not_found(
        self,
        use_case,
        mock_shipment_repository,
        mock_vehicle_repository,
        mock_route_repository,
    ):
        """Test handling when vehicle is not found."""
        # Arrange
        order_id = uuid4()
        route_id = uuid4()
        vehicle_id = uuid4()

        shipment = self._create_shipment(
            order_id=order_id,
            route_id=route_id,
            status=ShipmentStatus.ASSIGNED_TO_ROUTE,
        )

        route = Route(
            id=route_id,
            vehicle_id=vehicle_id,
            fecha_ruta=date(2024, 1, 15),
            estado_ruta=RouteStatus.PLANEADA,
            duracion_estimada_minutos=60,
            total_distance_km=Decimal("20.0"),
            total_orders=1,
        )

        mock_shipment_repository.find_by_order_id.return_value = shipment
        mock_route_repository.find_by_id.return_value = route
        mock_vehicle_repository.find_by_id.return_value = None

        # Act
        result = await use_case.execute(order_id=order_id)

        # Assert
        assert result["vehicle_plate"] is None
        assert result["driver_name"] is None

    @pytest.mark.asyncio
    async def test_execute_different_shipment_statuses(
        self,
        use_case,
        mock_shipment_repository,
        mock_vehicle_repository,
        mock_route_repository,
    ):
        """Test retrieval of shipments with different statuses."""
        for status in [
            ShipmentStatus.PENDING,
            ShipmentStatus.ASSIGNED_TO_ROUTE,
            ShipmentStatus.IN_TRANSIT,
            ShipmentStatus.DELIVERED,
        ]:
            # Arrange
            order_id = uuid4()
            shipment = self._create_shipment(order_id=order_id, status=status)

            mock_shipment_repository.find_by_order_id.return_value = shipment

            # Act
            result = await use_case.execute(order_id=order_id)

            # Assert
            assert result["shipment_status"] == status.value

    @pytest.mark.asyncio
    async def test_execute_repository_error_propagates(
        self,
        use_case,
        mock_shipment_repository,
        mock_vehicle_repository,
        mock_route_repository,
    ):
        """Test that repository errors are propagated correctly."""
        # Arrange
        order_id = uuid4()
        mock_shipment_repository.find_by_order_id.side_effect = Exception("Database error")

        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            await use_case.execute(order_id=order_id)

        assert "Database error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_execute_route_repository_error_propagates(
        self,
        use_case,
        mock_shipment_repository,
        mock_vehicle_repository,
        mock_route_repository,
    ):
        """Test that route repository errors are propagated."""
        # Arrange
        order_id = uuid4()
        route_id = uuid4()

        shipment = self._create_shipment(
            order_id=order_id,
            route_id=route_id,
            status=ShipmentStatus.ASSIGNED_TO_ROUTE,
        )

        mock_shipment_repository.find_by_order_id.return_value = shipment
        mock_route_repository.find_by_id.side_effect = Exception("Route error")

        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            await use_case.execute(order_id=order_id)

        assert "Route error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_execute_vehicle_repository_error_propagates(
        self,
        use_case,
        mock_shipment_repository,
        mock_vehicle_repository,
        mock_route_repository,
    ):
        """Test that vehicle repository errors are propagated."""
        # Arrange
        order_id = uuid4()
        route_id = uuid4()
        vehicle_id = uuid4()

        shipment = self._create_shipment(
            order_id=order_id,
            route_id=route_id,
            status=ShipmentStatus.ASSIGNED_TO_ROUTE,
        )

        route = Route(
            id=route_id,
            vehicle_id=vehicle_id,
            fecha_ruta=date(2024, 1, 15),
            estado_ruta=RouteStatus.PLANEADA,
            duracion_estimada_minutos=60,
            total_distance_km=Decimal("20.0"),
            total_orders=1,
        )

        mock_shipment_repository.find_by_order_id.return_value = shipment
        mock_route_repository.find_by_id.return_value = route
        mock_vehicle_repository.find_by_id.side_effect = Exception("Vehicle error")

        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            await use_case.execute(order_id=order_id)

        assert "Vehicle error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_execute_returns_all_expected_fields(
        self,
        use_case,
        mock_shipment_repository,
        mock_vehicle_repository,
        mock_route_repository,
    ):
        """Test that all expected fields are returned in the result."""
        # Arrange
        order_id = uuid4()
        shipment = self._create_shipment(order_id=order_id)
        mock_shipment_repository.find_by_order_id.return_value = shipment

        # Act
        result = await use_case.execute(order_id=order_id)

        # Assert
        expected_keys = {
            "shipment_id",
            "order_id",
            "shipment_status",
            "vehicle_plate",
            "driver_name",
            "fecha_entrega_estimada",
            "route_id",
        }
        assert set(result.keys()) == expected_keys

    @pytest.mark.asyncio
    async def test_execute_in_transit_shipment(
        self,
        use_case,
        mock_shipment_repository,
        mock_vehicle_repository,
        mock_route_repository,
    ):
        """Test retrieval of in-transit shipment with complete info."""
        # Arrange
        order_id = uuid4()
        route_id = uuid4()
        vehicle_id = uuid4()

        shipment = self._create_shipment(
            order_id=order_id,
            route_id=route_id,
            status=ShipmentStatus.IN_TRANSIT,
        )

        route = Route(
            id=route_id,
            vehicle_id=vehicle_id,
            fecha_ruta=date(2024, 1, 15),
            estado_ruta=RouteStatus.EN_PROGRESO,
            duracion_estimada_minutos=90,
            total_distance_km=Decimal("35.0"),
            total_orders=3,
        )

        vehicle = Vehicle(
            id=vehicle_id,
            placa="XYZ789",
            driver_name="Jane Smith",
            driver_phone="+9876543210",
        )

        mock_shipment_repository.find_by_order_id.return_value = shipment
        mock_route_repository.find_by_id.return_value = route
        mock_vehicle_repository.find_by_id.return_value = vehicle

        # Act
        result = await use_case.execute(order_id=order_id)

        # Assert
        assert result["shipment_status"] == "in_transit"
        assert result["vehicle_plate"] == "XYZ789"
        assert result["driver_name"] == "Jane Smith"
