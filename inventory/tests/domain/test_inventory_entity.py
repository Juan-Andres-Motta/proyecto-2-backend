"""Unit tests for Inventory entity.

Tests the Inventory domain entity including:
- Entity creation with all denormalized fields
- Product category field validation
- All required fields
"""
import pytest
from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

from src.domain.entities.inventory import Inventory


class TestInventoryEntity:
    """Test suite for Inventory domain entity."""

    def test_should_create_inventory_with_all_fields(self):
        """Test creating inventory entity with all required fields."""
        # Given
        inventory_id = uuid4()
        product_id = uuid4()
        warehouse_id = uuid4()
        now = datetime.now(timezone.utc)

        # When
        inventory = Inventory(
            id=inventory_id,
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
            warehouse_country="Peru",
            created_at=now,
            updated_at=now,
        )

        # Then
        assert inventory.id == inventory_id
        assert inventory.product_id == product_id
        assert inventory.warehouse_id == warehouse_id
        assert inventory.total_quantity == 100
        assert inventory.reserved_quantity == 0
        assert inventory.batch_number == "BATCH-001"
        assert inventory.expiration_date == now
        assert inventory.product_sku == "MED-001"
        assert inventory.product_name == "Aspirin 100mg"
        assert inventory.product_price == Decimal("10.50")
        assert inventory.product_category == "medicamentos_especiales"
        assert inventory.warehouse_name == "Lima Central"
        assert inventory.warehouse_city == "Lima"
        assert inventory.created_at == now
        assert inventory.updated_at == now

    def test_should_create_inventory_with_product_category(self):
        """Test that inventory includes product_category denormalized field."""
        # Given
        now = datetime.now(timezone.utc)

        # When
        inventory = Inventory(
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
            warehouse_country="Peru",
            created_at=now,
            updated_at=now,
        )

        # Then
        assert inventory.product_category == "insumos_quirurgicos"

    def test_should_allow_different_category_values(self):
        """Test that different category values are supported."""
        # Given
        categories = [
            "medicamentos_especiales",
            "insumos_quirurgicos",
            "reactivos_diagnosticos",
            "equipos_biomedicos",
            "otros",
        ]
        now = datetime.now(timezone.utc)

        # When/Then
        for category in categories:
            inventory = Inventory(
                id=uuid4(),
                product_id=uuid4(),
                warehouse_id=uuid4(),
                total_quantity=100,
                reserved_quantity=0,
                batch_number="BATCH-001",
                expiration_date=now,
                product_sku="TEST-001",
                product_name="Test Product",
                product_price=Decimal("10.00"),
                product_category=category,
                warehouse_name="Test Warehouse",
                warehouse_city="Test City",
                warehouse_country="Colombia",
                created_at=now,
                updated_at=now,
            )
            assert inventory.product_category == category

    def test_should_calculate_available_quantity(self):
        """Test that available quantity can be calculated from total - reserved."""
        # Given
        now = datetime.now(timezone.utc)
        inventory = Inventory(
            id=uuid4(),
            product_id=uuid4(),
            warehouse_id=uuid4(),
            total_quantity=100,
            reserved_quantity=30,
            batch_number="BATCH-001",
            expiration_date=now,
            product_sku="MED-001",
            product_name="Test Product",
            product_price=Decimal("10.00"),
            product_category="medicamentos_especiales",
            warehouse_name="Test Warehouse",
            warehouse_city="Test City",
            warehouse_country="Colombia",
            created_at=now,
            updated_at=now,
        )

        # When
        available = inventory.total_quantity - inventory.reserved_quantity

        # Then
        assert available == 70

    def test_should_support_nullable_category(self):
        """Test that product_category can be None for backwards compatibility."""
        # Given
        now = datetime.now(timezone.utc)

        # When
        inventory = Inventory(
            id=uuid4(),
            product_id=uuid4(),
            warehouse_id=uuid4(),
            total_quantity=100,
            reserved_quantity=0,
            batch_number="BATCH-001",
            expiration_date=now,
            product_sku="MED-001",
            product_name="Test Product",
            product_price=Decimal("10.00"),
            product_category=None,  # Nullable for old data
            warehouse_name="Test Warehouse",
            warehouse_city="Test City",
            warehouse_country="Colombia",
            created_at=now,
            updated_at=now,
        )

        # Then
        assert inventory.product_category is None

    def test_should_preserve_all_denormalized_fields(self):
        """Test that all denormalized fields are preserved for performance."""
        # Given
        now = datetime.now(timezone.utc)

        # When
        inventory = Inventory(
            id=uuid4(),
            product_id=uuid4(),
            warehouse_id=uuid4(),
            total_quantity=100,
            reserved_quantity=0,
            batch_number="BATCH-001",
            expiration_date=now,
            # Product denormalized fields
            product_sku="MED-001",
            product_name="Aspirin 100mg",
            product_price=Decimal("10.50"),
            product_category="medicamentos_especiales",
            # Warehouse denormalized fields
            warehouse_name="Lima Central",
            warehouse_city="Lima",
            warehouse_country="Peru",
            created_at=now,
            updated_at=now,
        )

        # Then - All denormalized fields should be present
        assert inventory.product_sku == "MED-001"
        assert inventory.product_name == "Aspirin 100mg"
        assert inventory.product_price == Decimal("10.50")
        assert inventory.product_category == "medicamentos_especiales"
        assert inventory.warehouse_name == "Lima Central"
        assert inventory.warehouse_city == "Lima"
        assert inventory.warehouse_country == "Peru"

    def test_can_reserve_with_sufficient_inventory(self):
        """Test that can_reserve returns True when enough inventory available."""
        # Given
        now = datetime.now(timezone.utc)
        inventory = Inventory(
            id=uuid4(),
            product_id=uuid4(),
            warehouse_id=uuid4(),
            total_quantity=100,
            reserved_quantity=20,  # 80 available
            batch_number="BATCH-001",
            expiration_date=now,
            product_sku="MED-001",
            product_name="Test Product",
            product_price=Decimal("10.00"),
            product_category="medicamentos_especiales",
            warehouse_name="Test Warehouse",
            warehouse_city="Test City",
            warehouse_country="Colombia",
            created_at=now,
            updated_at=now,
        )

        # When/Then
        assert inventory.can_reserve(50) is True  # 50 <= 80
        assert inventory.can_reserve(80) is True  # 80 <= 80
        assert inventory.can_reserve(81) is False  # 81 > 80
        assert inventory.can_reserve(0) is False  # quantity must be > 0
        assert inventory.can_reserve(-10) is False  # quantity must be > 0

    def test_can_release_with_sufficient_reserved(self):
        """Test that can_release returns True when enough reserved quantity."""
        # Given
        now = datetime.now(timezone.utc)
        inventory = Inventory(
            id=uuid4(),
            product_id=uuid4(),
            warehouse_id=uuid4(),
            total_quantity=100,
            reserved_quantity=30,
            batch_number="BATCH-001",
            expiration_date=now,
            product_sku="MED-001",
            product_name="Test Product",
            product_price=Decimal("10.00"),
            product_category="medicamentos_especiales",
            warehouse_name="Test Warehouse",
            warehouse_city="Test City",
            warehouse_country="Colombia",
            created_at=now,
            updated_at=now,
        )

        # When/Then
        assert inventory.can_release(15) is True  # 15 <= 30
        assert inventory.can_release(30) is True  # 30 <= 30
        assert inventory.can_release(31) is False  # 31 > 30
        assert inventory.can_release(0) is False  # quantity must be > 0
        assert inventory.can_release(-10) is False  # quantity must be > 0

    def test_reserve_success(self):
        """Test successful reservation updates reserved quantity."""
        # Given
        now = datetime.now(timezone.utc)
        inventory = Inventory(
            id=uuid4(),
            product_id=uuid4(),
            warehouse_id=uuid4(),
            total_quantity=100,
            reserved_quantity=10,
            batch_number="BATCH-001",
            expiration_date=now,
            product_sku="MED-001",
            product_name="Test Product",
            product_price=Decimal("10.00"),
            product_category="medicamentos_especiales",
            warehouse_name="Test Warehouse",
            warehouse_city="Test City",
            warehouse_country="Colombia",
            created_at=now,
            updated_at=now,
        )

        # When
        inventory.reserve(25)

        # Then
        assert inventory.reserved_quantity == 35

    def test_reserve_insufficient_inventory_raises_exception(self):
        """Test that reserve raises exception when insufficient inventory."""
        from src.domain.exceptions import InsufficientInventoryException

        # Given
        now = datetime.now(timezone.utc)
        inventory = Inventory(
            id=uuid4(),
            product_id=uuid4(),
            warehouse_id=uuid4(),
            total_quantity=100,
            reserved_quantity=80,  # 20 available
            batch_number="BATCH-001",
            expiration_date=now,
            product_sku="MED-001",
            product_name="Test Product",
            product_price=Decimal("10.00"),
            product_category="medicamentos_especiales",
            warehouse_name="Test Warehouse",
            warehouse_city="Test City",
            warehouse_country="Colombia",
            created_at=now,
            updated_at=now,
        )

        # When/Then
        with pytest.raises(InsufficientInventoryException) as exc_info:
            inventory.reserve(25)
        assert exc_info.value.inventory_id == inventory.id
        assert exc_info.value.requested == 25
        assert exc_info.value.available == 20

    def test_release_success(self):
        """Test successful release updates reserved quantity."""
        # Given
        now = datetime.now(timezone.utc)
        inventory = Inventory(
            id=uuid4(),
            product_id=uuid4(),
            warehouse_id=uuid4(),
            total_quantity=100,
            reserved_quantity=40,
            batch_number="BATCH-001",
            expiration_date=now,
            product_sku="MED-001",
            product_name="Test Product",
            product_price=Decimal("10.00"),
            product_category="medicamentos_especiales",
            warehouse_name="Test Warehouse",
            warehouse_city="Test City",
            warehouse_country="Colombia",
            created_at=now,
            updated_at=now,
        )

        # When
        inventory.release(15)

        # Then
        assert inventory.reserved_quantity == 25

    def test_release_more_than_reserved_raises_exception(self):
        """Test that release raises exception when trying to release more than reserved."""
        from src.domain.exceptions import InvalidReservationReleaseException

        # Given
        now = datetime.now(timezone.utc)
        inventory = Inventory(
            id=uuid4(),
            product_id=uuid4(),
            warehouse_id=uuid4(),
            total_quantity=100,
            reserved_quantity=20,
            batch_number="BATCH-001",
            expiration_date=now,
            product_sku="MED-001",
            product_name="Test Product",
            product_price=Decimal("10.00"),
            product_category="medicamentos_especiales",
            warehouse_name="Test Warehouse",
            warehouse_city="Test City",
            warehouse_country="Colombia",
            created_at=now,
            updated_at=now,
        )

        # When/Then
        with pytest.raises(InvalidReservationReleaseException) as exc_info:
            inventory.release(30)
        assert exc_info.value.requested_release == 30
        assert exc_info.value.currently_reserved == 20

    def test_adjust_reservation_positive_delta_reserves(self):
        """Test that adjust_reservation with positive delta reserves units."""
        # Given
        now = datetime.now(timezone.utc)
        inventory = Inventory(
            id=uuid4(),
            product_id=uuid4(),
            warehouse_id=uuid4(),
            total_quantity=100,
            reserved_quantity=10,
            batch_number="BATCH-001",
            expiration_date=now,
            product_sku="MED-001",
            product_name="Test Product",
            product_price=Decimal("10.00"),
            product_category="medicamentos_especiales",
            warehouse_name="Test Warehouse",
            warehouse_city="Test City",
            warehouse_country="Colombia",
            created_at=now,
            updated_at=now,
        )

        # When
        inventory.adjust_reservation(20)

        # Then
        assert inventory.reserved_quantity == 30

    def test_adjust_reservation_negative_delta_releases(self):
        """Test that adjust_reservation with negative delta releases units."""
        # Given
        now = datetime.now(timezone.utc)
        inventory = Inventory(
            id=uuid4(),
            product_id=uuid4(),
            warehouse_id=uuid4(),
            total_quantity=100,
            reserved_quantity=40,
            batch_number="BATCH-001",
            expiration_date=now,
            product_sku="MED-001",
            product_name="Test Product",
            product_price=Decimal("10.00"),
            product_category="medicamentos_especiales",
            warehouse_name="Test Warehouse",
            warehouse_city="Test City",
            warehouse_country="Colombia",
            created_at=now,
            updated_at=now,
        )

        # When
        inventory.adjust_reservation(-15)

        # Then
        assert inventory.reserved_quantity == 25

    def test_adjust_reservation_zero_delta_no_change(self):
        """Test that adjust_reservation with zero delta makes no change."""
        # Given
        now = datetime.now(timezone.utc)
        inventory = Inventory(
            id=uuid4(),
            product_id=uuid4(),
            warehouse_id=uuid4(),
            total_quantity=100,
            reserved_quantity=40,
            batch_number="BATCH-001",
            expiration_date=now,
            product_sku="MED-001",
            product_name="Test Product",
            product_price=Decimal("10.00"),
            product_category="medicamentos_especiales",
            warehouse_name="Test Warehouse",
            warehouse_city="Test City",
            warehouse_country="Colombia",
            created_at=now,
            updated_at=now,
        )

        # When
        inventory.adjust_reservation(0)

        # Then - No change
        assert inventory.reserved_quantity == 40
