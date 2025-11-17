"""Tests for InventoryRepository to achieve full code coverage."""

import pytest
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from src.adapters.output.repositories.inventory_repository import InventoryRepository
from src.domain.entities.inventory import Inventory as DomainInventory
from src.domain.exceptions import (
    InsufficientInventoryException,
    InvalidReservationReleaseException,
    InventoryNotFoundException,
)
from src.infrastructure.database.models.inventory import Inventory as ORMInventory


def _create_mock_orm_inventory(inventory_id=None):
    """Helper to create a mock ORM inventory."""
    mock = MagicMock(spec=ORMInventory)
    mock.id = inventory_id or uuid.uuid4()
    mock.product_id = uuid.uuid4()
    mock.warehouse_id = uuid.uuid4()
    mock.total_quantity = 100
    mock.reserved_quantity = 20
    mock.batch_number = "BATCH-001"
    mock.expiration_date = datetime.now(timezone.utc)
    mock.product_sku = "MED-001"
    mock.product_name = "Test Product"
    mock.product_price = Decimal("10.00")
    mock.product_category = "medicamentos_especiales"
    mock.warehouse_name = "Test Warehouse"
    mock.warehouse_city = "Test City"
    mock.warehouse_country = "Colombia"
    mock.created_at = datetime.now(timezone.utc)
    mock.updated_at = datetime.now(timezone.utc)
    return mock


class TestInventoryRepositoryUpdateReservedQuantity:
    """Test update_reserved_quantity method for full coverage."""

    @pytest.mark.asyncio
    async def test_update_reserved_quantity_not_found(self):
        """Test update_reserved_quantity when inventory not found."""
        # Given
        mock_session = AsyncMock(spec=AsyncSession)
        mock_scalars = MagicMock()
        mock_scalars.first.return_value = None
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute = AsyncMock(return_value=mock_result)

        repository = InventoryRepository(mock_session)
        inventory_id = uuid.uuid4()

        # When/Then
        with pytest.raises(InventoryNotFoundException):
            await repository.update_reserved_quantity(inventory_id, 10)

    @pytest.mark.asyncio
    async def test_update_reserved_quantity_with_insufficient_inventory(self):
        """Test that update_reserved_quantity raises when insufficient inventory."""
        # Given
        mock_session = AsyncMock(spec=AsyncSession)
        mock_orm_inventory = _create_mock_orm_inventory()
        mock_orm_inventory.reserved_quantity = 80  # 20 available

        mock_scalars = MagicMock()
        mock_scalars.first.return_value = mock_orm_inventory
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute = AsyncMock(return_value=mock_result)

        repository = InventoryRepository(mock_session)

        # When/Then - Try to reserve more than available
        with pytest.raises(InsufficientInventoryException) as exc_info:
            await repository.update_reserved_quantity(mock_orm_inventory.id, 30)

        assert exc_info.value.requested == 30
        assert exc_info.value.available == 20

    @pytest.mark.asyncio
    async def test_update_reserved_quantity_with_invalid_release(self):
        """Test that update_reserved_quantity raises when invalid release."""
        # Given
        mock_session = AsyncMock(spec=AsyncSession)
        mock_orm_inventory = _create_mock_orm_inventory()
        mock_orm_inventory.reserved_quantity = 20

        mock_scalars = MagicMock()
        mock_scalars.first.return_value = mock_orm_inventory
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute = AsyncMock(return_value=mock_result)

        repository = InventoryRepository(mock_session)

        # When/Then - Try to release more than reserved
        with pytest.raises(InvalidReservationReleaseException) as exc_info:
            await repository.update_reserved_quantity(mock_orm_inventory.id, -30)

        assert exc_info.value.requested_release == 30
        assert exc_info.value.currently_reserved == 20

    @pytest.mark.asyncio
    async def test_update_reserved_quantity_successful_reserve(self):
        """Test successful reserve operation."""
        # Given
        mock_session = AsyncMock(spec=AsyncSession)
        mock_orm_inventory = _create_mock_orm_inventory()

        mock_scalars = MagicMock()
        mock_scalars.first.return_value = mock_orm_inventory
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock()

        repository = InventoryRepository(mock_session)

        # When
        result = await repository.update_reserved_quantity(mock_orm_inventory.id, 10)

        # Then
        assert isinstance(result, DomainInventory)
        assert result.id == mock_orm_inventory.id
        assert mock_orm_inventory.reserved_quantity == 30  # 20 + 10
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_reserved_quantity_successful_release(self):
        """Test successful release operation."""
        # Given
        mock_session = AsyncMock(spec=AsyncSession)
        mock_orm_inventory = _create_mock_orm_inventory()
        mock_orm_inventory.reserved_quantity = 40

        mock_scalars = MagicMock()
        mock_scalars.first.return_value = mock_orm_inventory
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock()

        repository = InventoryRepository(mock_session)

        # When
        result = await repository.update_reserved_quantity(mock_orm_inventory.id, -15)

        # Then
        assert isinstance(result, DomainInventory)
        assert mock_orm_inventory.reserved_quantity == 25  # 40 - 15
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_reserved_quantity_exception_causes_rollback(self):
        """Test that exceptions during update cause rollback."""
        # Given
        mock_session = AsyncMock(spec=AsyncSession)
        mock_orm_inventory = _create_mock_orm_inventory()

        mock_scalars = MagicMock()
        mock_scalars.first.return_value = mock_orm_inventory
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.commit = AsyncMock(side_effect=Exception("DB Error"))
        mock_session.rollback = AsyncMock()

        repository = InventoryRepository(mock_session)

        # When/Then
        with pytest.raises(Exception):
            await repository.update_reserved_quantity(mock_orm_inventory.id, 10)

        # Verify rollback was called
        mock_session.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_to_domain_conversion(self):
        """Test _to_domain static method conversion."""
        # Given
        orm_inventory = _create_mock_orm_inventory()

        # When
        domain_inventory = InventoryRepository._to_domain(orm_inventory)

        # Then
        assert domain_inventory.id == orm_inventory.id
        assert domain_inventory.product_id == orm_inventory.product_id
        assert domain_inventory.warehouse_id == orm_inventory.warehouse_id
        assert domain_inventory.total_quantity == orm_inventory.total_quantity
        assert domain_inventory.reserved_quantity == orm_inventory.reserved_quantity
        assert domain_inventory.batch_number == orm_inventory.batch_number
        assert domain_inventory.product_sku == orm_inventory.product_sku
        assert domain_inventory.product_name == orm_inventory.product_name
        assert domain_inventory.product_category == orm_inventory.product_category
        assert domain_inventory.warehouse_name == orm_inventory.warehouse_name

    @pytest.mark.asyncio
    async def test_find_by_id_with_none_result(self):
        """Test find_by_id returns None when not found."""
        # Given
        mock_session = AsyncMock(spec=AsyncSession)
        mock_scalars = MagicMock()
        mock_scalars.first.return_value = None
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute = AsyncMock(return_value=mock_result)

        repository = InventoryRepository(mock_session)
        inventory_id = uuid.uuid4()

        # When
        result = await repository.find_by_id(inventory_id)

        # Then
        assert result is None

    @pytest.mark.asyncio
    async def test_list_inventories_returns_empty(self):
        """Test list_inventories returns empty list when no results."""
        # Given
        mock_session = AsyncMock(spec=AsyncSession)

        # Mock count query - return 0 count
        count_result = MagicMock()
        count_result.scalar.return_value = 0

        # Mock list query - return empty list
        list_result = MagicMock()
        list_scalars = MagicMock()
        list_scalars.all.return_value = []
        list_result.scalars.return_value = list_scalars

        mock_session.execute = AsyncMock(side_effect=[count_result, list_result])

        repository = InventoryRepository(mock_session)

        # When
        inventories, total = await repository.list_inventories()

        # Then
        assert inventories == []
        assert total == 0
