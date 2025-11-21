import pytest
from unittest.mock import AsyncMock, patch
from uuid import uuid4
from datetime import date, datetime
from decimal import Decimal

from src.application.use_cases.update_route_status import UpdateRouteStatusUseCase
from src.domain.entities import Route, Shipment
from src.domain.value_objects import RouteStatus, ShipmentStatus
from src.domain.exceptions import EntityNotFoundError, InvalidStatusTransitionError


class TestUpdateRouteStatusUseCase:
    """Test suite for UpdateRouteStatusUseCase."""

    @pytest.fixture
    def mock_route_repository(self):
        """Create a mock route repository."""
        return AsyncMock()

    @pytest.fixture
    def mock_shipment_repository(self):
        """Create a mock shipment repository."""
        return AsyncMock()

    @pytest.fixture
    def use_case(self, mock_route_repository, mock_shipment_repository):
        """Create an UpdateRouteStatusUseCase instance with mocked dependencies."""
        return UpdateRouteStatusUseCase(
            route_repository=mock_route_repository,
            shipment_repository=mock_shipment_repository,
        )

    def _create_route_with_shipments(self, route_id, status=RouteStatus.PLANEADA, num_shipments=2):
        """Helper to create a route with shipments."""
        route = Route(
            id=route_id,
            vehicle_id=uuid4(),
            fecha_ruta=date(2024, 1, 15),
            estado_ruta=status,
            duracion_estimada_minutos=120,
            total_distance_km=Decimal("45.5"),
            total_orders=num_shipments,
        )

        shipments = []
        for i in range(num_shipments):
            shipment = Shipment(
                id=uuid4(),
                order_id=uuid4(),
                customer_id=uuid4(),
                direccion_entrega=f"Address {i+1}",
                ciudad_entrega="City",
                pais_entrega="Country",
                fecha_pedido=datetime(2024, 1, 14, 10, 0, 0),
                fecha_entrega_estimada=date(2024, 1, 15),
            )
            # Manually set the route assignment to match expected status
            shipment.route_id = route_id
            shipment.sequence_in_route = i + 1
            if status == RouteStatus.PLANEADA:
                shipment.shipment_status = ShipmentStatus.ASSIGNED_TO_ROUTE
            elif status == RouteStatus.EN_PROGRESO:
                shipment.shipment_status = ShipmentStatus.IN_TRANSIT
            shipments.append(shipment)

        route.set_shipments(shipments)
        return route

    @pytest.mark.asyncio
    async def test_execute_start_route_success(
        self, use_case, mock_route_repository, mock_shipment_repository
    ):
        """Test successful route start (PLANEADA -> EN_PROGRESO)."""
        # Arrange
        route_id = uuid4()
        route = self._create_route_with_shipments(route_id, RouteStatus.PLANEADA)

        mock_route_repository.find_by_id.return_value = route
        mock_route_repository.update.return_value = None
        mock_shipment_repository.update.return_value = None

        # Act
        result = await use_case.execute(route_id=route_id, new_status="en_progreso")

        # Assert
        assert result.estado_ruta == RouteStatus.EN_PROGRESO
        mock_route_repository.find_by_id.assert_called_once_with(route_id)
        mock_route_repository.update.assert_called_once_with(route)
        # Shipments should be updated
        assert mock_shipment_repository.update.call_count == 2

    @pytest.mark.asyncio
    async def test_execute_complete_route_success(
        self, use_case, mock_route_repository, mock_shipment_repository
    ):
        """Test successful route completion (EN_PROGRESO -> COMPLETADA)."""
        # Arrange
        route_id = uuid4()
        route = self._create_route_with_shipments(route_id, RouteStatus.EN_PROGRESO)

        mock_route_repository.find_by_id.return_value = route
        mock_route_repository.update.return_value = None

        # Act
        result = await use_case.execute(route_id=route_id, new_status="completada")

        # Assert
        assert result.estado_ruta == RouteStatus.COMPLETADA
        mock_route_repository.update.assert_called_once_with(route)

    @pytest.mark.asyncio
    async def test_execute_cancel_route_from_planeada(
        self, use_case, mock_route_repository, mock_shipment_repository
    ):
        """Test successful route cancellation from PLANEADA."""
        # Arrange
        route_id = uuid4()
        route = self._create_route_with_shipments(route_id, RouteStatus.PLANEADA)

        mock_route_repository.find_by_id.return_value = route
        mock_route_repository.update.return_value = None

        # Act
        result = await use_case.execute(route_id=route_id, new_status="cancelada")

        # Assert
        assert result.estado_ruta == RouteStatus.CANCELADA
        mock_route_repository.update.assert_called_once_with(route)

    @pytest.mark.asyncio
    async def test_execute_cancel_route_from_en_progreso(
        self, use_case, mock_route_repository, mock_shipment_repository
    ):
        """Test successful route cancellation from EN_PROGRESO."""
        # Arrange
        route_id = uuid4()
        route = self._create_route_with_shipments(route_id, RouteStatus.EN_PROGRESO)

        mock_route_repository.find_by_id.return_value = route
        mock_route_repository.update.return_value = None

        # Act
        result = await use_case.execute(route_id=route_id, new_status="cancelada")

        # Assert
        assert result.estado_ruta == RouteStatus.CANCELADA

    @pytest.mark.asyncio
    async def test_execute_route_not_found_raises_error(
        self, use_case, mock_route_repository, mock_shipment_repository
    ):
        """Test that EntityNotFoundError is raised when route not found."""
        # Arrange
        route_id = uuid4()
        mock_route_repository.find_by_id.return_value = None

        # Act & Assert
        with pytest.raises(EntityNotFoundError) as exc_info:
            await use_case.execute(route_id=route_id, new_status="en_progreso")

        assert exc_info.value.entity_type == "Route"
        assert exc_info.value.entity_id == str(route_id)
        mock_route_repository.update.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_invalid_status_value_raises_error(
        self, use_case, mock_route_repository, mock_shipment_repository
    ):
        """Test that invalid status value raises ValueError."""
        # Arrange
        route_id = uuid4()
        route = self._create_route_with_shipments(route_id, RouteStatus.PLANEADA)
        mock_route_repository.find_by_id.return_value = route

        # Act & Assert
        with pytest.raises(ValueError):
            await use_case.execute(route_id=route_id, new_status="invalid_status")

        mock_route_repository.update.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_transition_to_planeada_raises_error(
        self, use_case, mock_route_repository, mock_shipment_repository
    ):
        """Test that transitioning to PLANEADA raises InvalidStatusTransitionError."""
        # Arrange
        route_id = uuid4()
        route = self._create_route_with_shipments(route_id, RouteStatus.EN_PROGRESO)
        mock_route_repository.find_by_id.return_value = route

        # Act & Assert
        with pytest.raises(InvalidStatusTransitionError) as exc_info:
            await use_case.execute(route_id=route_id, new_status="planeada")

        assert exc_info.value.entity_type == "Route"
        assert exc_info.value.current_status == "en_progreso"
        assert exc_info.value.target_status == "planeada"
        mock_route_repository.update.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_invalid_start_from_completada(
        self, use_case, mock_route_repository, mock_shipment_repository
    ):
        """Test that starting a completed route raises error."""
        # Arrange
        route_id = uuid4()
        route = Route(
            id=route_id,
            vehicle_id=uuid4(),
            fecha_ruta=date(2024, 1, 15),
            estado_ruta=RouteStatus.COMPLETADA,
            duracion_estimada_minutos=120,
            total_distance_km=Decimal("45.5"),
            total_orders=0,
        )
        mock_route_repository.find_by_id.return_value = route

        # Act & Assert
        with pytest.raises(ValueError):
            await use_case.execute(route_id=route_id, new_status="en_progreso")

        mock_route_repository.update.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_invalid_complete_from_planeada(
        self, use_case, mock_route_repository, mock_shipment_repository
    ):
        """Test that completing a planned route raises error."""
        # Arrange
        route_id = uuid4()
        route = self._create_route_with_shipments(route_id, RouteStatus.PLANEADA)
        mock_route_repository.find_by_id.return_value = route

        # Act & Assert
        with pytest.raises(ValueError):
            await use_case.execute(route_id=route_id, new_status="completada")

        mock_route_repository.update.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_invalid_cancel_from_completada(
        self, use_case, mock_route_repository, mock_shipment_repository
    ):
        """Test that cancelling a completed route raises error."""
        # Arrange
        route_id = uuid4()
        route = Route(
            id=route_id,
            vehicle_id=uuid4(),
            fecha_ruta=date(2024, 1, 15),
            estado_ruta=RouteStatus.COMPLETADA,
            duracion_estimada_minutos=120,
            total_distance_km=Decimal("45.5"),
            total_orders=0,
        )
        mock_route_repository.find_by_id.return_value = route

        # Act & Assert
        with pytest.raises(ValueError):
            await use_case.execute(route_id=route_id, new_status="cancelada")

        mock_route_repository.update.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_start_route_updates_shipments_to_in_transit(
        self, use_case, mock_route_repository, mock_shipment_repository
    ):
        """Test that starting a route updates shipments to in_transit."""
        # Arrange
        route_id = uuid4()
        route = self._create_route_with_shipments(route_id, RouteStatus.PLANEADA, num_shipments=3)

        mock_route_repository.find_by_id.return_value = route
        mock_route_repository.update.return_value = None
        mock_shipment_repository.update.return_value = None

        # Act
        await use_case.execute(route_id=route_id, new_status="en_progreso")

        # Assert
        assert mock_shipment_repository.update.call_count == 3
        for shipment in route.shipments:
            assert shipment.shipment_status == ShipmentStatus.IN_TRANSIT

    @pytest.mark.asyncio
    async def test_execute_repository_update_error_propagates(
        self, use_case, mock_route_repository, mock_shipment_repository
    ):
        """Test that repository update errors are propagated."""
        # Arrange
        route_id = uuid4()
        route = self._create_route_with_shipments(route_id, RouteStatus.EN_PROGRESO)
        mock_route_repository.find_by_id.return_value = route
        mock_route_repository.update.side_effect = Exception("Database error")

        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            await use_case.execute(route_id=route_id, new_status="completada")

        assert "Database error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_execute_repository_find_error_propagates(
        self, use_case, mock_route_repository, mock_shipment_repository
    ):
        """Test that repository find errors are propagated."""
        # Arrange
        route_id = uuid4()
        mock_route_repository.find_by_id.side_effect = Exception("Connection error")

        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            await use_case.execute(route_id=route_id, new_status="en_progreso")

        assert "Connection error" in str(exc_info.value)
        mock_route_repository.update.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_shipment_update_error_propagates(
        self, use_case, mock_route_repository, mock_shipment_repository
    ):
        """Test that shipment update errors are propagated."""
        # Arrange
        route_id = uuid4()
        route = self._create_route_with_shipments(route_id, RouteStatus.PLANEADA)
        mock_route_repository.find_by_id.return_value = route
        mock_shipment_repository.update.side_effect = Exception("Shipment error")

        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            await use_case.execute(route_id=route_id, new_status="en_progreso")

        assert "Shipment error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_execute_returns_updated_route(
        self, use_case, mock_route_repository, mock_shipment_repository
    ):
        """Test that the updated route is returned."""
        # Arrange
        route_id = uuid4()
        route = self._create_route_with_shipments(route_id, RouteStatus.EN_PROGRESO)

        mock_route_repository.find_by_id.return_value = route
        mock_route_repository.update.return_value = None

        # Act
        result = await use_case.execute(route_id=route_id, new_status="completada")

        # Assert
        assert result is route
        assert result.id == route_id
        assert result.estado_ruta == RouteStatus.COMPLETADA

    @pytest.mark.asyncio
    async def test_execute_route_with_no_shipments(
        self, use_case, mock_route_repository, mock_shipment_repository
    ):
        """Test starting a route with no shipments."""
        # Arrange
        route_id = uuid4()
        route = Route(
            id=route_id,
            vehicle_id=uuid4(),
            fecha_ruta=date(2024, 1, 15),
            estado_ruta=RouteStatus.PLANEADA,
            duracion_estimada_minutos=0,
            total_distance_km=Decimal("0.0"),
            total_orders=0,
        )

        mock_route_repository.find_by_id.return_value = route
        mock_route_repository.update.return_value = None

        # Act
        result = await use_case.execute(route_id=route_id, new_status="en_progreso")

        # Assert
        assert result.estado_ruta == RouteStatus.EN_PROGRESO
        mock_shipment_repository.update.assert_not_called()
