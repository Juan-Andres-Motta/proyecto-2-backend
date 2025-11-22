import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import uuid4
from datetime import date, datetime
from decimal import Decimal
from dataclasses import dataclass

from src.application.use_cases.generate_routes import GenerateRoutesUseCase
from src.domain.entities import Route, Vehicle, Shipment
from src.domain.value_objects import ShipmentStatus, RouteStatus
from src.domain.exceptions import RouteOptimizationError


@dataclass
class MockOptimizationResult:
    """Mock optimization result for testing."""
    vehicle: Vehicle
    shipments: list
    estimated_duration_minutes: int
    total_distance_km: Decimal


class TestGenerateRoutesUseCase:
    """Test suite for GenerateRoutesUseCase."""

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
    def mock_route_optimizer(self):
        """Create a mock route optimizer."""
        return AsyncMock()

    @pytest.fixture
    def mock_event_publisher(self):
        """Create a mock SQS event publisher."""
        publisher = AsyncMock()
        publisher.publish_routes_generated = AsyncMock()
        return publisher

    @pytest.fixture
    def use_case(
        self,
        mock_shipment_repository,
        mock_vehicle_repository,
        mock_route_repository,
        mock_route_optimizer,
        mock_event_publisher,
        session,
    ):
        """Create a GenerateRoutesUseCase instance with mocked dependencies."""
        return GenerateRoutesUseCase(
            shipment_repository=mock_shipment_repository,
            vehicle_repository=mock_vehicle_repository,
            route_repository=mock_route_repository,
            route_optimizer=mock_route_optimizer,
            event_publisher=mock_event_publisher,
            session=session,
        )

    def _create_shipment(self, order_id=None):
        """Helper to create a shipment for testing."""
        return Shipment(
            id=uuid4(),
            order_id=order_id or uuid4(),
            customer_id=uuid4(),
            direccion_entrega="123 Main St",
            ciudad_entrega="City",
            pais_entrega="Country",
            fecha_pedido=datetime(2024, 1, 14, 10, 0, 0),
            fecha_entrega_estimada=date(2024, 1, 15),
        )

    def _create_vehicle(self, vehicle_id=None):
        """Helper to create a vehicle for testing."""
        return Vehicle(
            id=vehicle_id or uuid4(),
            placa="ABC123",
            driver_name="John Doe",
            driver_phone="+1234567890",
        )

    @pytest.mark.asyncio
    async def test_execute_generates_routes_successfully(
        self,
        use_case,
        mock_shipment_repository,
        mock_vehicle_repository,
        mock_route_repository,
        mock_route_optimizer,
        mock_event_publisher,
    ):
        """Test successful route generation."""
        # Arrange
        fecha_entrega = date(2024, 1, 15)
        vehicle = self._create_vehicle()
        vehicle_ids = [vehicle.id]

        shipments = [self._create_shipment(), self._create_shipment()]

        optimization_result = MockOptimizationResult(
            vehicle=vehicle,
            shipments=shipments,
            estimated_duration_minutes=120,
            total_distance_km=Decimal("45.5"),
        )

        mock_shipment_repository.find_pending_by_date.return_value = shipments
        mock_vehicle_repository.find_by_ids.return_value = [vehicle]
        mock_route_optimizer.optimize_routes.return_value = [optimization_result]
        mock_route_repository.save.return_value = None
        mock_shipment_repository.update_many.return_value = None

        # Act
        result = await use_case.execute(
            fecha_entrega_estimada=fecha_entrega,
            vehicle_ids=vehicle_ids,
        )

        # Assert
        assert len(result) == 1
        assert result[0].fecha_ruta == fecha_entrega
        assert result[0].total_orders == 2
        assert result[0].duracion_estimada_minutos == 120
        assert result[0].total_distance_km == Decimal("45.5")

        mock_shipment_repository.find_pending_by_date.assert_called_once_with(fecha_entrega)
        mock_vehicle_repository.find_by_ids.assert_called_once_with(vehicle_ids)
        mock_route_optimizer.optimize_routes.assert_called_once()
        mock_route_repository.save.assert_called_once()
        mock_shipment_repository.update_many.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_no_pending_shipments_returns_empty(
        self,
        use_case,
        mock_shipment_repository,
        mock_vehicle_repository,
        mock_route_repository,
        mock_route_optimizer,
        mock_event_publisher,
    ):
        """Test that empty list is returned when no pending shipments exist."""
        # Arrange
        fecha_entrega = date(2024, 1, 15)
        vehicle_ids = [uuid4()]

        mock_shipment_repository.find_pending_by_date.return_value = []

        # Act
        result = await use_case.execute(
            fecha_entrega_estimada=fecha_entrega,
            vehicle_ids=vehicle_ids,
        )

        # Assert
        assert result == []
        mock_vehicle_repository.find_by_ids.assert_not_called()
        mock_route_optimizer.optimize_routes.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_no_valid_vehicles_raises_error(
        self,
        use_case,
        mock_shipment_repository,
        mock_vehicle_repository,
        mock_route_repository,
        mock_route_optimizer,
        mock_event_publisher,
    ):
        """Test that RouteOptimizationError is raised when no valid vehicles found."""
        # Arrange
        fecha_entrega = date(2024, 1, 15)
        vehicle_ids = [uuid4()]

        shipments = [self._create_shipment()]

        mock_shipment_repository.find_pending_by_date.return_value = shipments
        mock_vehicle_repository.find_by_ids.return_value = []

        # Act & Assert
        with pytest.raises(RouteOptimizationError) as exc_info:
            await use_case.execute(
                fecha_entrega_estimada=fecha_entrega,
                vehicle_ids=vehicle_ids,
            )

        assert "No valid vehicles found" in str(exc_info.value)
        mock_route_optimizer.optimize_routes.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_optimizer_returns_no_routes(
        self,
        use_case,
        mock_shipment_repository,
        mock_vehicle_repository,
        mock_route_repository,
        mock_route_optimizer,
        mock_event_publisher,
    ):
        """Test handling when optimizer returns no routes."""
        # Arrange
        fecha_entrega = date(2024, 1, 15)
        vehicle = self._create_vehicle()
        vehicle_ids = [vehicle.id]

        shipments = [self._create_shipment()]

        mock_shipment_repository.find_pending_by_date.return_value = shipments
        mock_vehicle_repository.find_by_ids.return_value = [vehicle]
        mock_route_optimizer.optimize_routes.return_value = []

        # Act
        result = await use_case.execute(
            fecha_entrega_estimada=fecha_entrega,
            vehicle_ids=vehicle_ids,
        )

        # Assert
        assert result == []
        mock_route_repository.save.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_multiple_routes(
        self,
        use_case,
        mock_shipment_repository,
        mock_vehicle_repository,
        mock_route_repository,
        mock_route_optimizer,
        mock_event_publisher,
    ):
        """Test generation of multiple routes."""
        # Arrange
        fecha_entrega = date(2024, 1, 15)
        vehicle1 = self._create_vehicle()
        vehicle2 = self._create_vehicle()
        vehicle_ids = [vehicle1.id, vehicle2.id]

        shipments1 = [self._create_shipment(), self._create_shipment()]
        shipments2 = [self._create_shipment()]

        optimization_results = [
            MockOptimizationResult(
                vehicle=vehicle1,
                shipments=shipments1,
                estimated_duration_minutes=120,
                total_distance_km=Decimal("45.5"),
            ),
            MockOptimizationResult(
                vehicle=vehicle2,
                shipments=shipments2,
                estimated_duration_minutes=60,
                total_distance_km=Decimal("20.0"),
            ),
        ]

        mock_shipment_repository.find_pending_by_date.return_value = shipments1 + shipments2
        mock_vehicle_repository.find_by_ids.return_value = [vehicle1, vehicle2]
        mock_route_optimizer.optimize_routes.return_value = optimization_results

        # Act
        result = await use_case.execute(
            fecha_entrega_estimada=fecha_entrega,
            vehicle_ids=vehicle_ids,
        )

        # Assert
        assert len(result) == 2
        assert mock_route_repository.save.call_count == 2
        assert mock_shipment_repository.update_many.call_count == 2

    @pytest.mark.asyncio
    async def test_execute_publishes_routes_generated_void_event(
        self,
        use_case,
        mock_shipment_repository,
        mock_vehicle_repository,
        mock_route_repository,
        mock_route_optimizer,
        mock_event_publisher,
    ):
        """Test that routes_generated void event is published once."""
        # Arrange
        fecha_entrega = date(2024, 1, 15)
        vehicle = self._create_vehicle()
        vehicle_ids = [vehicle.id]

        shipments = [self._create_shipment(), self._create_shipment(), self._create_shipment()]

        optimization_result = MockOptimizationResult(
            vehicle=vehicle,
            shipments=shipments,
            estimated_duration_minutes=180,
            total_distance_km=Decimal("60.0"),
        )

        mock_shipment_repository.find_pending_by_date.return_value = shipments
        mock_vehicle_repository.find_by_ids.return_value = [vehicle]
        mock_route_optimizer.optimize_routes.return_value = [optimization_result]

        # Act
        await use_case.execute(
            fecha_entrega_estimada=fecha_entrega,
            vehicle_ids=vehicle_ids,
        )

        # Assert - void event with no arguments
        mock_event_publisher.publish_routes_generated.assert_called_once_with()

    @pytest.mark.asyncio
    async def test_execute_routes_generated_publish_error_logged_not_raised(
        self,
        use_case,
        mock_shipment_repository,
        mock_vehicle_repository,
        mock_route_repository,
        mock_route_optimizer,
        mock_event_publisher,
    ):
        """Test that routes_generated publishing errors are logged but don't stop execution."""
        # Arrange
        fecha_entrega = date(2024, 1, 15)
        vehicle = self._create_vehicle()
        vehicle_ids = [vehicle.id]

        shipments = [self._create_shipment()]

        optimization_result = MockOptimizationResult(
            vehicle=vehicle,
            shipments=shipments,
            estimated_duration_minutes=60,
            total_distance_km=Decimal("20.0"),
        )

        mock_shipment_repository.find_pending_by_date.return_value = shipments
        mock_vehicle_repository.find_by_ids.return_value = [vehicle]
        mock_route_optimizer.optimize_routes.return_value = [optimization_result]
        mock_event_publisher.publish_routes_generated.side_effect = Exception("SQS error")

        # Act - should not raise
        result = await use_case.execute(
            fecha_entrega_estimada=fecha_entrega,
            vehicle_ids=vehicle_ids,
        )

        # Assert
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_execute_shipment_repository_error_propagates(
        self,
        use_case,
        mock_shipment_repository,
        mock_vehicle_repository,
        mock_route_repository,
        mock_route_optimizer,
        mock_event_publisher,
    ):
        """Test that shipment repository errors are propagated."""
        # Arrange
        fecha_entrega = date(2024, 1, 15)
        vehicle_ids = [uuid4()]

        mock_shipment_repository.find_pending_by_date.side_effect = Exception("Database error")

        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            await use_case.execute(
                fecha_entrega_estimada=fecha_entrega,
                vehicle_ids=vehicle_ids,
            )

        assert "Database error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_execute_vehicle_repository_error_propagates(
        self,
        use_case,
        mock_shipment_repository,
        mock_vehicle_repository,
        mock_route_repository,
        mock_route_optimizer,
        mock_event_publisher,
    ):
        """Test that vehicle repository errors are propagated."""
        # Arrange
        fecha_entrega = date(2024, 1, 15)
        vehicle_ids = [uuid4()]

        shipments = [self._create_shipment()]

        mock_shipment_repository.find_pending_by_date.return_value = shipments
        mock_vehicle_repository.find_by_ids.side_effect = Exception("Vehicle error")

        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            await use_case.execute(
                fecha_entrega_estimada=fecha_entrega,
                vehicle_ids=vehicle_ids,
            )

        assert "Vehicle error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_execute_optimizer_error_propagates(
        self,
        use_case,
        mock_shipment_repository,
        mock_vehicle_repository,
        mock_route_repository,
        mock_route_optimizer,
        mock_event_publisher,
    ):
        """Test that optimizer errors are propagated."""
        # Arrange
        fecha_entrega = date(2024, 1, 15)
        vehicle = self._create_vehicle()
        vehicle_ids = [vehicle.id]

        shipments = [self._create_shipment()]

        mock_shipment_repository.find_pending_by_date.return_value = shipments
        mock_vehicle_repository.find_by_ids.return_value = [vehicle]
        mock_route_optimizer.optimize_routes.side_effect = Exception("Optimizer error")

        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            await use_case.execute(
                fecha_entrega_estimada=fecha_entrega,
                vehicle_ids=vehicle_ids,
            )

        assert "Optimizer error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_execute_route_save_error_propagates(
        self,
        use_case,
        mock_shipment_repository,
        mock_vehicle_repository,
        mock_route_repository,
        mock_route_optimizer,
        mock_event_publisher,
    ):
        """Test that route save errors are propagated."""
        # Arrange
        fecha_entrega = date(2024, 1, 15)
        vehicle = self._create_vehicle()
        vehicle_ids = [vehicle.id]

        shipments = [self._create_shipment()]

        optimization_result = MockOptimizationResult(
            vehicle=vehicle,
            shipments=shipments,
            estimated_duration_minutes=60,
            total_distance_km=Decimal("20.0"),
        )

        mock_shipment_repository.find_pending_by_date.return_value = shipments
        mock_vehicle_repository.find_by_ids.return_value = [vehicle]
        mock_route_optimizer.optimize_routes.return_value = [optimization_result]
        mock_route_repository.save.side_effect = Exception("Save error")

        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            await use_case.execute(
                fecha_entrega_estimada=fecha_entrega,
                vehicle_ids=vehicle_ids,
            )

        assert "Save error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_execute_adds_shipments_to_route_with_sequence(
        self,
        use_case,
        mock_shipment_repository,
        mock_vehicle_repository,
        mock_route_repository,
        mock_route_optimizer,
        mock_event_publisher,
    ):
        """Test that shipments are added to route with proper sequence."""
        # Arrange
        fecha_entrega = date(2024, 1, 15)
        vehicle = self._create_vehicle()
        vehicle_ids = [vehicle.id]

        shipments = [self._create_shipment(), self._create_shipment(), self._create_shipment()]

        optimization_result = MockOptimizationResult(
            vehicle=vehicle,
            shipments=shipments,
            estimated_duration_minutes=120,
            total_distance_km=Decimal("45.0"),
        )

        mock_shipment_repository.find_pending_by_date.return_value = shipments
        mock_vehicle_repository.find_by_ids.return_value = [vehicle]
        mock_route_optimizer.optimize_routes.return_value = [optimization_result]

        # Act
        result = await use_case.execute(
            fecha_entrega_estimada=fecha_entrega,
            vehicle_ids=vehicle_ids,
        )

        # Assert
        assert result[0].total_orders == 3
        route_shipments = result[0].shipments
        assert len(route_shipments) == 3
        # Verify sequences
        for i, shipment in enumerate(route_shipments, 1):
            assert shipment.sequence_in_route == i
            assert shipment.shipment_status == ShipmentStatus.ASSIGNED_TO_ROUTE

    @pytest.mark.asyncio
    async def test_execute_assigns_vehicle_id_to_route(
        self,
        use_case,
        mock_shipment_repository,
        mock_vehicle_repository,
        mock_route_repository,
        mock_route_optimizer,
        mock_event_publisher,
    ):
        """Test that vehicle ID is properly assigned to route."""
        # Arrange
        fecha_entrega = date(2024, 1, 15)
        vehicle = self._create_vehicle()
        vehicle_ids = [vehicle.id]

        shipments = [self._create_shipment()]

        optimization_result = MockOptimizationResult(
            vehicle=vehicle,
            shipments=shipments,
            estimated_duration_minutes=60,
            total_distance_km=Decimal("20.0"),
        )

        mock_shipment_repository.find_pending_by_date.return_value = shipments
        mock_vehicle_repository.find_by_ids.return_value = [vehicle]
        mock_route_optimizer.optimize_routes.return_value = [optimization_result]

        # Act
        result = await use_case.execute(
            fecha_entrega_estimada=fecha_entrega,
            vehicle_ids=vehicle_ids,
        )

        # Assert
        assert result[0].vehicle_id == vehicle.id

    @pytest.mark.asyncio
    async def test_execute_route_has_planeada_status(
        self,
        use_case,
        mock_shipment_repository,
        mock_vehicle_repository,
        mock_route_repository,
        mock_route_optimizer,
        mock_event_publisher,
    ):
        """Test that generated routes have PLANEADA status."""
        # Arrange
        fecha_entrega = date(2024, 1, 15)
        vehicle = self._create_vehicle()
        vehicle_ids = [vehicle.id]

        shipments = [self._create_shipment()]

        optimization_result = MockOptimizationResult(
            vehicle=vehicle,
            shipments=shipments,
            estimated_duration_minutes=60,
            total_distance_km=Decimal("20.0"),
        )

        mock_shipment_repository.find_pending_by_date.return_value = shipments
        mock_vehicle_repository.find_by_ids.return_value = [vehicle]
        mock_route_optimizer.optimize_routes.return_value = [optimization_result]

        # Act
        result = await use_case.execute(
            fecha_entrega_estimada=fecha_entrega,
            vehicle_ids=vehicle_ids,
        )

        # Assert
        assert result[0].estado_ruta == RouteStatus.PLANEADA

    @pytest.mark.asyncio
    async def test_execute_publishes_one_void_event_for_multiple_routes(
        self,
        use_case,
        mock_shipment_repository,
        mock_vehicle_repository,
        mock_route_repository,
        mock_route_optimizer,
        mock_event_publisher,
    ):
        """Test that only one void event is published even for multiple routes."""
        # Arrange
        fecha_entrega = date(2024, 1, 15)
        vehicle1 = self._create_vehicle()
        vehicle2 = self._create_vehicle()
        vehicle_ids = [vehicle1.id, vehicle2.id]

        shipments1 = [self._create_shipment(), self._create_shipment()]
        shipments2 = [self._create_shipment()]

        optimization_results = [
            MockOptimizationResult(
                vehicle=vehicle1,
                shipments=shipments1,
                estimated_duration_minutes=120,
                total_distance_km=Decimal("45.5"),
            ),
            MockOptimizationResult(
                vehicle=vehicle2,
                shipments=shipments2,
                estimated_duration_minutes=60,
                total_distance_km=Decimal("20.0"),
            ),
        ]

        mock_shipment_repository.find_pending_by_date.return_value = shipments1 + shipments2
        mock_vehicle_repository.find_by_ids.return_value = [vehicle1, vehicle2]
        mock_route_optimizer.optimize_routes.return_value = optimization_results

        # Act
        await use_case.execute(
            fecha_entrega_estimada=fecha_entrega,
            vehicle_ids=vehicle_ids,
        )

        # Assert - only one routes_generated void event
        mock_event_publisher.publish_routes_generated.assert_called_once_with()
