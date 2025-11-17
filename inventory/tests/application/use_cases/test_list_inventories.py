import uuid
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock

import pytest

from src.application.use_cases.list_inventories import ListInventoriesUseCase
from src.domain.entities.inventory import Inventory


@pytest.mark.asyncio
async def test_list_inventories_use_case_empty():
    """Test list inventories use case with empty results."""
    mock_repository = AsyncMock()
    mock_repository.list_inventories = AsyncMock(return_value=([], 0))

    use_case = ListInventoriesUseCase(mock_repository)
    inventories, total = await use_case.execute(limit=10, offset=0)

    assert len(inventories) == 0
    assert total == 0
    mock_repository.list_inventories.assert_called_once_with(
        limit=10, offset=0, product_id=None, warehouse_id=None, sku=None, category=None, name=None
    )


@pytest.mark.asyncio
async def test_list_inventories_use_case_with_data():
    """Test list inventories use case with data."""
    mock_repository = AsyncMock()

    product_id = uuid.uuid4()
    warehouse_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    mock_inventories = []
    for i in range(3):
        inventory = Inventory(
            id=uuid.uuid4(),
            product_id=product_id,
            warehouse_id=warehouse_id,
            total_quantity=100 + i,
            reserved_quantity=10 + i,
            batch_number=f"BATCH00{i}",
            expiration_date=datetime(2026, 12, 31, tzinfo=timezone.utc),
            product_sku=f"SKU-00{i}",
            product_name=f"Product {i}",
            product_price=Decimal("10.50"),
            product_category="medicamentos_especiales",
            warehouse_name="Test Warehouse",
            warehouse_city="Test City",
            warehouse_country="Colombia",
            created_at=now,
            updated_at=now,
        )
        mock_inventories.append(inventory)

    mock_repository.list_inventories = AsyncMock(return_value=(mock_inventories, 3))

    use_case = ListInventoriesUseCase(mock_repository)
    inventories, total = await use_case.execute(limit=10, offset=0)

    assert len(inventories) == 3
    assert total == 3
    mock_repository.list_inventories.assert_called_once_with(
        limit=10, offset=0, product_id=None, warehouse_id=None, sku=None, category=None, name=None
    )


@pytest.mark.asyncio
async def test_list_inventories_use_case_default_pagination():
    """Test list inventories use case with default pagination."""
    mock_repository = AsyncMock()
    mock_repository.list_inventories = AsyncMock(return_value=([], 0))

    use_case = ListInventoriesUseCase(mock_repository)
    await use_case.execute()

    mock_repository.list_inventories.assert_called_once_with(
        limit=10, offset=0, product_id=None, warehouse_id=None, sku=None, category=None, name=None
    )


@pytest.mark.asyncio
async def test_list_inventories_use_case_with_offset():
    """Test list inventories use case with offset pagination."""
    mock_repository = AsyncMock()
    mock_repository.list_inventories = AsyncMock(return_value=([], 0))

    use_case = ListInventoriesUseCase(mock_repository)
    await use_case.execute(limit=5, offset=10)

    mock_repository.list_inventories.assert_called_once_with(
        limit=5, offset=10, product_id=None, warehouse_id=None, sku=None, category=None, name=None
    )


@pytest.mark.asyncio
async def test_list_inventories_use_case_limit_exceeds_total():
    """Test list inventories use case when limit exceeds total."""
    mock_repository = AsyncMock()

    product_id = uuid.uuid4()
    warehouse_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    mock_inventories = [
        Inventory(
            id=uuid.uuid4(),
            product_id=product_id,
            warehouse_id=warehouse_id,
            total_quantity=100,
            reserved_quantity=10,
            batch_number="BATCH001",
            expiration_date=datetime(2026, 12, 31, tzinfo=timezone.utc),
            product_sku="SKU-001",
            product_name="Product 1",
            product_price=Decimal("10.50"),
            product_category="medicamentos_especiales",
            warehouse_name="Test Warehouse",
            warehouse_city="Test City",
            warehouse_country="Colombia",
            created_at=now,
            updated_at=now,
        )
    ]

    mock_repository.list_inventories = AsyncMock(return_value=(mock_inventories, 1))

    use_case = ListInventoriesUseCase(mock_repository)
    inventories, total = await use_case.execute(limit=100, offset=0)

    assert len(inventories) == 1
    assert total == 1


@pytest.mark.asyncio
async def test_list_inventories_use_case_with_product_id_filter():
    """Test list inventories use case with product_id filter."""
    mock_repository = AsyncMock()
    mock_repository.list_inventories = AsyncMock(return_value=([], 0))

    product_id = uuid.uuid4()
    use_case = ListInventoriesUseCase(mock_repository)
    await use_case.execute(product_id=product_id)

    mock_repository.list_inventories.assert_called_once_with(
        limit=10, offset=0, product_id=product_id, warehouse_id=None, sku=None, category=None, name=None
    )


@pytest.mark.asyncio
async def test_list_inventories_use_case_with_warehouse_id_filter():
    """Test list inventories use case with warehouse_id filter."""
    mock_repository = AsyncMock()
    mock_repository.list_inventories = AsyncMock(return_value=([], 0))

    warehouse_id = uuid.uuid4()
    use_case = ListInventoriesUseCase(mock_repository)
    await use_case.execute(warehouse_id=warehouse_id)

    mock_repository.list_inventories.assert_called_once_with(
        limit=10, offset=0, product_id=None, warehouse_id=warehouse_id, sku=None, category=None, name=None
    )


@pytest.mark.asyncio
async def test_list_inventories_use_case_with_sku_filter():
    """Test list inventories use case with sku filter."""
    mock_repository = AsyncMock()
    mock_repository.list_inventories = AsyncMock(return_value=([], 0))

    use_case = ListInventoriesUseCase(mock_repository)
    await use_case.execute(sku="MED-001")

    mock_repository.list_inventories.assert_called_once_with(
        limit=10, offset=0, product_id=None, warehouse_id=None, sku="MED-001", category=None, name=None
    )


@pytest.mark.asyncio
async def test_list_inventories_use_case_with_category_filter():
    """Test list inventories use case with category filter."""
    mock_repository = AsyncMock()
    mock_repository.list_inventories = AsyncMock(return_value=([], 0))

    use_case = ListInventoriesUseCase(mock_repository)
    await use_case.execute(category="medicamentos_especiales")

    mock_repository.list_inventories.assert_called_once_with(
        limit=10, offset=0, product_id=None, warehouse_id=None, sku=None, category="medicamentos_especiales", name=None
    )


@pytest.mark.asyncio
async def test_list_inventories_use_case_with_all_filters():
    """Test list inventories use case with all filters combined."""
    mock_repository = AsyncMock()
    mock_repository.list_inventories = AsyncMock(return_value=([], 0))

    product_id = uuid.uuid4()
    warehouse_id = uuid.uuid4()
    use_case = ListInventoriesUseCase(mock_repository)
    await use_case.execute(
        limit=20,
        offset=10,
        product_id=product_id,
        warehouse_id=warehouse_id,
        sku="MED-001",
        category="insumos_quirurgicos"
    )

    mock_repository.list_inventories.assert_called_once_with(
        limit=20,
        offset=10,
        product_id=product_id,
        warehouse_id=warehouse_id,
        sku="MED-001",
        category="insumos_quirurgicos",
        name=None
    )


@pytest.mark.asyncio
async def test_list_inventories_use_case_returns_domain_entities():
    """Test that list inventories returns domain entities."""
    mock_repository = AsyncMock()

    product_id = uuid.uuid4()
    warehouse_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    inventory = Inventory(
        id=uuid.uuid4(),
        product_id=product_id,
        warehouse_id=warehouse_id,
        total_quantity=100,
        reserved_quantity=10,
        batch_number="BATCH001",
        expiration_date=datetime(2026, 12, 31, tzinfo=timezone.utc),
        product_sku="MED-001",
        product_name="Aspirin 100mg",
        product_price=Decimal("10.50"),
        product_category="medicamentos_especiales",
        warehouse_name="Lima Central",
        warehouse_city="Lima",
        warehouse_country="Colombia",
        created_at=now,
        updated_at=now,
    )

    mock_repository.list_inventories = AsyncMock(return_value=([inventory], 1))

    use_case = ListInventoriesUseCase(mock_repository)
    inventories, total = await use_case.execute()

    assert len(inventories) == 1
    assert total == 1
    assert inventories[0].product_category == "medicamentos_especiales"
    assert inventories[0].product_sku == "MED-001"
    assert inventories[0].warehouse_name == "Lima Central"


# ======================== NAME FILTER TESTS ========================


@pytest.mark.asyncio
async def test_list_inventories_use_case_with_name_filter():
    """Test list inventories use case with name filter."""
    mock_repository = AsyncMock()
    mock_repository.list_inventories = AsyncMock(return_value=([], 0))

    use_case = ListInventoriesUseCase(mock_repository)
    await use_case.execute(name="Aspirin")

    mock_repository.list_inventories.assert_called_once_with(
        limit=10, offset=0, product_id=None, warehouse_id=None, sku=None, category=None, name="Aspirin"
    )


@pytest.mark.asyncio
async def test_list_inventories_use_case_with_name_filter_partial_match():
    """Test list inventories use case with name filter using partial match (e.g., 'asp' matches 'Aspirin')."""
    mock_repository = AsyncMock()

    product_id = uuid.uuid4()
    warehouse_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    aspirin_inventory = Inventory(
        id=uuid.uuid4(),
        product_id=product_id,
        warehouse_id=warehouse_id,
        total_quantity=100,
        reserved_quantity=10,
        batch_number="BATCH001",
        expiration_date=datetime(2026, 12, 31, tzinfo=timezone.utc),
        product_sku="MED-001",
        product_name="Aspirin 100mg",
        product_price=Decimal("10.50"),
        product_category="medicamentos_especiales",
        warehouse_name="Lima Central",
        warehouse_city="Lima",
        warehouse_country="Colombia",
        created_at=now,
        updated_at=now,
    )

    mock_repository.list_inventories = AsyncMock(return_value=([aspirin_inventory], 1))

    use_case = ListInventoriesUseCase(mock_repository)
    inventories, total = await use_case.execute(name="asp")

    assert len(inventories) == 1
    assert total == 1
    assert inventories[0].product_name == "Aspirin 100mg"
    mock_repository.list_inventories.assert_called_once_with(
        limit=10, offset=0, product_id=None, warehouse_id=None, sku=None, category=None, name="asp"
    )


@pytest.mark.asyncio
async def test_list_inventories_use_case_with_name_filter_case_insensitive():
    """Test that name filter is case-insensitive (ILIKE behavior)."""
    mock_repository = AsyncMock()

    product_id = uuid.uuid4()
    warehouse_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    aspirin_inventory = Inventory(
        id=uuid.uuid4(),
        product_id=product_id,
        warehouse_id=warehouse_id,
        total_quantity=100,
        reserved_quantity=10,
        batch_number="BATCH001",
        expiration_date=datetime(2026, 12, 31, tzinfo=timezone.utc),
        product_sku="MED-001",
        product_name="Aspirin 100mg",
        product_price=Decimal("10.50"),
        product_category="medicamentos_especiales",
        warehouse_name="Lima Central",
        warehouse_city="Lima",
        warehouse_country="Colombia",
        created_at=now,
        updated_at=now,
    )

    mock_repository.list_inventories = AsyncMock(return_value=([aspirin_inventory], 1))

    use_case = ListInventoriesUseCase(mock_repository)
    # Test with uppercase query on product with mixed case name
    inventories, total = await use_case.execute(name="ASPIRIN")

    assert len(inventories) == 1
    assert total == 1
    assert inventories[0].product_name == "Aspirin 100mg"
    mock_repository.list_inventories.assert_called_once_with(
        limit=10, offset=0, product_id=None, warehouse_id=None, sku=None, category=None, name="ASPIRIN"
    )


@pytest.mark.asyncio
async def test_list_inventories_use_case_with_name_filter_no_results():
    """Test name filter returns empty results when no matches found."""
    mock_repository = AsyncMock()
    mock_repository.list_inventories = AsyncMock(return_value=([], 0))

    use_case = ListInventoriesUseCase(mock_repository)
    inventories, total = await use_case.execute(name="NonexistentProduct")

    assert len(inventories) == 0
    assert total == 0
    mock_repository.list_inventories.assert_called_once_with(
        limit=10, offset=0, product_id=None, warehouse_id=None, sku=None, category=None, name="NonexistentProduct"
    )


@pytest.mark.asyncio
async def test_list_inventories_use_case_with_name_filter_multiple_results():
    """Test name filter returns multiple results when multiple products match."""
    mock_repository = AsyncMock()

    product_id = uuid.uuid4()
    warehouse_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    # Create multiple inventories with names matching "Vitamin"
    vitamin_inventories = []
    for i in range(3):
        vitamin_inventories.append(
            Inventory(
                id=uuid.uuid4(),
                product_id=product_id,
                warehouse_id=warehouse_id,
                total_quantity=100 + i,
                reserved_quantity=10 + i,
                batch_number=f"BATCH00{i}",
                expiration_date=datetime(2026, 12, 31, tzinfo=timezone.utc),
                product_sku=f"VIT-{i:03d}",
                product_name=f"Vitamin C {100 + (i * 50)}mg",
                product_price=Decimal("15.50"),
                product_category="vitaminas",
                warehouse_name="Lima Central",
                warehouse_city="Lima",
                warehouse_country="Colombia",
                created_at=now,
                updated_at=now,
            )
        )

    mock_repository.list_inventories = AsyncMock(return_value=(vitamin_inventories, 3))

    use_case = ListInventoriesUseCase(mock_repository)
    inventories, total = await use_case.execute(name="Vitamin")

    assert len(inventories) == 3
    assert total == 3
    assert all("Vitamin" in inv.product_name for inv in inventories)
    mock_repository.list_inventories.assert_called_once_with(
        limit=10, offset=0, product_id=None, warehouse_id=None, sku=None, category=None, name="Vitamin"
    )


@pytest.mark.asyncio
async def test_list_inventories_use_case_with_name_filter_and_pagination():
    """Test name filter works correctly with pagination (limit/offset)."""
    mock_repository = AsyncMock()

    product_id = uuid.uuid4()
    warehouse_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    # Create inventories matching "Medicine"
    medicine_inventories = [
        Inventory(
            id=uuid.uuid4(),
            product_id=product_id,
            warehouse_id=warehouse_id,
            total_quantity=100,
            reserved_quantity=10,
            batch_number="BATCH001",
            expiration_date=datetime(2026, 12, 31, tzinfo=timezone.utc),
            product_sku="MED-001",
            product_name="Medicine A",
            product_price=Decimal("10.50"),
            product_category="medicamentos_generales",
            warehouse_name="Lima Central",
            warehouse_city="Lima",
            warehouse_country="Colombia",
            created_at=now,
            updated_at=now,
        ),
        Inventory(
            id=uuid.uuid4(),
            product_id=product_id,
            warehouse_id=warehouse_id,
            total_quantity=150,
            reserved_quantity=20,
            batch_number="BATCH002",
            expiration_date=datetime(2026, 12, 31, tzinfo=timezone.utc),
            product_sku="MED-002",
            product_name="Medicine B",
            product_price=Decimal("12.75"),
            product_category="medicamentos_generales",
            warehouse_name="Lima Central",
            warehouse_city="Lima",
            warehouse_country="Colombia",
            created_at=now,
            updated_at=now,
        ),
    ]

    # Return only the first page with 1 item per page
    mock_repository.list_inventories = AsyncMock(return_value=([medicine_inventories[0]], 2))

    use_case = ListInventoriesUseCase(mock_repository)
    inventories, total = await use_case.execute(name="Medicine", limit=1, offset=0)

    assert len(inventories) == 1
    assert total == 2
    assert inventories[0].product_name == "Medicine A"
    mock_repository.list_inventories.assert_called_once_with(
        limit=1, offset=0, product_id=None, warehouse_id=None, sku=None, category=None, name="Medicine"
    )


@pytest.mark.asyncio
async def test_list_inventories_use_case_with_name_filter_pagination_second_page():
    """Test name filter with pagination on second page."""
    mock_repository = AsyncMock()

    product_id = uuid.uuid4()
    warehouse_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    # Create inventory for second page
    medicine_inventory = Inventory(
        id=uuid.uuid4(),
        product_id=product_id,
        warehouse_id=warehouse_id,
        total_quantity=150,
        reserved_quantity=20,
        batch_number="BATCH002",
        expiration_date=datetime(2026, 12, 31, tzinfo=timezone.utc),
        product_sku="MED-002",
        product_name="Medicine B",
        product_price=Decimal("12.75"),
        product_category="medicamentos_generales",
        warehouse_name="Lima Central",
        warehouse_city="Lima",
        warehouse_country="Colombia",
        created_at=now,
        updated_at=now,
    )

    # Return only the second page item
    mock_repository.list_inventories = AsyncMock(return_value=([medicine_inventory], 2))

    use_case = ListInventoriesUseCase(mock_repository)
    inventories, total = await use_case.execute(name="Medicine", limit=1, offset=1)

    assert len(inventories) == 1
    assert total == 2
    assert inventories[0].product_name == "Medicine B"
    mock_repository.list_inventories.assert_called_once_with(
        limit=1, offset=1, product_id=None, warehouse_id=None, sku=None, category=None, name="Medicine"
    )


@pytest.mark.asyncio
async def test_list_inventories_use_case_with_name_and_other_filters():
    """Test name filter combined with other filters."""
    mock_repository = AsyncMock()

    product_id = uuid.uuid4()
    warehouse_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    inventory = Inventory(
        id=uuid.uuid4(),
        product_id=product_id,
        warehouse_id=warehouse_id,
        total_quantity=100,
        reserved_quantity=10,
        batch_number="BATCH001",
        expiration_date=datetime(2026, 12, 31, tzinfo=timezone.utc),
        product_sku="ASP-001",
        product_name="Aspirin 500mg",
        product_price=Decimal("10.50"),
        product_category="medicamentos_generales",
        warehouse_name="Lima Central",
        warehouse_city="Lima",
        warehouse_country="Colombia",
        created_at=now,
        updated_at=now,
    )

    mock_repository.list_inventories = AsyncMock(return_value=([inventory], 1))

    use_case = ListInventoriesUseCase(mock_repository)
    inventories, total = await use_case.execute(
        name="Aspirin",
        sku="ASP-001",
        category="medicamentos_generales",
        product_id=product_id,
        warehouse_id=warehouse_id,
    )

    assert len(inventories) == 1
    assert total == 1
    assert inventories[0].product_name == "Aspirin 500mg"
    mock_repository.list_inventories.assert_called_once_with(
        limit=10,
        offset=0,
        product_id=product_id,
        warehouse_id=warehouse_id,
        sku="ASP-001",
        category="medicamentos_generales",
        name="Aspirin",
    )


@pytest.mark.asyncio
async def test_list_inventories_use_case_with_name_filter_whitespace():
    """Test name filter with whitespace in the query."""
    mock_repository = AsyncMock()

    product_id = uuid.uuid4()
    warehouse_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    inventory = Inventory(
        id=uuid.uuid4(),
        product_id=product_id,
        warehouse_id=warehouse_id,
        total_quantity=100,
        reserved_quantity=10,
        batch_number="BATCH001",
        expiration_date=datetime(2026, 12, 31, tzinfo=timezone.utc),
        product_sku="IBUPF-001",
        product_name="Ibuprofen 400mg",
        product_price=Decimal("10.50"),
        product_category="medicamentos_generales",
        warehouse_name="Lima Central",
        warehouse_city="Lima",
        warehouse_country="Colombia",
        created_at=now,
        updated_at=now,
    )

    mock_repository.list_inventories = AsyncMock(return_value=([inventory], 1))

    use_case = ListInventoriesUseCase(mock_repository)
    # Test with whitespace in query
    inventories, total = await use_case.execute(name="Ibuprofen 400")

    assert len(inventories) == 1
    assert total == 1
    assert inventories[0].product_name == "Ibuprofen 400mg"
    mock_repository.list_inventories.assert_called_once_with(
        limit=10, offset=0, product_id=None, warehouse_id=None, sku=None, category=None, name="Ibuprofen 400"
    )


@pytest.mark.asyncio
async def test_list_inventories_use_case_with_name_filter_special_characters():
    """Test name filter with special characters in product name."""
    mock_repository = AsyncMock()

    product_id = uuid.uuid4()
    warehouse_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    # Product name with special characters (e.g., parentheses, hyphens)
    inventory = Inventory(
        id=uuid.uuid4(),
        product_id=product_id,
        warehouse_id=warehouse_id,
        total_quantity=100,
        reserved_quantity=10,
        batch_number="BATCH001",
        expiration_date=datetime(2026, 12, 31, tzinfo=timezone.utc),
        product_sku="VIT-B12",
        product_name="Vitamin B12 (Cyanocobalamin) - 1000mg",
        product_price=Decimal("15.75"),
        product_category="vitaminas",
        warehouse_name="Lima Central",
        warehouse_city="Lima",
        warehouse_country="Colombia",
        created_at=now,
        updated_at=now,
    )

    mock_repository.list_inventories = AsyncMock(return_value=([inventory], 1))

    use_case = ListInventoriesUseCase(mock_repository)
    # Test with partial match including special characters
    inventories, total = await use_case.execute(name="Cyanocobalamin")

    assert len(inventories) == 1
    assert total == 1
    assert "Cyanocobalamin" in inventories[0].product_name
    mock_repository.list_inventories.assert_called_once_with(
        limit=10, offset=0, product_id=None, warehouse_id=None, sku=None, category=None, name="Cyanocobalamin"
    )


@pytest.mark.asyncio
async def test_list_inventories_use_case_with_empty_name_filter():
    """Test name filter with empty string (should be treated as None)."""
    mock_repository = AsyncMock()
    mock_repository.list_inventories = AsyncMock(return_value=([], 0))

    use_case = ListInventoriesUseCase(mock_repository)
    # Empty string should still be passed to repository
    await use_case.execute(name="")

    mock_repository.list_inventories.assert_called_once_with(
        limit=10, offset=0, product_id=None, warehouse_id=None, sku=None, category=None, name=""
    )


@pytest.mark.asyncio
async def test_list_inventories_use_case_name_filter_middle_of_string():
    """Test name filter matches text in middle of product name."""
    mock_repository = AsyncMock()

    product_id = uuid.uuid4()
    warehouse_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    inventory = Inventory(
        id=uuid.uuid4(),
        product_id=product_id,
        warehouse_id=warehouse_id,
        total_quantity=100,
        reserved_quantity=10,
        batch_number="BATCH001",
        expiration_date=datetime(2026, 12, 31, tzinfo=timezone.utc),
        product_sku="PARACET-500",
        product_name="Paracetamol 500mg Tablets",
        product_price=Decimal("8.50"),
        product_category="medicamentos_generales",
        warehouse_name="Lima Central",
        warehouse_city="Lima",
        warehouse_country="Colombia",
        created_at=now,
        updated_at=now,
    )

    mock_repository.list_inventories = AsyncMock(return_value=([inventory], 1))

    use_case = ListInventoriesUseCase(mock_repository)
    # Test matching text in the middle of product name
    inventories, total = await use_case.execute(name="cetamol")

    assert len(inventories) == 1
    assert total == 1
    assert "cetamol" in inventories[0].product_name.lower()
    mock_repository.list_inventories.assert_called_once_with(
        limit=10, offset=0, product_id=None, warehouse_id=None, sku=None, category=None, name="cetamol"
    )


@pytest.mark.asyncio
async def test_list_inventories_use_case_name_filter_end_of_string():
    """Test name filter matches text at end of product name."""
    mock_repository = AsyncMock()

    product_id = uuid.uuid4()
    warehouse_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    inventory = Inventory(
        id=uuid.uuid4(),
        product_id=product_id,
        warehouse_id=warehouse_id,
        total_quantity=50,
        reserved_quantity=5,
        batch_number="BATCH001",
        expiration_date=datetime(2026, 12, 31, tzinfo=timezone.utc),
        product_sku="DIPYRONE-500",
        product_name="Dipyrone 500mg Capsules",
        product_price=Decimal("7.25"),
        product_category="medicamentos_generales",
        warehouse_name="Lima Central",
        warehouse_city="Lima",
        warehouse_country="Colombia",
        created_at=now,
        updated_at=now,
    )

    mock_repository.list_inventories = AsyncMock(return_value=([inventory], 1))

    use_case = ListInventoriesUseCase(mock_repository)
    # Test matching text at the end of product name
    inventories, total = await use_case.execute(name="Capsules")

    assert len(inventories) == 1
    assert total == 1
    assert inventories[0].product_name.endswith("Capsules")
    mock_repository.list_inventories.assert_called_once_with(
        limit=10, offset=0, product_id=None, warehouse_id=None, sku=None, category=None, name="Capsules"
    )
