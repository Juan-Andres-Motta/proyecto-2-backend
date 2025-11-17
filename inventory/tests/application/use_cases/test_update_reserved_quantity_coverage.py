"""Tests for UpdateReservedQuantityUseCase for full coverage."""

import pytest
from uuid import uuid4
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock

from src.application.use_cases.update_reserved_quantity import (
    UpdateReservedQuantityUseCase,
)
from src.domain.entities.inventory import Inventory as DomainInventory
from src.domain.exceptions import (
    InsufficientInventoryException,
    InvalidReservationReleaseException,
    InventoryNotFoundException,
)


class TestUpdateReservedQuantityUseCase:
    """Test suite for UpdateReservedQuantityUseCase."""

    def _create_mock_inventory(self, inventory_id, reserved=20):
        """Helper to create a mock domain inventory."""
        return DomainInventory(
            id=inventory_id,
            product_id=uuid4(),
            warehouse_id=uuid4(),
            total_quantity=100,
            reserved_quantity=reserved,
            batch_number="BATCH-001",
            expiration_date=datetime.now(timezone.utc),
            product_sku="MED-001",
            product_name="Test Product",
            product_price=Decimal("10.00"),
            product_category="medicamentos_especiales",
            warehouse_name="Test Warehouse",
            warehouse_city="Test City",
            warehouse_country="Colombia",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

    @pytest.mark.asyncio
    async def test_execute_reserve_successfully(self):
        """Test successfully reserving inventory."""
        # Given
        inventory_id = uuid4()
        mock_inventory = self._create_mock_inventory(inventory_id, reserved=20)
        mock_repository = AsyncMock()
        mock_repository.update_reserved_quantity = AsyncMock(
            return_value=mock_inventory
        )

        use_case = UpdateReservedQuantityUseCase(mock_repository)

        # When
        result = await use_case.execute(inventory_id, 10)

        # Then
        assert result == mock_inventory
        mock_repository.update_reserved_quantity.assert_called_once_with(
            inventory_id, 10
        )

    @pytest.mark.asyncio
    async def test_execute_release_successfully(self):
        """Test successfully releasing inventory."""
        # Given
        inventory_id = uuid4()
        mock_inventory = self._create_mock_inventory(inventory_id, reserved=20)
        mock_repository = AsyncMock()
        mock_repository.update_reserved_quantity = AsyncMock(
            return_value=mock_inventory
        )

        use_case = UpdateReservedQuantityUseCase(mock_repository)

        # When
        result = await use_case.execute(inventory_id, -5)

        # Then
        assert result == mock_inventory
        mock_repository.update_reserved_quantity.assert_called_once_with(
            inventory_id, -5
        )

    @pytest.mark.asyncio
    async def test_execute_raises_insufficient_inventory_exception(self):
        """Test that execute propagates InsufficientInventoryException."""
        # Given
        inventory_id = uuid4()
        mock_repository = AsyncMock()
        mock_repository.update_reserved_quantity = AsyncMock(
            side_effect=InsufficientInventoryException(
                inventory_id=inventory_id,
                requested=150,
                available=50,
                product_sku="MED-001",
            )
        )

        use_case = UpdateReservedQuantityUseCase(mock_repository)

        # When/Then
        with pytest.raises(InsufficientInventoryException) as exc_info:
            await use_case.execute(inventory_id, 150)

        assert exc_info.value.inventory_id == inventory_id
        assert exc_info.value.requested == 150
        assert exc_info.value.available == 50

    @pytest.mark.asyncio
    async def test_execute_raises_invalid_release_exception(self):
        """Test that execute propagates InvalidReservationReleaseException."""
        # Given
        inventory_id = uuid4()
        mock_repository = AsyncMock()
        mock_repository.update_reserved_quantity = AsyncMock(
            side_effect=InvalidReservationReleaseException(
                requested_release=50, currently_reserved=20
            )
        )

        use_case = UpdateReservedQuantityUseCase(mock_repository)

        # When/Then
        with pytest.raises(InvalidReservationReleaseException) as exc_info:
            await use_case.execute(inventory_id, -50)

        assert exc_info.value.requested_release == 50
        assert exc_info.value.currently_reserved == 20

    @pytest.mark.asyncio
    async def test_execute_raises_inventory_not_found_exception(self):
        """Test that execute propagates InventoryNotFoundException."""
        # Given
        inventory_id = uuid4()
        mock_repository = AsyncMock()
        mock_repository.update_reserved_quantity = AsyncMock(
            side_effect=InventoryNotFoundException(inventory_id=inventory_id)
        )

        use_case = UpdateReservedQuantityUseCase(mock_repository)

        # When/Then
        with pytest.raises(InventoryNotFoundException):
            await use_case.execute(inventory_id, 10)

    @pytest.mark.asyncio
    async def test_execute_with_large_positive_delta(self):
        """Test execute with large positive quantity delta."""
        # Given
        inventory_id = uuid4()
        mock_inventory = self._create_mock_inventory(inventory_id, reserved=0)
        mock_repository = AsyncMock()
        mock_repository.update_reserved_quantity = AsyncMock(
            return_value=mock_inventory
        )

        use_case = UpdateReservedQuantityUseCase(mock_repository)

        # When
        result = await use_case.execute(inventory_id, 500)

        # Then
        assert result == mock_inventory
        mock_repository.update_reserved_quantity.assert_called_once_with(
            inventory_id, 500
        )

    @pytest.mark.asyncio
    async def test_execute_with_large_negative_delta(self):
        """Test execute with large negative quantity delta."""
        # Given
        inventory_id = uuid4()
        mock_inventory = self._create_mock_inventory(inventory_id, reserved=100)
        mock_repository = AsyncMock()
        mock_repository.update_reserved_quantity = AsyncMock(
            return_value=mock_inventory
        )

        use_case = UpdateReservedQuantityUseCase(mock_repository)

        # When
        result = await use_case.execute(inventory_id, -50)

        # Then
        assert result == mock_inventory
        mock_repository.update_reserved_quantity.assert_called_once_with(
            inventory_id, -50
        )

    @pytest.mark.asyncio
    async def test_execute_returns_domain_inventory(self):
        """Test that execute returns DomainInventory instance."""
        # Given
        inventory_id = uuid4()
        mock_inventory = self._create_mock_inventory(inventory_id)
        mock_repository = AsyncMock()
        mock_repository.update_reserved_quantity = AsyncMock(
            return_value=mock_inventory
        )

        use_case = UpdateReservedQuantityUseCase(mock_repository)

        # When
        result = await use_case.execute(inventory_id, 10)

        # Then
        assert isinstance(result, DomainInventory)
        assert result.id == inventory_id
        assert result.total_quantity == 100
        assert result.product_sku == "MED-001"
        assert result.product_category == "medicamentos_especiales"

    @pytest.mark.asyncio
    async def test_repository_called_with_exact_parameters(self):
        """Test that repository is called with exact parameters."""
        # Given
        inventory_id = uuid4()
        quantity_delta = 25
        mock_inventory = self._create_mock_inventory(inventory_id)
        mock_repository = AsyncMock()
        mock_repository.update_reserved_quantity = AsyncMock(
            return_value=mock_inventory
        )

        use_case = UpdateReservedQuantityUseCase(mock_repository)

        # When
        await use_case.execute(inventory_id, quantity_delta)

        # Then - Verify exact parameters passed
        call_args = mock_repository.update_reserved_quantity.call_args
        assert call_args[0][0] == inventory_id
        assert call_args[0][1] == quantity_delta

    @pytest.mark.asyncio
    async def test_execute_with_zero_delta(self):
        """Test execute with zero delta (edge case)."""
        # Given
        inventory_id = uuid4()
        mock_inventory = self._create_mock_inventory(inventory_id)
        mock_repository = AsyncMock()
        mock_repository.update_reserved_quantity = AsyncMock(
            return_value=mock_inventory
        )

        use_case = UpdateReservedQuantityUseCase(mock_repository)

        # When - Zero delta is allowed at use case level
        result = await use_case.execute(inventory_id, 0)

        # Then
        assert result == mock_inventory
        mock_repository.update_reserved_quantity.assert_called_once_with(
            inventory_id, 0
        )
