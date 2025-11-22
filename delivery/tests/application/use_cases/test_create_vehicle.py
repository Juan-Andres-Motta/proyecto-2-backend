import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from src.application.use_cases.create_vehicle import CreateVehicleUseCase
from src.domain.entities import Vehicle
from src.domain.exceptions import ValidationError


class TestCreateVehicleUseCase:
    """Test suite for CreateVehicleUseCase."""

    @pytest.fixture
    def mock_vehicle_repository(self):
        """Create a mock vehicle repository."""
        return AsyncMock()

    @pytest.fixture
    def use_case(self, mock_vehicle_repository):
        """Create a CreateVehicleUseCase instance with mocked dependencies."""
        return CreateVehicleUseCase(vehicle_repository=mock_vehicle_repository)

    @pytest.mark.asyncio
    async def test_execute_success_with_all_fields(
        self, use_case, mock_vehicle_repository
    ):
        """Test successful vehicle creation with all fields provided."""
        # Arrange
        placa = "ABC123"
        driver_name = "John Doe"
        driver_phone = "+1234567890"

        mock_vehicle_repository.find_by_placa.return_value = None
        mock_vehicle_repository.save.return_value = None

        # Act
        result = await use_case.execute(
            placa=placa,
            driver_name=driver_name,
            driver_phone=driver_phone,
        )

        # Assert
        assert result is not None
        assert result.placa == placa
        assert result.driver_name == driver_name
        assert result.driver_phone == driver_phone
        assert result.is_active is True
        assert result.id is not None

        mock_vehicle_repository.find_by_placa.assert_called_once_with(placa)
        mock_vehicle_repository.save.assert_called_once()
        saved_vehicle = mock_vehicle_repository.save.call_args[0][0]
        assert saved_vehicle.placa == placa

    @pytest.mark.asyncio
    async def test_execute_success_without_driver_phone(
        self, use_case, mock_vehicle_repository
    ):
        """Test successful vehicle creation without optional driver_phone."""
        # Arrange
        placa = "XYZ789"
        driver_name = "Jane Smith"

        mock_vehicle_repository.find_by_placa.return_value = None
        mock_vehicle_repository.save.return_value = None

        # Act
        result = await use_case.execute(
            placa=placa,
            driver_name=driver_name,
        )

        # Assert
        assert result is not None
        assert result.placa == placa
        assert result.driver_name == driver_name
        assert result.driver_phone is None
        assert result.is_active is True

        mock_vehicle_repository.find_by_placa.assert_called_once_with(placa)
        mock_vehicle_repository.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_duplicate_placa_raises_validation_error(
        self, use_case, mock_vehicle_repository
    ):
        """Test that creating a vehicle with duplicate placa raises ValidationError."""
        # Arrange
        placa = "ABC123"
        driver_name = "John Doe"

        existing_vehicle = Vehicle(
            id=uuid4(),
            placa=placa,
            driver_name="Existing Driver",
        )
        mock_vehicle_repository.find_by_placa.return_value = existing_vehicle

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            await use_case.execute(
                placa=placa,
                driver_name=driver_name,
            )

        assert f"Vehicle with placa {placa} already exists" in str(exc_info.value)
        mock_vehicle_repository.find_by_placa.assert_called_once_with(placa)
        mock_vehicle_repository.save.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_generates_unique_id(
        self, use_case, mock_vehicle_repository
    ):
        """Test that each created vehicle gets a unique ID."""
        # Arrange
        mock_vehicle_repository.find_by_placa.return_value = None
        mock_vehicle_repository.save.return_value = None

        # Act
        result1 = await use_case.execute(
            placa="ABC123",
            driver_name="Driver 1",
        )

        mock_vehicle_repository.find_by_placa.return_value = None
        result2 = await use_case.execute(
            placa="XYZ789",
            driver_name="Driver 2",
        )

        # Assert
        assert result1.id != result2.id

    @pytest.mark.asyncio
    async def test_execute_with_empty_driver_phone(
        self, use_case, mock_vehicle_repository
    ):
        """Test vehicle creation with empty string for driver_phone."""
        # Arrange
        placa = "ABC123"
        driver_name = "John Doe"
        driver_phone = ""

        mock_vehicle_repository.find_by_placa.return_value = None
        mock_vehicle_repository.save.return_value = None

        # Act
        result = await use_case.execute(
            placa=placa,
            driver_name=driver_name,
            driver_phone=driver_phone,
        )

        # Assert
        assert result.driver_phone == ""
        mock_vehicle_repository.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_repository_save_called_with_correct_vehicle(
        self, use_case, mock_vehicle_repository
    ):
        """Test that repository save is called with the correct vehicle entity."""
        # Arrange
        placa = "TEST123"
        driver_name = "Test Driver"
        driver_phone = "+5551234567"

        mock_vehicle_repository.find_by_placa.return_value = None
        mock_vehicle_repository.save.return_value = None

        # Act
        result = await use_case.execute(
            placa=placa,
            driver_name=driver_name,
            driver_phone=driver_phone,
        )

        # Assert
        mock_vehicle_repository.save.assert_called_once()
        saved_vehicle = mock_vehicle_repository.save.call_args[0][0]

        assert isinstance(saved_vehicle, Vehicle)
        assert saved_vehicle.placa == placa
        assert saved_vehicle.driver_name == driver_name
        assert saved_vehicle.driver_phone == driver_phone
        assert saved_vehicle.id == result.id

    @pytest.mark.asyncio
    async def test_execute_repository_error_propagates(
        self, use_case, mock_vehicle_repository
    ):
        """Test that repository errors are propagated correctly."""
        # Arrange
        mock_vehicle_repository.find_by_placa.return_value = None
        mock_vehicle_repository.save.side_effect = Exception("Database error")

        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            await use_case.execute(
                placa="ABC123",
                driver_name="John Doe",
            )

        assert "Database error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_execute_find_by_placa_error_propagates(
        self, use_case, mock_vehicle_repository
    ):
        """Test that find_by_placa errors are propagated correctly."""
        # Arrange
        mock_vehicle_repository.find_by_placa.side_effect = Exception("Connection error")

        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            await use_case.execute(
                placa="ABC123",
                driver_name="John Doe",
            )

        assert "Connection error" in str(exc_info.value)
        mock_vehicle_repository.save.assert_not_called()
