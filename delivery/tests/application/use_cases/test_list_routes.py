import pytest
from unittest.mock import AsyncMock
from uuid import uuid4
from datetime import date
from decimal import Decimal

from src.application.use_cases.list_routes import ListRoutesUseCase
from src.domain.entities import Route, Vehicle
from src.domain.value_objects import RouteStatus


class TestListRoutesUseCase:
    """Test suite for ListRoutesUseCase."""

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
        """Create a ListRoutesUseCase instance with mocked dependencies."""
        return ListRoutesUseCase(
            route_repository=mock_route_repository,
            vehicle_repository=mock_vehicle_repository,
        )

    @pytest.mark.asyncio
    async def test_execute_returns_routes_with_vehicle_info(
        self, use_case, mock_route_repository, mock_vehicle_repository
    ):
        """Test successful retrieval of routes with vehicle information."""
        # Arrange
        vehicle_id = uuid4()
        route_id = uuid4()

        route = Route(
            id=route_id,
            vehicle_id=vehicle_id,
            fecha_ruta=date(2024, 1, 15),
            estado_ruta=RouteStatus.PLANEADA,
            duracion_estimada_minutos=120,
            total_distance_km=Decimal("45.5"),
            total_orders=5,
        )

        vehicle = Vehicle(
            id=vehicle_id,
            placa="ABC123",
            driver_name="John Doe",
        )

        mock_route_repository.find_all.return_value = ([route], 1)
        mock_vehicle_repository.find_by_id.return_value = vehicle

        # Act
        result, total = await use_case.execute()

        # Assert
        assert total == 1
        assert len(result) == 1
        assert result[0]["id"] == route_id
        assert result[0]["vehicle_id"] == vehicle_id
        assert result[0]["vehicle_plate"] == "ABC123"
        assert result[0]["driver_name"] == "John Doe"
        assert result[0]["fecha_ruta"] == date(2024, 1, 15)
        assert result[0]["estado_ruta"] == "planeada"
        assert result[0]["duracion_estimada_minutos"] == 120
        assert result[0]["total_distance_km"] == 45.5
        assert result[0]["total_orders"] == 5

    @pytest.mark.asyncio
    async def test_execute_with_filters(
        self, use_case, mock_route_repository, mock_vehicle_repository
    ):
        """Test retrieval with date and status filters."""
        # Arrange
        fecha_ruta = date(2024, 1, 15)
        estado_ruta = "planeada"

        mock_route_repository.find_all.return_value = ([], 0)

        # Act
        result, total = await use_case.execute(
            fecha_ruta=fecha_ruta,
            estado_ruta=estado_ruta,
            page=1,
            page_size=20,
        )

        # Assert
        mock_route_repository.find_all.assert_called_once_with(
            fecha_ruta=fecha_ruta,
            estado_ruta=estado_ruta,
            page=1,
            page_size=20,
        )
        assert result == []
        assert total == 0

    @pytest.mark.asyncio
    async def test_execute_with_pagination(
        self, use_case, mock_route_repository, mock_vehicle_repository
    ):
        """Test retrieval with custom pagination parameters."""
        # Arrange
        mock_route_repository.find_all.return_value = ([], 0)

        # Act
        await use_case.execute(page=3, page_size=50)

        # Assert
        mock_route_repository.find_all.assert_called_once_with(
            fecha_ruta=None,
            estado_ruta=None,
            page=3,
            page_size=50,
        )

    @pytest.mark.asyncio
    async def test_execute_returns_empty_list_when_no_routes(
        self, use_case, mock_route_repository, mock_vehicle_repository
    ):
        """Test that empty list is returned when no routes exist."""
        # Arrange
        mock_route_repository.find_all.return_value = ([], 0)

        # Act
        result, total = await use_case.execute()

        # Assert
        assert result == []
        assert total == 0

    @pytest.mark.asyncio
    async def test_execute_handles_vehicle_not_found(
        self, use_case, mock_route_repository, mock_vehicle_repository
    ):
        """Test handling when vehicle is not found for a route."""
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
            total_orders=3,
        )

        mock_route_repository.find_all.return_value = ([route], 1)
        mock_vehicle_repository.find_by_id.return_value = None

        # Act
        result, total = await use_case.execute()

        # Assert
        assert total == 1
        assert len(result) == 1
        assert result[0]["vehicle_plate"] is None
        assert result[0]["driver_name"] is None

    @pytest.mark.asyncio
    async def test_execute_multiple_routes(
        self, use_case, mock_route_repository, mock_vehicle_repository
    ):
        """Test retrieval of multiple routes."""
        # Arrange
        vehicle_id_1 = uuid4()
        vehicle_id_2 = uuid4()
        route_id_1 = uuid4()
        route_id_2 = uuid4()

        routes = [
            Route(
                id=route_id_1,
                vehicle_id=vehicle_id_1,
                fecha_ruta=date(2024, 1, 15),
                estado_ruta=RouteStatus.PLANEADA,
                duracion_estimada_minutos=90,
                total_distance_km=Decimal("30.0"),
                total_orders=4,
            ),
            Route(
                id=route_id_2,
                vehicle_id=vehicle_id_2,
                fecha_ruta=date(2024, 1, 15),
                estado_ruta=RouteStatus.EN_PROGRESO,
                duracion_estimada_minutos=120,
                total_distance_km=Decimal("50.0"),
                total_orders=6,
            ),
        ]

        vehicles = {
            vehicle_id_1: Vehicle(id=vehicle_id_1, placa="ABC123", driver_name="Driver 1"),
            vehicle_id_2: Vehicle(id=vehicle_id_2, placa="XYZ789", driver_name="Driver 2"),
        }

        mock_route_repository.find_all.return_value = (routes, 2)
        mock_vehicle_repository.find_by_id.side_effect = lambda vid: vehicles.get(vid)

        # Act
        result, total = await use_case.execute()

        # Assert
        assert total == 2
        assert len(result) == 2
        assert result[0]["vehicle_plate"] == "ABC123"
        assert result[1]["vehicle_plate"] == "XYZ789"
        assert result[0]["estado_ruta"] == "planeada"
        assert result[1]["estado_ruta"] == "en_progreso"

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
            total_distance_km=Decimal("123.456"),
            total_orders=2,
        )

        mock_route_repository.find_all.return_value = ([route], 1)
        mock_vehicle_repository.find_by_id.return_value = Vehicle(
            id=vehicle_id, placa="TEST", driver_name="Test"
        )

        # Act
        result, total = await use_case.execute()

        # Assert
        assert isinstance(result[0]["total_distance_km"], float)
        assert result[0]["total_distance_km"] == 123.456

    @pytest.mark.asyncio
    async def test_execute_repository_error_propagates(
        self, use_case, mock_route_repository, mock_vehicle_repository
    ):
        """Test that repository errors are propagated correctly."""
        # Arrange
        mock_route_repository.find_all.side_effect = Exception("Database error")

        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            await use_case.execute()

        assert "Database error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_execute_vehicle_repository_error_propagates(
        self, use_case, mock_route_repository, mock_vehicle_repository
    ):
        """Test that vehicle repository errors are propagated."""
        # Arrange
        vehicle_id = uuid4()
        route = Route(
            id=uuid4(),
            vehicle_id=vehicle_id,
            fecha_ruta=date(2024, 1, 15),
            estado_ruta=RouteStatus.PLANEADA,
            duracion_estimada_minutos=60,
            total_distance_km=Decimal("20.0"),
            total_orders=2,
        )

        mock_route_repository.find_all.return_value = ([route], 1)
        mock_vehicle_repository.find_by_id.side_effect = Exception("Vehicle lookup error")

        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            await use_case.execute()

        assert "Vehicle lookup error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_execute_default_pagination(
        self, use_case, mock_route_repository, mock_vehicle_repository
    ):
        """Test that default pagination values are used."""
        # Arrange
        mock_route_repository.find_all.return_value = ([], 0)

        # Act
        await use_case.execute()

        # Assert
        mock_route_repository.find_all.assert_called_once_with(
            fecha_ruta=None,
            estado_ruta=None,
            page=1,
            page_size=20,
        )

    @pytest.mark.asyncio
    async def test_execute_different_route_statuses(
        self, use_case, mock_route_repository, mock_vehicle_repository
    ):
        """Test routes with different status values."""
        # Arrange
        vehicle_id = uuid4()
        vehicle = Vehicle(id=vehicle_id, placa="ABC123", driver_name="Driver")

        statuses = [
            RouteStatus.PLANEADA,
            RouteStatus.EN_PROGRESO,
            RouteStatus.COMPLETADA,
            RouteStatus.CANCELADA,
        ]

        routes = [
            Route(
                id=uuid4(),
                vehicle_id=vehicle_id,
                fecha_ruta=date(2024, 1, 15),
                estado_ruta=status,
                duracion_estimada_minutos=60,
                total_distance_km=Decimal("20.0"),
                total_orders=2,
            )
            for status in statuses
        ]

        mock_route_repository.find_all.return_value = (routes, len(routes))
        mock_vehicle_repository.find_by_id.return_value = vehicle

        # Act
        result, total = await use_case.execute()

        # Assert
        assert total == 4
        assert result[0]["estado_ruta"] == "planeada"
        assert result[1]["estado_ruta"] == "en_progreso"
        assert result[2]["estado_ruta"] == "completada"
        assert result[3]["estado_ruta"] == "cancelada"
