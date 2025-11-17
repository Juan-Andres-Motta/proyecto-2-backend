"""Unit tests for Inventory Repository with category filtering.

Tests the inventory repository implementation including:
- find_all() with category filter
- find_all() without category (returns all)
- Category filtering logic
- _to_domain() mapper includes product_category
"""
import pytest
from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

from src.adapters.output.repositories.inventory_repository import InventoryRepository
from src.infrastructure.database.models import Inventory as ORMInventory, Warehouse


@pytest.mark.asyncio
class TestInventoryRepository:
    """Test suite for Inventory Repository."""

    async def test_should_create_inventory_with_category(self, db_session):
        """Test creating inventory with product_category field."""
        # Given
        repository = InventoryRepository(db_session)

        # Create warehouse first
        warehouse = Warehouse(
            id=uuid4(),
            name="Lima Central",
            city="Lima",
            country="Peru",
            address="123 Test St"
        )
        db_session.add(warehouse)
        await db_session.commit()

        inventory_data = {
            "id": uuid4(),
            "product_id": uuid4(),
            "warehouse_id": warehouse.id,
            "total_quantity": 100,
            "reserved_quantity": 0,
            "batch_number": "BATCH-001",
            "expiration_date": datetime.now(timezone.utc),
            "product_sku": "MED-001",
            "product_name": "Aspirin 100mg",
            "product_price": Decimal("10.50"),
            "product_category": "medicamentos_especiales",
            "warehouse_name": "Lima Central",
            "warehouse_city": "Lima",
        "warehouse_country": "Colombia",
        }

        # When
        created_inventory = await repository.create(inventory_data)

        # Then
        assert created_inventory.id == inventory_data["id"]
        assert created_inventory.product_category == "medicamentos_especiales"

    async def test_should_find_by_id_and_include_category(self, db_session):
        """Test finding inventory by ID includes product_category."""
        # Given
        repository = InventoryRepository(db_session)
        inventory_id = uuid4()

        # Create warehouse first
        warehouse = Warehouse(
            id=uuid4(),
            name="Lima Central",
            city="Lima",
            country="Peru",
            address="123 Test St"
        )
        db_session.add(warehouse)
        await db_session.commit()

        orm_inventory = ORMInventory(
            id=inventory_id,
            product_id=uuid4(),
            warehouse_id=warehouse.id,
            total_quantity=100,
            reserved_quantity=0,
            batch_number="BATCH-001",
            expiration_date=datetime.now(timezone.utc),
            product_sku="MED-001",
            product_name="Aspirin 100mg",
            product_price=Decimal("10.50"),
            product_category="medicamentos_especiales",
            warehouse_name="Lima Central",
            warehouse_city="Lima",
            warehouse_country="Colombia",
        )
        db_session.add(orm_inventory)
        await db_session.commit()

        # When
        found_inventory = await repository.find_by_id(inventory_id)

        # Then
        assert found_inventory is not None
        assert found_inventory.id == inventory_id
        assert found_inventory.product_category == "medicamentos_especiales"

    async def test_should_filter_inventories_by_category(self, db_session):
        """Test filtering inventories by product_category."""
        # Given
        repository = InventoryRepository(db_session)

        # Create warehouse first
        warehouse = Warehouse(
            id=uuid4(),
            name="Lima Central",
            city="Lima",
            country="Peru",
            address="123 Test St"
        )
        db_session.add(warehouse)
        await db_session.commit()

        # Create inventories in different categories
        product_id_1 = uuid4()
        product_id_2 = uuid4()

        inventory1 = ORMInventory(
            id=uuid4(),
            product_id=product_id_1,
            warehouse_id=warehouse.id,
            total_quantity=100,
            reserved_quantity=0,
            batch_number="BATCH-001",
            expiration_date=datetime.now(timezone.utc),
            product_sku="MED-001",
            product_name="Aspirin 100mg",
            product_price=Decimal("10.50"),
            product_category="medicamentos_especiales",
            warehouse_name="Lima Central",
            warehouse_city="Lima",
            warehouse_country="Colombia",
        )
        inventory2 = ORMInventory(
            id=uuid4(),
            product_id=product_id_2,
            warehouse_id=warehouse.id,
            total_quantity=50,
            reserved_quantity=0,
            batch_number="BATCH-002",
            expiration_date=datetime.now(timezone.utc),
            product_sku="SURG-001",
            product_name="Surgical Mask",
            product_price=Decimal("5.00"),
            product_category="insumos_quirurgicos",
            warehouse_name="Lima Central",
            warehouse_city="Lima",
            warehouse_country="Colombia",
        )
        db_session.add_all([inventory1, inventory2])
        await db_session.commit()

        # When - Filter by medicamentos_especiales
        inventories, total = await repository.list_inventories(
            category="medicamentos_especiales"
        )

        # Then - Only medicamentos_especiales returned
        assert total == 1
        assert len(inventories) == 1
        assert inventories[0].product_category == "medicamentos_especiales"
        assert inventories[0].product_sku == "MED-001"

    async def test_should_return_all_inventories_when_no_category_filter(self, db_session):
        """Test listing all inventories when category filter is not provided."""
        # Given
        repository = InventoryRepository(db_session)

        # Create warehouse first
        warehouse = Warehouse(
            id=uuid4(),
            name="Lima Central",
            city="Lima",
            country="Peru",
            address="123 Test St"
        )
        db_session.add(warehouse)
        await db_session.commit()

        # Create inventories in different categories
        inventory1 = ORMInventory(
            id=uuid4(),
            product_id=uuid4(),
            warehouse_id=warehouse.id,
            total_quantity=100,
            reserved_quantity=0,
            batch_number="BATCH-001",
            expiration_date=datetime.now(timezone.utc),
            product_sku="MED-001",
            product_name="Aspirin 100mg",
            product_price=Decimal("10.50"),
            product_category="medicamentos_especiales",
            warehouse_name="Lima Central",
            warehouse_city="Lima",
            warehouse_country="Colombia",
        )
        inventory2 = ORMInventory(
            id=uuid4(),
            product_id=uuid4(),
            warehouse_id=warehouse.id,
            total_quantity=50,
            reserved_quantity=0,
            batch_number="BATCH-002",
            expiration_date=datetime.now(timezone.utc),
            product_sku="SURG-001",
            product_name="Surgical Mask",
            product_price=Decimal("5.00"),
            product_category="insumos_quirurgicos",
            warehouse_name="Lima Central",
            warehouse_city="Lima",
            warehouse_country="Colombia",
        )
        db_session.add_all([inventory1, inventory2])
        await db_session.commit()

        # When - No category filter
        inventories, total = await repository.list_inventories(limit=10)

        # Then - All inventories returned
        assert total == 2
        assert len(inventories) == 2
        categories = {inv.product_category for inv in inventories}
        assert "medicamentos_especiales" in categories
        assert "insumos_quirurgicos" in categories

    async def test_should_combine_category_filter_with_other_filters(self, db_session):
        """Test combining category filter with product_id filter."""
        # Given
        repository = InventoryRepository(db_session)

        # Create warehouse first
        warehouse = Warehouse(
            id=uuid4(),
            name="Lima Central",
            city="Lima",
            country="Peru",
            address="123 Test St"
        )
        db_session.add(warehouse)
        await db_session.commit()

        product_id = uuid4()

        # Create multiple inventories of same product but different categories
        # (This shouldn't happen in real life, but tests the filter logic)
        inventory1 = ORMInventory(
            id=uuid4(),
            product_id=product_id,
            warehouse_id=warehouse.id,
            total_quantity=100,
            reserved_quantity=0,
            batch_number="BATCH-001",
            expiration_date=datetime.now(timezone.utc),
            product_sku="MED-001",
            product_name="Product A",
            product_price=Decimal("10.50"),
            product_category="medicamentos_especiales",
            warehouse_name="Lima Central",
            warehouse_city="Lima",
            warehouse_country="Colombia",
        )
        inventory2 = ORMInventory(
            id=uuid4(),
            product_id=uuid4(),
            warehouse_id=warehouse.id,
            total_quantity=50,
            reserved_quantity=0,
            batch_number="BATCH-002",
            expiration_date=datetime.now(timezone.utc),
            product_sku="SURG-001",
            product_name="Product B",
            product_price=Decimal("5.00"),
            product_category="medicamentos_especiales",
            warehouse_name="Lima Central",
            warehouse_city="Lima",
            warehouse_country="Colombia",
        )
        db_session.add_all([inventory1, inventory2])
        await db_session.commit()

        # When - Filter by both category and product_id
        inventories, total = await repository.list_inventories(
            category="medicamentos_especiales",
            product_id=product_id
        )

        # Then - Only matching both filters
        assert total == 1
        assert len(inventories) == 1
        assert inventories[0].product_id == product_id
        assert inventories[0].product_category == "medicamentos_especiales"

    async def test_should_return_empty_list_when_category_has_no_matches(self, db_session):
        """Test that empty list is returned when category filter has no matches."""
        # Given
        repository = InventoryRepository(db_session)

        # Create warehouse first
        warehouse = Warehouse(
            id=uuid4(),
            name="Lima Central",
            city="Lima",
            country="Peru",
            address="123 Test St"
        )
        db_session.add(warehouse)
        await db_session.commit()

        # Create inventory in different category
        inventory = ORMInventory(
            id=uuid4(),
            product_id=uuid4(),
            warehouse_id=warehouse.id,
            total_quantity=100,
            reserved_quantity=0,
            batch_number="BATCH-001",
            expiration_date=datetime.now(timezone.utc),
            product_sku="MED-001",
            product_name="Aspirin 100mg",
            product_price=Decimal("10.50"),
            product_category="medicamentos_especiales",
            warehouse_name="Lima Central",
            warehouse_city="Lima",
            warehouse_country="Colombia",
        )
        db_session.add(inventory)
        await db_session.commit()

        # When - Filter by non-existent category
        inventories, total = await repository.list_inventories(
            category="equipos_biomedicos"
        )

        # Then - Empty list
        assert total == 0
        assert len(inventories) == 0

    async def test_should_map_orm_to_domain_with_category(self, db_session):
        """Test that _to_domain() mapper includes product_category."""
        # Given
        repository = InventoryRepository(db_session)
        orm_inventory = ORMInventory(
            id=uuid4(),
            product_id=uuid4(),
            warehouse_id=uuid4(),
            total_quantity=100,
            reserved_quantity=0,
            batch_number="BATCH-001",
            expiration_date=datetime.now(timezone.utc),
            product_sku="MED-001",
            product_name="Aspirin 100mg",
            product_price=Decimal("10.50"),
            product_category="medicamentos_especiales",
            warehouse_name="Lima Central",
            warehouse_city="Lima",
            warehouse_country="Colombia",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        # When
        domain_inventory = repository._to_domain(orm_inventory)

        # Then
        assert domain_inventory.product_category == "medicamentos_especiales"
        assert domain_inventory.id == orm_inventory.id
        assert domain_inventory.product_sku == "MED-001"
        assert domain_inventory.product_name == "Aspirin 100mg"

    async def test_should_filter_by_sku_and_category_together(self, db_session):
        """Test filtering by both SKU and category simultaneously."""
        # Given
        repository = InventoryRepository(db_session)

        # Create warehouse first
        warehouse = Warehouse(
            id=uuid4(),
            name="Lima Central",
            city="Lima",
            country="Peru",
            address="123 Test St"
        )
        db_session.add(warehouse)
        await db_session.commit()

        # Create inventories with same SKU but different categories
        inventory1 = ORMInventory(
            id=uuid4(),
            product_id=uuid4(),
            warehouse_id=warehouse.id,
            total_quantity=100,
            reserved_quantity=0,
            batch_number="BATCH-001",
            expiration_date=datetime.now(timezone.utc),
            product_sku="MED-001",
            product_name="Product A",
            product_price=Decimal("10.50"),
            product_category="medicamentos_especiales",
            warehouse_name="Lima Central",
            warehouse_city="Lima",
            warehouse_country="Colombia",
        )
        inventory2 = ORMInventory(
            id=uuid4(),
            product_id=uuid4(),
            warehouse_id=warehouse.id,
            total_quantity=50,
            reserved_quantity=0,
            batch_number="BATCH-002",
            expiration_date=datetime.now(timezone.utc),
            product_sku="MED-002",
            product_name="Product B",
            product_price=Decimal("5.00"),
            product_category="medicamentos_especiales",
            warehouse_name="Lima Central",
            warehouse_city="Lima",
            warehouse_country="Colombia",
        )
        db_session.add_all([inventory1, inventory2])
        await db_session.commit()

        # When - Filter by SKU and category
        inventories, total = await repository.list_inventories(
            sku="MED-001",
            category="medicamentos_especiales"
        )

        # Then - Only matching both filters
        assert total == 1
        assert len(inventories) == 1
        assert inventories[0].product_sku == "MED-001"
        assert inventories[0].product_category == "medicamentos_especiales"

    async def test_should_handle_nullable_category_in_filter(self, db_session):
        """Test that inventories with NULL category are not returned when filtering by category."""
        # Given
        repository = InventoryRepository(db_session)

        # Create warehouse first
        warehouse = Warehouse(
            id=uuid4(),
            name="Lima Central",
            city="Lima",
            country="Peru",
            address="123 Test St"
        )
        db_session.add(warehouse)
        await db_session.commit()

        # Create inventory with NULL category
        inventory = ORMInventory(
            id=uuid4(),
            product_id=uuid4(),
            warehouse_id=warehouse.id,
            total_quantity=100,
            reserved_quantity=0,
            batch_number="BATCH-001",
            expiration_date=datetime.now(timezone.utc),
            product_sku="MED-001",
            product_name="Old Product",
            product_price=Decimal("10.50"),
            product_category=None,  # NULL category
            warehouse_name="Lima Central",
            warehouse_city="Lima",
            warehouse_country="Colombia",
        )
        db_session.add(inventory)
        await db_session.commit()

        # When - Filter by category
        inventories, total = await repository.list_inventories(
            category="medicamentos_especiales"
        )

        # Then - NULL category not returned
        assert total == 0
        assert len(inventories) == 0

    async def test_should_filter_inventories_by_name(self, db_session):
        """Test filtering inventories by product name using ILIKE."""
        # Given
        repository = InventoryRepository(db_session)

        # Create warehouse first
        warehouse = Warehouse(
            id=uuid4(),
            name="Lima Central",
            city="Lima",
            country="Peru",
            address="123 Test St"
        )
        db_session.add(warehouse)
        await db_session.commit()

        # Create inventories with different names
        inventory1 = ORMInventory(
            id=uuid4(),
            product_id=uuid4(),
            warehouse_id=warehouse.id,
            total_quantity=100,
            reserved_quantity=0,
            batch_number="BATCH-001",
            expiration_date=datetime.now(timezone.utc),
            product_sku="MED-001",
            product_name="Aspirin 100mg",
            product_price=Decimal("10.50"),
            product_category="medicamentos_especiales",
            warehouse_name="Lima Central",
            warehouse_city="Lima",
            warehouse_country="Colombia",
        )
        inventory2 = ORMInventory(
            id=uuid4(),
            product_id=uuid4(),
            warehouse_id=warehouse.id,
            total_quantity=50,
            reserved_quantity=0,
            batch_number="BATCH-002",
            expiration_date=datetime.now(timezone.utc),
            product_sku="SURG-001",
            product_name="Surgical Mask",
            product_price=Decimal("5.00"),
            product_category="insumos_quirurgicos",
            warehouse_name="Lima Central",
            warehouse_city="Lima",
            warehouse_country="Colombia",
        )
        inventory3 = ORMInventory(
            id=uuid4(),
            product_id=uuid4(),
            warehouse_id=warehouse.id,
            total_quantity=75,
            reserved_quantity=0,
            batch_number="BATCH-003",
            expiration_date=datetime.now(timezone.utc),
            product_sku="MED-002",
            product_name="Ibuprofen 200mg",
            product_price=Decimal("8.00"),
            product_category="medicamentos_especiales",
            warehouse_name="Lima Central",
            warehouse_city="Lima",
            warehouse_country="Colombia",
        )
        db_session.add_all([inventory1, inventory2, inventory3])
        await db_session.commit()

        # When - Filter by name containing "mask" (case insensitive)
        inventories, total = await repository.list_inventories(
            name="mask"
        )

        # Then - Only Surgical Mask returned
        assert total == 1
        assert len(inventories) == 1
        assert inventories[0].product_name == "Surgical Mask"

    async def test_should_filter_by_name_case_insensitive(self, db_session):
        """Test that name filtering is case insensitive."""
        # Given
        repository = InventoryRepository(db_session)

        # Create warehouse first
        warehouse = Warehouse(
            id=uuid4(),
            name="Lima Central",
            city="Lima",
            country="Peru",
            address="123 Test St"
        )
        db_session.add(warehouse)
        await db_session.commit()

        # Create inventory
        inventory = ORMInventory(
            id=uuid4(),
            product_id=uuid4(),
            warehouse_id=warehouse.id,
            total_quantity=100,
            reserved_quantity=0,
            batch_number="BATCH-001",
            expiration_date=datetime.now(timezone.utc),
            product_sku="MED-001",
            product_name="Aspirin 100mg",
            product_price=Decimal("10.50"),
            product_category="medicamentos_especiales",
            warehouse_name="Lima Central",
            warehouse_city="Lima",
            warehouse_country="Colombia",
        )
        db_session.add(inventory)
        await db_session.commit()

        # When - Filter by uppercase "ASPIRIN"
        inventories, total = await repository.list_inventories(
            name="ASPIRIN"
        )

        # Then - Should find "Aspirin 100mg"
        assert total == 1
        assert len(inventories) == 1
        assert inventories[0].product_name == "Aspirin 100mg"

    async def test_should_combine_name_filter_with_other_filters(self, db_session):
        """Test combining name filter with category and other filters."""
        # Given
        repository = InventoryRepository(db_session)

        # Create warehouse first
        warehouse = Warehouse(
            id=uuid4(),
            name="Lima Central",
            city="Lima",
            country="Peru",
            address="123 Test St"
        )
        db_session.add(warehouse)
        await db_session.commit()

        # Create inventories
        inventory1 = ORMInventory(
            id=uuid4(),
            product_id=uuid4(),
            warehouse_id=warehouse.id,
            total_quantity=100,
            reserved_quantity=0,
            batch_number="BATCH-001",
            expiration_date=datetime.now(timezone.utc),
            product_sku="MED-001",
            product_name="Aspirin 100mg",
            product_price=Decimal("10.50"),
            product_category="medicamentos_especiales",
            warehouse_name="Lima Central",
            warehouse_city="Lima",
            warehouse_country="Colombia",
        )
        inventory2 = ORMInventory(
            id=uuid4(),
            product_id=uuid4(),
            warehouse_id=warehouse.id,
            total_quantity=50,
            reserved_quantity=0,
            batch_number="BATCH-002",
            expiration_date=datetime.now(timezone.utc),
            product_sku="SURG-001",
            product_name="Aspirin Mask",
            product_price=Decimal("5.00"),
            product_category="insumos_quirurgicos",
            warehouse_name="Lima Central",
            warehouse_city="Lima",
            warehouse_country="Colombia",
        )
        db_session.add_all([inventory1, inventory2])
        await db_session.commit()

        # When - Filter by name="aspirin" AND category="medicamentos_especiales"
        inventories, total = await repository.list_inventories(
            name="aspirin",
            category="medicamentos_especiales"
        )

        # Then - Only medicamentos_especiales with "aspirin" in name
        assert total == 1
        assert len(inventories) == 1
        assert inventories[0].product_name == "Aspirin 100mg"
        assert inventories[0].product_category == "medicamentos_especiales"
