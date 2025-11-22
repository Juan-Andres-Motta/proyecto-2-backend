import pytest
from unittest.mock import AsyncMock
from uuid import uuid4

from src.application.use_cases.list_vehicles import ListVehiclesUseCase
from src.domain.entities import Vehicle


class TestListVehiclesUseCase:
    """Test suite for ListVehiclesUseCase."""

    @pytest.fixture
    def mock_vehicle_repository(self):
        """Create a mock vehicle repository."""
        return AsyncMock()

    @pytest.fixture
    def use_case(self, mock_vehicle_repository):
        """Create a ListVehiclesUseCase instance with mocked dependencies."""
        return ListVehiclesUseCase(vehicle_repository=mock_vehicle_repository)

    @pytest.mark.asyncio
    async def test_execute_returns_list_of_active_vehicles(
        self, use_case, mock_vehicle_repository
    ):
        """Test successful retrieval of active vehicles."""
        # Arrange
        vehicles = [
            Vehicle(
                id=uuid4(),
                placa="ABC123",
                driver_name="John Doe",
                driver_phone="+1234567890",
            ),
            Vehicle(
                id=uuid4(),
                placa="XYZ789",
                driver_name="Jane Smith",
                driver_phone="+0987654321",
            ),
        ]
        mock_vehicle_repository.find_all_active.return_value = vehicles

        # Act
        result = await use_case.execute()

        # Assert
        assert result == vehicles
        assert len(result) == 2
        mock_vehicle_repository.find_all_active.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_returns_empty_list_when_no_vehicles(
        self, use_case, mock_vehicle_repository
    ):
        """Test that empty list is returned when no active vehicles exist."""
        # Arrange
        mock_vehicle_repository.find_all_active.return_value = []

        # Act
        result = await use_case.execute()

        # Assert
        assert result == []
        assert len(result) == 0
        mock_vehicle_repository.find_all_active.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_returns_single_vehicle(
        self, use_case, mock_vehicle_repository
    ):
        """Test retrieval of a single active vehicle."""
        # Arrange
        vehicle = Vehicle(
            id=uuid4(),
            placa="ABC123",
            driver_name="John Doe",
        )
        mock_vehicle_repository.find_all_active.return_value = [vehicle]

        # Act
        result = await use_case.execute()

        # Assert
        assert len(result) == 1
        assert result[0] == vehicle
        assert result[0].placa == "ABC123"
        mock_vehicle_repository.find_all_active.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_returns_vehicles_with_all_fields(
        self, use_case, mock_vehicle_repository
    ):
        """Test that returned vehicles have all expected fields."""
        # Arrange
        vehicle_id = uuid4()
        vehicle = Vehicle(
            id=vehicle_id,
            placa="TEST123",
            driver_name="Test Driver",
            driver_phone="+5551234567",
            is_active=True,
        )
        mock_vehicle_repository.find_all_active.return_value = [vehicle]

        # Act
        result = await use_case.execute()

        # Assert
        assert len(result) == 1
        returned_vehicle = result[0]
        assert returned_vehicle.id == vehicle_id
        assert returned_vehicle.placa == "TEST123"
        assert returned_vehicle.driver_name == "Test Driver"
        assert returned_vehicle.driver_phone == "+5551234567"
        assert returned_vehicle.is_active is True

    @pytest.mark.asyncio
    async def test_execute_repository_error_propagates(
        self, use_case, mock_vehicle_repository
    ):
        """Test that repository errors are propagated correctly."""
        # Arrange
        mock_vehicle_repository.find_all_active.side_effect = Exception("Database error")

        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            await use_case.execute()

        assert "Database error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_execute_returns_vehicles_without_phone(
        self, use_case, mock_vehicle_repository
    ):
        """Test retrieval of vehicles without phone numbers."""
        # Arrange
        vehicle = Vehicle(
            id=uuid4(),
            placa="ABC123",
            driver_name="John Doe",
            driver_phone=None,
        )
        mock_vehicle_repository.find_all_active.return_value = [vehicle]

        # Act
        result = await use_case.execute()

        # Assert
        assert len(result) == 1
        assert result[0].driver_phone is None

    @pytest.mark.asyncio
    async def test_execute_returns_multiple_vehicles_in_order(
        self, use_case, mock_vehicle_repository
    ):
        """Test that multiple vehicles are returned in the same order as from repository."""
        # Arrange
        vehicles = [
            Vehicle(id=uuid4(), placa="A001", driver_name="Driver A"),
            Vehicle(id=uuid4(), placa="B002", driver_name="Driver B"),
            Vehicle(id=uuid4(), placa="C003", driver_name="Driver C"),
        ]
        mock_vehicle_repository.find_all_active.return_value = vehicles

        # Act
        result = await use_case.execute()

        # Assert
        assert len(result) == 3
        assert result[0].placa == "A001"
        assert result[1].placa == "B002"
        assert result[2].placa == "C003"
