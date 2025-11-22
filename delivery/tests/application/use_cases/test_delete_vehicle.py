import pytest
from unittest.mock import AsyncMock
from uuid import uuid4

from src.application.use_cases.delete_vehicle import DeleteVehicleUseCase
from src.domain.entities import Vehicle
from src.domain.exceptions import EntityNotFoundError


class TestDeleteVehicleUseCase:
    """Test suite for DeleteVehicleUseCase."""

    @pytest.fixture
    def mock_vehicle_repository(self):
        """Create a mock vehicle repository."""
        return AsyncMock()

    @pytest.fixture
    def use_case(self, mock_vehicle_repository):
        """Create a DeleteVehicleUseCase instance with mocked dependencies."""
        return DeleteVehicleUseCase(vehicle_repository=mock_vehicle_repository)

    @pytest.mark.asyncio
    async def test_execute_success(
        self, use_case, mock_vehicle_repository
    ):
        """Test successful vehicle deletion."""
        # Arrange
        vehicle_id = uuid4()
        existing_vehicle = Vehicle(
            id=vehicle_id,
            placa="ABC123",
            driver_name="John Doe",
            driver_phone="+1234567890",
        )
        mock_vehicle_repository.find_by_id.return_value = existing_vehicle
        mock_vehicle_repository.delete.return_value = None

        # Act
        result = await use_case.execute(vehicle_id=vehicle_id)

        # Assert
        assert result is None
        mock_vehicle_repository.find_by_id.assert_called_once_with(vehicle_id)
        mock_vehicle_repository.delete.assert_called_once_with(vehicle_id)

    @pytest.mark.asyncio
    async def test_execute_vehicle_not_found_raises_error(
        self, use_case, mock_vehicle_repository
    ):
        """Test that EntityNotFoundError is raised when vehicle not found."""
        # Arrange
        vehicle_id = uuid4()
        mock_vehicle_repository.find_by_id.return_value = None

        # Act & Assert
        with pytest.raises(EntityNotFoundError) as exc_info:
            await use_case.execute(vehicle_id=vehicle_id)

        assert exc_info.value.entity_type == "Vehicle"
        assert exc_info.value.entity_id == str(vehicle_id)
        mock_vehicle_repository.find_by_id.assert_called_once_with(vehicle_id)
        mock_vehicle_repository.delete.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_repository_delete_error_propagates(
        self, use_case, mock_vehicle_repository
    ):
        """Test that repository delete errors are propagated."""
        # Arrange
        vehicle_id = uuid4()
        existing_vehicle = Vehicle(
            id=vehicle_id,
            placa="ABC123",
            driver_name="John Doe",
        )
        mock_vehicle_repository.find_by_id.return_value = existing_vehicle
        mock_vehicle_repository.delete.side_effect = Exception("Database error")

        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            await use_case.execute(vehicle_id=vehicle_id)

        assert "Database error" in str(exc_info.value)
        mock_vehicle_repository.find_by_id.assert_called_once_with(vehicle_id)
        mock_vehicle_repository.delete.assert_called_once_with(vehicle_id)

    @pytest.mark.asyncio
    async def test_execute_repository_find_error_propagates(
        self, use_case, mock_vehicle_repository
    ):
        """Test that repository find errors are propagated."""
        # Arrange
        vehicle_id = uuid4()
        mock_vehicle_repository.find_by_id.side_effect = Exception("Connection error")

        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            await use_case.execute(vehicle_id=vehicle_id)

        assert "Connection error" in str(exc_info.value)
        mock_vehicle_repository.delete.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_returns_none_on_success(
        self, use_case, mock_vehicle_repository
    ):
        """Test that successful deletion returns None."""
        # Arrange
        vehicle_id = uuid4()
        existing_vehicle = Vehicle(
            id=vehicle_id,
            placa="XYZ789",
            driver_name="Jane Smith",
        )
        mock_vehicle_repository.find_by_id.return_value = existing_vehicle
        mock_vehicle_repository.delete.return_value = None

        # Act
        result = await use_case.execute(vehicle_id=vehicle_id)

        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_execute_delete_called_with_correct_id(
        self, use_case, mock_vehicle_repository
    ):
        """Test that delete is called with the correct vehicle ID."""
        # Arrange
        vehicle_id = uuid4()
        existing_vehicle = Vehicle(
            id=vehicle_id,
            placa="TEST123",
            driver_name="Test Driver",
        )
        mock_vehicle_repository.find_by_id.return_value = existing_vehicle
        mock_vehicle_repository.delete.return_value = None

        # Act
        await use_case.execute(vehicle_id=vehicle_id)

        # Assert
        mock_vehicle_repository.delete.assert_called_once_with(vehicle_id)
        # Verify the exact UUID was passed
        call_args = mock_vehicle_repository.delete.call_args[0]
        assert call_args[0] == vehicle_id

    @pytest.mark.asyncio
    async def test_execute_with_different_vehicle_ids(
        self, use_case, mock_vehicle_repository
    ):
        """Test deletion with multiple different vehicle IDs."""
        # First deletion
        vehicle_id_1 = uuid4()
        vehicle_1 = Vehicle(id=vehicle_id_1, placa="A001", driver_name="Driver A")
        mock_vehicle_repository.find_by_id.return_value = vehicle_1
        mock_vehicle_repository.delete.return_value = None

        await use_case.execute(vehicle_id=vehicle_id_1)
        mock_vehicle_repository.delete.assert_called_with(vehicle_id_1)

        # Reset mock
        mock_vehicle_repository.reset_mock()

        # Second deletion
        vehicle_id_2 = uuid4()
        vehicle_2 = Vehicle(id=vehicle_id_2, placa="B002", driver_name="Driver B")
        mock_vehicle_repository.find_by_id.return_value = vehicle_2

        await use_case.execute(vehicle_id=vehicle_id_2)
        mock_vehicle_repository.delete.assert_called_with(vehicle_id_2)
