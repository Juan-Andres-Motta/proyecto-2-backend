import pytest
from unittest.mock import AsyncMock
from uuid import uuid4
from datetime import date, datetime

from src.application.use_cases.update_shipment_status import UpdateShipmentStatusUseCase
from src.domain.entities import Shipment
from src.domain.value_objects import ShipmentStatus
from src.domain.exceptions import EntityNotFoundError, InvalidStatusTransitionError


class TestUpdateShipmentStatusUseCase:
    """Test suite for UpdateShipmentStatusUseCase."""

    @pytest.fixture
    def mock_shipment_repository(self):
        """Create a mock shipment repository."""
        return AsyncMock()

    @pytest.fixture
    def use_case(self, mock_shipment_repository):
        """Create an UpdateShipmentStatusUseCase instance with mocked dependencies."""
        return UpdateShipmentStatusUseCase(shipment_repository=mock_shipment_repository)

    def _create_shipment(self, order_id=None, status=ShipmentStatus.PENDING):
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
        # Set route assignment for non-pending statuses
        if status != ShipmentStatus.PENDING:
            shipment.route_id = uuid4()
            shipment.sequence_in_route = 1
        return shipment

    @pytest.mark.asyncio
    async def test_execute_mark_in_transit_success(
        self, use_case, mock_shipment_repository
    ):
        """Test successful transition to in_transit status."""
        # Arrange
        order_id = uuid4()
        shipment = self._create_shipment(
            order_id=order_id,
            status=ShipmentStatus.ASSIGNED_TO_ROUTE,
        )

        mock_shipment_repository.find_by_order_id.return_value = shipment
        mock_shipment_repository.update.return_value = None

        # Act
        result = await use_case.execute(order_id=order_id, new_status="in_transit")

        # Assert
        assert result.shipment_status == ShipmentStatus.IN_TRANSIT
        mock_shipment_repository.find_by_order_id.assert_called_once_with(order_id)
        mock_shipment_repository.update.assert_called_once_with(shipment)

    @pytest.mark.asyncio
    async def test_execute_mark_delivered_success(
        self, use_case, mock_shipment_repository
    ):
        """Test successful transition to delivered status."""
        # Arrange
        order_id = uuid4()
        shipment = self._create_shipment(
            order_id=order_id,
            status=ShipmentStatus.IN_TRANSIT,
        )

        mock_shipment_repository.find_by_order_id.return_value = shipment
        mock_shipment_repository.update.return_value = None

        # Act
        result = await use_case.execute(order_id=order_id, new_status="delivered")

        # Assert
        assert result.shipment_status == ShipmentStatus.DELIVERED
        mock_shipment_repository.update.assert_called_once_with(shipment)

    @pytest.mark.asyncio
    async def test_execute_shipment_not_found_raises_error(
        self, use_case, mock_shipment_repository
    ):
        """Test that EntityNotFoundError is raised when shipment not found."""
        # Arrange
        order_id = uuid4()
        mock_shipment_repository.find_by_order_id.return_value = None

        # Act & Assert
        with pytest.raises(EntityNotFoundError) as exc_info:
            await use_case.execute(order_id=order_id, new_status="in_transit")

        assert exc_info.value.entity_type == "Shipment"
        assert exc_info.value.entity_id == str(order_id)
        mock_shipment_repository.update.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_invalid_status_value_raises_error(
        self, use_case, mock_shipment_repository
    ):
        """Test that invalid status value raises ValueError."""
        # Arrange
        order_id = uuid4()
        shipment = self._create_shipment(order_id=order_id)
        mock_shipment_repository.find_by_order_id.return_value = shipment

        # Act & Assert
        with pytest.raises(ValueError):
            await use_case.execute(order_id=order_id, new_status="invalid_status")

        mock_shipment_repository.update.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_transition_to_pending_raises_error(
        self, use_case, mock_shipment_repository
    ):
        """Test that transitioning to pending raises InvalidStatusTransitionError."""
        # Arrange
        order_id = uuid4()
        shipment = self._create_shipment(
            order_id=order_id,
            status=ShipmentStatus.ASSIGNED_TO_ROUTE,
        )
        mock_shipment_repository.find_by_order_id.return_value = shipment

        # Act & Assert
        with pytest.raises(InvalidStatusTransitionError) as exc_info:
            await use_case.execute(order_id=order_id, new_status="pending")

        assert exc_info.value.entity_type == "Shipment"
        assert exc_info.value.current_status == "assigned_to_route"
        assert exc_info.value.target_status == "pending"
        mock_shipment_repository.update.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_transition_to_assigned_raises_error(
        self, use_case, mock_shipment_repository
    ):
        """Test that transitioning to assigned_to_route raises InvalidStatusTransitionError."""
        # Arrange
        order_id = uuid4()
        shipment = self._create_shipment(
            order_id=order_id,
            status=ShipmentStatus.IN_TRANSIT,
        )
        mock_shipment_repository.find_by_order_id.return_value = shipment

        # Act & Assert
        with pytest.raises(InvalidStatusTransitionError) as exc_info:
            await use_case.execute(order_id=order_id, new_status="assigned_to_route")

        assert exc_info.value.entity_type == "Shipment"
        mock_shipment_repository.update.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_invalid_in_transit_from_pending(
        self, use_case, mock_shipment_repository
    ):
        """Test that marking pending shipment as in_transit raises error."""
        # Arrange
        order_id = uuid4()
        shipment = self._create_shipment(
            order_id=order_id,
            status=ShipmentStatus.PENDING,
        )
        mock_shipment_repository.find_by_order_id.return_value = shipment

        # Act & Assert
        with pytest.raises(ValueError):
            await use_case.execute(order_id=order_id, new_status="in_transit")

        mock_shipment_repository.update.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_invalid_delivered_from_assigned(
        self, use_case, mock_shipment_repository
    ):
        """Test that marking assigned shipment as delivered raises error."""
        # Arrange
        order_id = uuid4()
        shipment = self._create_shipment(
            order_id=order_id,
            status=ShipmentStatus.ASSIGNED_TO_ROUTE,
        )
        mock_shipment_repository.find_by_order_id.return_value = shipment

        # Act & Assert
        with pytest.raises(ValueError):
            await use_case.execute(order_id=order_id, new_status="delivered")

        mock_shipment_repository.update.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_invalid_in_transit_from_delivered(
        self, use_case, mock_shipment_repository
    ):
        """Test that marking delivered shipment as in_transit raises error."""
        # Arrange
        order_id = uuid4()
        shipment = self._create_shipment(
            order_id=order_id,
            status=ShipmentStatus.DELIVERED,
        )
        mock_shipment_repository.find_by_order_id.return_value = shipment

        # Act & Assert
        with pytest.raises(ValueError):
            await use_case.execute(order_id=order_id, new_status="in_transit")

        mock_shipment_repository.update.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_repository_update_error_propagates(
        self, use_case, mock_shipment_repository
    ):
        """Test that repository update errors are propagated."""
        # Arrange
        order_id = uuid4()
        shipment = self._create_shipment(
            order_id=order_id,
            status=ShipmentStatus.ASSIGNED_TO_ROUTE,
        )
        mock_shipment_repository.find_by_order_id.return_value = shipment
        mock_shipment_repository.update.side_effect = Exception("Database error")

        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            await use_case.execute(order_id=order_id, new_status="in_transit")

        assert "Database error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_execute_repository_find_error_propagates(
        self, use_case, mock_shipment_repository
    ):
        """Test that repository find errors are propagated."""
        # Arrange
        order_id = uuid4()
        mock_shipment_repository.find_by_order_id.side_effect = Exception("Connection error")

        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            await use_case.execute(order_id=order_id, new_status="in_transit")

        assert "Connection error" in str(exc_info.value)
        mock_shipment_repository.update.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_returns_updated_shipment(
        self, use_case, mock_shipment_repository
    ):
        """Test that the updated shipment is returned."""
        # Arrange
        order_id = uuid4()
        shipment = self._create_shipment(
            order_id=order_id,
            status=ShipmentStatus.ASSIGNED_TO_ROUTE,
        )

        mock_shipment_repository.find_by_order_id.return_value = shipment
        mock_shipment_repository.update.return_value = None

        # Act
        result = await use_case.execute(order_id=order_id, new_status="in_transit")

        # Assert
        assert result is shipment
        assert result.order_id == order_id
        assert result.shipment_status == ShipmentStatus.IN_TRANSIT

    @pytest.mark.asyncio
    async def test_execute_complete_delivery_flow(
        self, use_case, mock_shipment_repository
    ):
        """Test complete delivery flow: assigned -> in_transit -> delivered."""
        # First transition: assigned_to_route -> in_transit
        order_id = uuid4()
        shipment = self._create_shipment(
            order_id=order_id,
            status=ShipmentStatus.ASSIGNED_TO_ROUTE,
        )

        mock_shipment_repository.find_by_order_id.return_value = shipment
        mock_shipment_repository.update.return_value = None

        result = await use_case.execute(order_id=order_id, new_status="in_transit")
        assert result.shipment_status == ShipmentStatus.IN_TRANSIT

        # Second transition: in_transit -> delivered
        result = await use_case.execute(order_id=order_id, new_status="delivered")
        assert result.shipment_status == ShipmentStatus.DELIVERED

    @pytest.mark.asyncio
    async def test_execute_uses_correct_order_id(
        self, use_case, mock_shipment_repository
    ):
        """Test that the correct order_id is used for lookup."""
        # Arrange
        order_id = uuid4()
        shipment = self._create_shipment(
            order_id=order_id,
            status=ShipmentStatus.ASSIGNED_TO_ROUTE,
        )

        mock_shipment_repository.find_by_order_id.return_value = shipment
        mock_shipment_repository.update.return_value = None

        # Act
        await use_case.execute(order_id=order_id, new_status="in_transit")

        # Assert
        mock_shipment_repository.find_by_order_id.assert_called_once_with(order_id)
        call_arg = mock_shipment_repository.find_by_order_id.call_args[0][0]
        assert call_arg == order_id
