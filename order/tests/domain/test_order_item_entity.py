"""Tests for OrderItem domain entity."""

import pytest
from datetime import date, timedelta
from decimal import Decimal
from uuid import uuid4

from src.domain.entities import OrderItem


class TestOrderItemValidation:
    """Test OrderItem entity validation."""

    def test_order_item_validates_positive_cantidad(self):
        """Test that cantidad must be greater than 0."""
        with pytest.raises(ValueError, match="cantidad must be greater than 0"):
            OrderItem(
                id=uuid4(),
                pedido_id=uuid4(),
                inventario_id=uuid4(),
                cantidad=0,  # Invalid
                precio_unitario=Decimal("10.00"),
                precio_total=Decimal("0.00"),
                product_name="Product",
                product_sku="SKU",
                product_category="medicamentos_generales",
                warehouse_id=uuid4(),
                warehouse_name="Warehouse",
                warehouse_city="City",
                warehouse_country="Country",
                batch_number="BATCH",
                expiration_date=date.today() + timedelta(days=30),
            )

        with pytest.raises(ValueError, match="cantidad must be greater than 0"):
            OrderItem(
                id=uuid4(),
                pedido_id=uuid4(),
                inventario_id=uuid4(),
                cantidad=-5,  # Invalid
                precio_unitario=Decimal("10.00"),
                precio_total=Decimal("-50.00"),
                product_name="Product",
                product_sku="SKU",
                product_category="medicamentos_generales",
                warehouse_id=uuid4(),
                warehouse_name="Warehouse",
                warehouse_city="City",
                warehouse_country="Country",
                batch_number="BATCH",
                expiration_date=date.today() + timedelta(days=30),
            )

    def test_order_item_validates_non_negative_precio_unitario(self):
        """Test that precio_unitario cannot be negative."""
        with pytest.raises(ValueError, match="precio_unitario cannot be negative"):
            OrderItem(
                id=uuid4(),
                pedido_id=uuid4(),
                inventario_id=uuid4(),
                cantidad=5,
                precio_unitario=Decimal("-10.00"),  # Invalid
                precio_total=Decimal("-50.00"),
                product_name="Product",
                product_sku="SKU",
                product_category="medicamentos_generales",
                warehouse_id=uuid4(),
                warehouse_name="Warehouse",
                warehouse_city="City",
                warehouse_country="Country",
                batch_number="BATCH",
                expiration_date=date.today() + timedelta(days=30),
            )

    def test_order_item_validates_non_negative_precio_total(self):
        """Test that precio_total cannot be negative."""
        with pytest.raises(ValueError, match="precio_total cannot be negative"):
            OrderItem(
                id=uuid4(),
                pedido_id=uuid4(),
                inventario_id=uuid4(),
                cantidad=5,
                precio_unitario=Decimal("10.00"),
                precio_total=Decimal("-50.00"),  # Invalid
                product_name="Product",
                product_sku="SKU",
                product_category="medicamentos_generales",
                warehouse_id=uuid4(),
                warehouse_name="Warehouse",
                warehouse_city="City",
                warehouse_country="Country",
                batch_number="BATCH",
                expiration_date=date.today() + timedelta(days=30),
            )

    def test_order_item_validates_precio_total_calculation(self):
        """Test that precio_total must match cantidad * precio_unitario."""
        with pytest.raises(ValueError, match="does not match"):
            OrderItem(
                id=uuid4(),
                pedido_id=uuid4(),
                inventario_id=uuid4(),
                cantidad=5,
                precio_unitario=Decimal("10.00"),
                precio_total=Decimal("40.00"),  # Should be 50.00
                product_name="Product",
                product_sku="SKU",
                product_category="medicamentos_generales",
                warehouse_id=uuid4(),
                warehouse_name="Warehouse",
                warehouse_city="City",
                warehouse_country="Country",
                batch_number="BATCH",
                expiration_date=date.today() + timedelta(days=30),
            )

    def test_order_item_accepts_correct_values(self):
        """Test that valid OrderItem is created successfully."""
        item = OrderItem(
            id=uuid4(),
            pedido_id=uuid4(),
            inventario_id=uuid4(),
            cantidad=10,
            precio_unitario=Decimal("25.50"),
            precio_total=Decimal("255.00"),
            product_name="Test Product",
            product_sku="TEST-SKU-001",
            product_category="medicamentos_generales",
            warehouse_id=uuid4(),
            warehouse_name="Main Warehouse",
            warehouse_city="Bogota",
            warehouse_country="Colombia",
            batch_number="BATCH-2025-001",
            expiration_date=date.today() + timedelta(days=60),
        )

        assert item.cantidad == 10
        assert item.precio_unitario == Decimal("25.50")
        assert item.precio_total == Decimal("255.00")
        assert item.product_name == "Test Product"
        assert item.product_sku == "TEST-SKU-001"
        assert item.warehouse_name == "Main Warehouse"
        assert item.batch_number == "BATCH-2025-001"
