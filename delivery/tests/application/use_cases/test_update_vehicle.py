import pytest
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from src.application.use_cases.update_vehicle import UpdateVehicleUseCase
from src.domain.entities import Vehicle
from src.domain.exceptions import EntityNotFoundError


class TestUpdateVehicleUseCase:
    """Test suite for UpdateVehicleUseCase."""

    @pytest.fixture
    def mock_vehicle_repository(self):
        """Create a mock vehicle repository."""
        return AsyncMock()

    @pytest.fixture
    def use_case(self, mock_vehicle_repository):
        """Create an UpdateVehicleUseCase instance with mocked dependencies."""
        return UpdateVehicleUseCase(vehicle_repository=mock_vehicle_repository)

    @pytest.mark.asyncio
    async def test_execute_update_driver_name(
        self, use_case, mock_vehicle_repository
    ):
        """Test successful update of driver name."""
        # Arrange
        vehicle_id = uuid4()
        existing_vehicle = Vehicle(
            id=vehicle_id,
            placa="ABC123",
            driver_name="Old Name",
            driver_phone="+1234567890",
        )
        mock_vehicle_repository.find_by_id.return_value = existing_vehicle
        mock_vehicle_repository.update.return_value = None

        new_driver_name = "New Name"

        # Act
        result = await use_case.execute(
            vehicle_id=vehicle_id,
            driver_name=new_driver_name,
        )

        # Assert
        assert result.driver_name == new_driver_name
        assert result.driver_phone == "+1234567890"  # Unchanged
        mock_vehicle_repository.find_by_id.assert_called_once_with(vehicle_id)
        mock_vehicle_repository.update.assert_called_once_with(existing_vehicle)

    @pytest.mark.asyncio
    async def test_execute_update_driver_phone(
        self, use_case, mock_vehicle_repository
    ):
        """Test successful update of driver phone."""
        # Arrange
        vehicle_id = uuid4()
        existing_vehicle = Vehicle(
            id=vehicle_id,
            placa="ABC123",
            driver_name="John Doe",
            driver_phone="+1234567890",
        )
        mock_vehicle_repository.find_by_id.return_value = existing_vehicle
        mock_vehicle_repository.update.return_value = None

        new_driver_phone = "+0987654321"

        # Act
        result = await use_case.execute(
            vehicle_id=vehicle_id,
            driver_phone=new_driver_phone,
        )

        # Assert
        assert result.driver_phone == new_driver_phone
        assert result.driver_name == "John Doe"  # Unchanged
        mock_vehicle_repository.find_by_id.assert_called_once_with(vehicle_id)
        mock_vehicle_repository.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_update_both_fields(
        self, use_case, mock_vehicle_repository
    ):
        """Test successful update of both driver name and phone."""
        # Arrange
        vehicle_id = uuid4()
        existing_vehicle = Vehicle(
            id=vehicle_id,
            placa="ABC123",
            driver_name="Old Name",
            driver_phone="+1234567890",
        )
        mock_vehicle_repository.find_by_id.return_value = existing_vehicle
        mock_vehicle_repository.update.return_value = None

        new_driver_name = "New Name"
        new_driver_phone = "+0987654321"

        # Act
        result = await use_case.execute(
            vehicle_id=vehicle_id,
            driver_name=new_driver_name,
            driver_phone=new_driver_phone,
        )

        # Assert
        assert result.driver_name == new_driver_name
        assert result.driver_phone == new_driver_phone
        mock_vehicle_repository.update.assert_called_once()

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
            await use_case.execute(
                vehicle_id=vehicle_id,
                driver_name="New Name",
            )

        assert exc_info.value.entity_type == "Vehicle"
        assert exc_info.value.entity_id == str(vehicle_id)
        mock_vehicle_repository.find_by_id.assert_called_once_with(vehicle_id)
        mock_vehicle_repository.update.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_no_updates_provided(
        self, use_case, mock_vehicle_repository
    ):
        """Test execution when no update fields are provided."""
        # Arrange
        vehicle_id = uuid4()
        existing_vehicle = Vehicle(
            id=vehicle_id,
            placa="ABC123",
            driver_name="John Doe",
            driver_phone="+1234567890",
        )
        mock_vehicle_repository.find_by_id.return_value = existing_vehicle
        mock_vehicle_repository.update.return_value = None

        # Act
        result = await use_case.execute(vehicle_id=vehicle_id)

        # Assert
        assert result.driver_name == "John Doe"
        assert result.driver_phone == "+1234567890"
        mock_vehicle_repository.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_update_phone_to_none(
        self, use_case, mock_vehicle_repository
    ):
        """Test updating phone to None (clearing the field)."""
        # Arrange
        vehicle_id = uuid4()
        existing_vehicle = Vehicle(
            id=vehicle_id,
            placa="ABC123",
            driver_name="John Doe",
            driver_phone="+1234567890",
        )
        mock_vehicle_repository.find_by_id.return_value = existing_vehicle
        mock_vehicle_repository.update.return_value = None

        # Act - Note: None means "no update", so phone won't change
        # To clear the phone, we'd pass empty string
        result = await use_case.execute(
            vehicle_id=vehicle_id,
            driver_phone=None,
        )

        # Assert - Phone remains unchanged because None means no update
        assert result.driver_phone == "+1234567890"

    @pytest.mark.asyncio
    async def test_execute_update_phone_to_empty_string(
        self, use_case, mock_vehicle_repository
    ):
        """Test updating phone to empty string."""
        # Arrange
        vehicle_id = uuid4()
        existing_vehicle = Vehicle(
            id=vehicle_id,
            placa="ABC123",
            driver_name="John Doe",
            driver_phone="+1234567890",
        )
        mock_vehicle_repository.find_by_id.return_value = existing_vehicle
        mock_vehicle_repository.update.return_value = None

        # Act
        result = await use_case.execute(
            vehicle_id=vehicle_id,
            driver_phone="",
        )

        # Assert
        assert result.driver_phone == ""
        mock_vehicle_repository.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_repository_update_error_propagates(
        self, use_case, mock_vehicle_repository
    ):
        """Test that repository update errors are propagated."""
        # Arrange
        vehicle_id = uuid4()
        existing_vehicle = Vehicle(
            id=vehicle_id,
            placa="ABC123",
            driver_name="John Doe",
        )
        mock_vehicle_repository.find_by_id.return_value = existing_vehicle
        mock_vehicle_repository.update.side_effect = Exception("Database error")

        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            await use_case.execute(
                vehicle_id=vehicle_id,
                driver_name="New Name",
            )

        assert "Database error" in str(exc_info.value)

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
            await use_case.execute(
                vehicle_id=vehicle_id,
                driver_name="New Name",
            )

        assert "Connection error" in str(exc_info.value)
        mock_vehicle_repository.update.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_returns_updated_vehicle_entity(
        self, use_case, mock_vehicle_repository
    ):
        """Test that the returned vehicle is the updated entity."""
        # Arrange
        vehicle_id = uuid4()
        existing_vehicle = Vehicle(
            id=vehicle_id,
            placa="ABC123",
            driver_name="Old Name",
            driver_phone="+1234567890",
        )
        mock_vehicle_repository.find_by_id.return_value = existing_vehicle
        mock_vehicle_repository.update.return_value = None

        # Act
        result = await use_case.execute(
            vehicle_id=vehicle_id,
            driver_name="Updated Name",
        )

        # Assert
        assert result is existing_vehicle  # Same instance
        assert result.id == vehicle_id
        assert result.placa == "ABC123"  # Placa never changes
        assert result.driver_name == "Updated Name"

    @pytest.mark.asyncio
    async def test_execute_empty_driver_name_raises_error(
        self, use_case, mock_vehicle_repository
    ):
        """Test that empty driver name raises ValueError from entity."""
        # Arrange
        vehicle_id = uuid4()
        existing_vehicle = Vehicle(
            id=vehicle_id,
            placa="ABC123",
            driver_name="John Doe",
        )
        mock_vehicle_repository.find_by_id.return_value = existing_vehicle

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            await use_case.execute(
                vehicle_id=vehicle_id,
                driver_name="",
            )

        assert "driver_name cannot be empty" in str(exc_info.value)
        mock_vehicle_repository.update.assert_not_called()
