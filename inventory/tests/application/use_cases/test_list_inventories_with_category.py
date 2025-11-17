"""Unit tests for ListInventoriesUseCase with category filtering.

Tests the list inventories use case including:
- Listing with category filter
- Listing without category filter
- Empty results handling
- Pagination with category filter
"""
import pytest
from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4
from unittest.mock import AsyncMock

from src.application.use_cases.list_inventories import ListInventoriesUseCase
from src.domain.entities.inventory import Inventory


@pytest.mark.asyncio
class TestListInventoriesUseCase:
    """Test suite for ListInventoriesUseCase with category filtering."""

    async def test_should_list_inventories_with_category_filter(self):
        """Test listing inventories filtered by category."""
        # Given
        now = datetime.now(timezone.utc)

        inventory1 = Inventory(
            id=uuid4(),
            product_id=uuid4(),
            warehouse_id=uuid4(),
            total_quantity=100,
            reserved_quantity=0,
            batch_number="BATCH-001",
            expiration_date=now,
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

        mock_repository = AsyncMock()
        mock_repository.list_inventories.return_value = ([inventory1], 1)

        use_case = ListInventoriesUseCase(mock_repository)

        # When
        inventories, total = await use_case.execute(
            category="medicamentos_especiales"
        )

        # Then
        assert total == 1
        assert len(inventories) == 1
        assert inventories[0].product_category == "medicamentos_especiales"
        mock_repository.list_inventories.assert_called_once_with(
            limit=10,
            offset=0,
            product_id=None,
            warehouse_id=None,
            sku=None,
            category="medicamentos_especiales",
            name=None,
        )

    async def test_should_list_all_inventories_when_no_category_filter(self):
        """Test listing all inventories when no category filter provided."""
        # Given
        now = datetime.now(timezone.utc)

        inventory1 = Inventory(
            id=uuid4(),
            product_id=uuid4(),
            warehouse_id=uuid4(),
            total_quantity=100,
            reserved_quantity=0,
            batch_number="BATCH-001",
            expiration_date=now,
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

        inventory2 = Inventory(
            id=uuid4(),
            product_id=uuid4(),
            warehouse_id=uuid4(),
            total_quantity=50,
            reserved_quantity=0,
            batch_number="BATCH-002",
            expiration_date=now,
            product_sku="SURG-001",
            product_name="Surgical Mask",
            product_price=Decimal("5.00"),
            product_category="insumos_quirurgicos",
            warehouse_name="Cusco Warehouse",
            warehouse_city="Cusco",
            warehouse_country="Colombia",
            created_at=now,
            updated_at=now,
        )

        mock_repository = AsyncMock()
        mock_repository.list_inventories.return_value = ([inventory1, inventory2], 2)

        use_case = ListInventoriesUseCase(mock_repository)

        # When
        inventories, total = await use_case.execute()

        # Then
        assert total == 2
        assert len(inventories) == 2
        categories = {inv.product_category for inv in inventories}
        assert "medicamentos_especiales" in categories
        assert "insumos_quirurgicos" in categories
        mock_repository.list_inventories.assert_called_once_with(
            limit=10,
            offset=0,
            product_id=None,
            warehouse_id=None,
            sku=None,
            category=None,
            name=None,
        )

    async def test_should_return_empty_list_when_no_inventories_match_category(self):
        """Test that empty list is returned when category has no matches."""
        # Given
        mock_repository = AsyncMock()
        mock_repository.list_inventories.return_value = ([], 0)

        use_case = ListInventoriesUseCase(mock_repository)

        # When
        inventories, total = await use_case.execute(
            category="equipos_biomedicos"
        )

        # Then
        assert total == 0
        assert len(inventories) == 0
        mock_repository.list_inventories.assert_called_once()

    async def test_should_combine_category_filter_with_pagination(self):
        """Test combining category filter with pagination parameters."""
        # Given
        now = datetime.now(timezone.utc)

        inventories = [
            Inventory(
                id=uuid4(),
                product_id=uuid4(),
                warehouse_id=uuid4(),
                total_quantity=100,
                reserved_quantity=0,
                batch_number=f"BATCH-{i:03d}",
                expiration_date=now,
                product_sku=f"MED-{i:03d}",
                product_name=f"Product {i}",
                product_price=Decimal("10.50"),
                product_category="medicamentos_especiales",
                warehouse_name="Lima Central",
                warehouse_city="Lima",
                warehouse_country="Colombia",
                created_at=now,
                updated_at=now,
            )
            for i in range(5)  # 5 inventories
        ]

        mock_repository = AsyncMock()
        mock_repository.list_inventories.return_value = (inventories, 15)  # 15 total

        use_case = ListInventoriesUseCase(mock_repository)

        # When
        result_inventories, total = await use_case.execute(
            limit=5,
            offset=10,
            category="medicamentos_especiales"
        )

        # Then
        assert total == 15
        assert len(result_inventories) == 5
        mock_repository.list_inventories.assert_called_once_with(
            limit=5,
            offset=10,
            product_id=None,
            warehouse_id=None,
            sku=None,
            category="medicamentos_especiales",
            name=None,
        )

    async def test_should_combine_category_filter_with_other_filters(self):
        """Test combining category filter with product_id and warehouse_id filters."""
        # Given
        product_id = uuid4()
        warehouse_id = uuid4()
        now = datetime.now(timezone.utc)

        inventory = Inventory(
            id=uuid4(),
            product_id=product_id,
            warehouse_id=warehouse_id,
            total_quantity=100,
            reserved_quantity=0,
            batch_number="BATCH-001",
            expiration_date=now,
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

        mock_repository = AsyncMock()
        mock_repository.list_inventories.return_value = ([inventory], 1)

        use_case = ListInventoriesUseCase(mock_repository)

        # When
        inventories, total = await use_case.execute(
            product_id=product_id,
            warehouse_id=warehouse_id,
            category="medicamentos_especiales"
        )

        # Then
        assert total == 1
        assert len(inventories) == 1
        mock_repository.list_inventories.assert_called_once_with(
            limit=10,
            offset=0,
            product_id=product_id,
            warehouse_id=warehouse_id,
            sku=None,
            category="medicamentos_especiales",
            name=None,
        )

    async def test_should_filter_by_sku_and_category_together(self):
        """Test filtering by both SKU and category simultaneously."""
        # Given
        now = datetime.now(timezone.utc)

        inventory = Inventory(
            id=uuid4(),
            product_id=uuid4(),
            warehouse_id=uuid4(),
            total_quantity=100,
            reserved_quantity=0,
            batch_number="BATCH-001",
            expiration_date=now,
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

        mock_repository = AsyncMock()
        mock_repository.list_inventories.return_value = ([inventory], 1)

        use_case = ListInventoriesUseCase(mock_repository)

        # When
        inventories, total = await use_case.execute(
            sku="MED-001",
            category="medicamentos_especiales"
        )

        # Then
        assert total == 1
        assert len(inventories) == 1
        assert inventories[0].product_sku == "MED-001"
        assert inventories[0].product_category == "medicamentos_especiales"
        mock_repository.list_inventories.assert_called_once_with(
            limit=10,
            offset=0,
            product_id=None,
            warehouse_id=None,
            sku="MED-001",
            category="medicamentos_especiales",
            name=None,
        )

    async def test_should_use_default_pagination_when_not_specified(self):
        """Test that default pagination values are used when not specified."""
        # Given
        mock_repository = AsyncMock()
        mock_repository.list_inventories.return_value = ([], 0)

        use_case = ListInventoriesUseCase(mock_repository)

        # When
        await use_case.execute()

        # Then - Should use default limit=10, offset=0
        mock_repository.list_inventories.assert_called_once_with(
            limit=10,
            offset=0,
            product_id=None,
            warehouse_id=None,
            sku=None,
            category=None,
            name=None,
        )

    async def test_should_handle_large_result_sets_with_category_filter(self):
        """Test handling large result sets when filtering by category."""
        # Given
        now = datetime.now(timezone.utc)

        inventories = [
            Inventory(
                id=uuid4(),
                product_id=uuid4(),
                warehouse_id=uuid4(),
                total_quantity=100,
                reserved_quantity=0,
                batch_number=f"BATCH-{i:03d}",
                expiration_date=now,
                product_sku=f"MED-{i:03d}",
                product_name=f"Product {i}",
                product_price=Decimal("10.50"),
                product_category="medicamentos_especiales",
                warehouse_name="Lima Central",
                warehouse_city="Lima",
                warehouse_country="Colombia",
                created_at=now,
                updated_at=now,
            )
            for i in range(100)  # 100 inventories returned
        ]

        mock_repository = AsyncMock()
        mock_repository.list_inventories.return_value = (inventories, 500)  # 500 total

        use_case = ListInventoriesUseCase(mock_repository)

        # When
        result_inventories, total = await use_case.execute(
            limit=100,
            category="medicamentos_especiales"
        )

        # Then
        assert total == 500
        assert len(result_inventories) == 100

    async def test_should_pass_through_all_filter_parameters_to_repository(self):
        """Test that all filter parameters are correctly passed to repository."""
        # Given
        product_id = uuid4()
        warehouse_id = uuid4()
        sku = "MED-001"
        category = "medicamentos_especiales"
        limit = 20
        offset = 40

        mock_repository = AsyncMock()
        mock_repository.list_inventories.return_value = ([], 0)

        use_case = ListInventoriesUseCase(mock_repository)

        # When
        await use_case.execute(
            limit=limit,
            offset=offset,
            product_id=product_id,
            warehouse_id=warehouse_id,
            sku=sku,
            category=category
        )

        # Then - Verify all parameters passed through
        mock_repository.list_inventories.assert_called_once_with(
            limit=limit,
            offset=offset,
            product_id=product_id,
            warehouse_id=warehouse_id,
            sku=sku,
            category=category,
            name=None,
        )
