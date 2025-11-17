"""Unit tests for GetInventoryUseCase."""
import pytest
from uuid import uuid4
from unittest.mock import AsyncMock
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from src.application.use_cases.get_inventory import GetInventoryUseCase
from src.domain.entities.inventory import Inventory
from src.domain.exceptions import InventoryNotFoundException


@pytest.fixture
def mock_repository():
    """Create mock repository."""
    return AsyncMock()


@pytest.fixture
def sample_inventory():
    """Create sample inventory entity."""
    return Inventory(
        id=uuid4(),
        product_id=uuid4(),
        warehouse_id=uuid4(),
        total_quantity=100,
        reserved_quantity=20,
        product_name="Aspirin 100mg",
        product_sku="MED-001",
        product_price=Decimal("10.50"),
        product_category="medicamentos_especiales",
        warehouse_name="Lima Central",
        warehouse_city="Lima",
        warehouse_country="Colombia",
        batch_number="BATCH-001",
        expiration_date=datetime.now(timezone.utc) + timedelta(days=180),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


@pytest.mark.asyncio
async def test_get_inventory_success(mock_repository, sample_inventory):
    """Test successfully retrieving inventory by ID."""
    # Setup
    inventory_id = sample_inventory.id
    mock_repository.find_by_id.return_value = sample_inventory

    use_case = GetInventoryUseCase(repository=mock_repository)

    # Execute
    result = await use_case.execute(inventory_id)

    # Assert
    assert result == sample_inventory
    assert result.id == inventory_id
    assert result.total_quantity == 100
    assert result.reserved_quantity == 20
    # Verify available_quantity computation
    assert result.total_quantity - result.reserved_quantity == 80

    # Verify repository was called correctly
    mock_repository.find_by_id.assert_called_once_with(inventory_id)


@pytest.mark.asyncio
async def test_get_inventory_not_found(mock_repository):
    """Test getting inventory that doesn't exist raises InventoryNotFoundException."""
    # Setup
    inventory_id = uuid4()
    mock_repository.find_by_id.return_value = None

    use_case = GetInventoryUseCase(repository=mock_repository)

    # Execute & Assert
    with pytest.raises(InventoryNotFoundException) as exc_info:
        await use_case.execute(inventory_id)

    # Verify exception message contains inventory_id
    assert str(inventory_id) in str(exc_info.value)

    # Verify repository was called
    mock_repository.find_by_id.assert_called_once_with(inventory_id)


@pytest.mark.asyncio
async def test_get_inventory_with_zero_available_quantity(mock_repository):
    """Test getting inventory with zero available quantity (all reserved)."""
    # Setup - all inventory is reserved
    inventory = Inventory(
        id=uuid4(),
        product_id=uuid4(),
        warehouse_id=uuid4(),
        total_quantity=50,
        reserved_quantity=50,  # All reserved
        product_name="Out of Stock Product",
        product_sku="OUT-001",
        product_price=Decimal("5.00"),
        product_category="medicamentos_basicos",
        warehouse_name="Bogota Warehouse",
        warehouse_city="Bogota",
        warehouse_country="Colombia",
        batch_number="BATCH-002",
        expiration_date=datetime.now(timezone.utc) + timedelta(days=90),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    mock_repository.find_by_id.return_value = inventory
    use_case = GetInventoryUseCase(repository=mock_repository)

    # Execute
    result = await use_case.execute(inventory.id)

    # Assert - should still return the inventory even with 0 available
    assert result == inventory
    assert result.total_quantity == 50
    assert result.reserved_quantity == 50
    assert result.total_quantity - result.reserved_quantity == 0


@pytest.mark.asyncio
async def test_get_inventory_with_full_stock(mock_repository):
    """Test getting inventory with full available stock (nothing reserved)."""
    # Setup - nothing reserved
    inventory = Inventory(
        id=uuid4(),
        product_id=uuid4(),
        warehouse_id=uuid4(),
        total_quantity=200,
        reserved_quantity=0,  # Nothing reserved
        product_name="Full Stock Product",
        product_sku="FULL-001",
        product_price=Decimal("15.00"),
        product_category="medicamentos_especiales",
        warehouse_name="Lima Warehouse",
        warehouse_city="Lima",
        warehouse_country="Colombia",
        batch_number="BATCH-003",
        expiration_date=datetime.now(timezone.utc) + timedelta(days=365),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    mock_repository.find_by_id.return_value = inventory
    use_case = GetInventoryUseCase(repository=mock_repository)

    # Execute
    result = await use_case.execute(inventory.id)

    # Assert
    assert result == inventory
    assert result.total_quantity == 200
    assert result.reserved_quantity == 0
    assert result.total_quantity - result.reserved_quantity == 200
