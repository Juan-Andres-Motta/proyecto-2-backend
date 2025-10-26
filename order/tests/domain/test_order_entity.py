"""Tests for Order domain entity."""

import pytest
from datetime import date, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

from src.domain.entities import Order, OrderItem
from src.domain.value_objects import CreationMethod


class TestOrderEntityValidation:
    """Test Order entity business rule validation."""

    def test_order_with_visita_vendedor_requires_seller_and_visit(self):
        """Test that visita_vendedor requires both seller_id and visit_id."""
        with pytest.raises(ValueError, match="seller_id is required"):
            Order(
                id=uuid4(),
                customer_id=uuid4(),
                seller_id=None,  # Missing
                visit_id=uuid4(),
                fecha_pedido=datetime.now(),
                fecha_entrega_estimada=date.today() + timedelta(days=1),
                metodo_creacion=CreationMethod.VISITA_VENDEDOR,
                direccion_entrega="123 Main St",
                ciudad_entrega="City",
                pais_entrega="Country",
                customer_name="John Doe",
            )

        with pytest.raises(ValueError, match="visit_id is required"):
            Order(
                id=uuid4(),
                customer_id=uuid4(),
                seller_id=uuid4(),
                visit_id=None,  # Missing
                fecha_pedido=datetime.now(),
                fecha_entrega_estimada=date.today() + timedelta(days=1),
                metodo_creacion=CreationMethod.VISITA_VENDEDOR,
                direccion_entrega="123 Main St",
                ciudad_entrega="City",
                pais_entrega="Country",
                customer_name="John Doe",
                seller_name="Seller Name",
            )

    def test_order_with_app_vendedor_requires_seller_only(self):
        """Test that app_vendedor requires seller_id, visit_id is optional."""
        # Test that seller_id is required
        with pytest.raises(ValueError, match="seller_id is required"):
            Order(
                id=uuid4(),
                customer_id=uuid4(),
                seller_id=None,  # Missing
                visit_id=None,
                fecha_pedido=datetime.now(),
                fecha_entrega_estimada=date.today() + timedelta(days=1),
                metodo_creacion=CreationMethod.APP_VENDEDOR,
                direccion_entrega="123 Main St",
                ciudad_entrega="City",
                pais_entrega="Country",
                customer_name="John Doe",
            )

        # Test that visit_id is optional (can be present)
        order_with_visit = Order(
            id=uuid4(),
            customer_id=uuid4(),
            seller_id=uuid4(),
            visit_id=uuid4(),  # Optional, allowed
            fecha_pedido=datetime.now(),
            fecha_entrega_estimada=date.today() + timedelta(days=1),
            metodo_creacion=CreationMethod.APP_VENDEDOR,
            direccion_entrega="123 Main St",
            ciudad_entrega="City",
            pais_entrega="Country",
            customer_name="John Doe",
            seller_name="Seller Name",
        )
        assert order_with_visit.visit_id is not None

    def test_order_with_app_cliente_requires_no_seller_or_visit(self):
        """Test that app_cliente requires neither seller_id nor visit_id."""
        with pytest.raises(ValueError, match="seller_id must be None"):
            Order(
                id=uuid4(),
                customer_id=uuid4(),
                seller_id=uuid4(),  # Should be None
                visit_id=None,
                fecha_pedido=datetime.now(),
                fecha_entrega_estimada=date.today() + timedelta(days=1),
                metodo_creacion=CreationMethod.APP_CLIENTE,
                direccion_entrega="123 Main St",
                ciudad_entrega="City",
                pais_entrega="Country",
                customer_name="John Doe",
            )

        with pytest.raises(ValueError, match="visit_id must be None"):
            Order(
                id=uuid4(),
                customer_id=uuid4(),
                seller_id=None,
                visit_id=uuid4(),  # Should be None
                fecha_pedido=datetime.now(),
                fecha_entrega_estimada=date.today() + timedelta(days=1),
                metodo_creacion=CreationMethod.APP_CLIENTE,
                direccion_entrega="123 Main St",
                ciudad_entrega="City",
                pais_entrega="Country",
                customer_name="John Doe",
            )

    def test_order_requires_customer_name(self):
        """Test that customer_name is required."""
        with pytest.raises(ValueError, match="customer_name is required"):
            Order(
                id=uuid4(),
                customer_id=uuid4(),
                seller_id=None,
                visit_id=None,
                fecha_pedido=datetime.now(),
                fecha_entrega_estimada=date.today() + timedelta(days=1),
                metodo_creacion=CreationMethod.APP_CLIENTE,
                direccion_entrega="123 Main St",
                ciudad_entrega="City",
                pais_entrega="Country",
                customer_name="",  # Empty
            )

    def test_order_requires_delivery_address(self):
        """Test that delivery address fields are required."""
        with pytest.raises(ValueError, match="direccion_entrega is required"):
            Order(
                id=uuid4(),
                customer_id=uuid4(),
                seller_id=None,
                visit_id=None,
                fecha_pedido=datetime.now(),
                fecha_entrega_estimada=date.today() + timedelta(days=1),
                metodo_creacion=CreationMethod.APP_CLIENTE,
                direccion_entrega="",  # Empty
                ciudad_entrega="City",
                pais_entrega="Country",
                customer_name="John Doe",
            )


class TestOrderEntityItems:
    """Test Order entity item management."""

    def test_add_item_updates_monto_total(self):
        """Test that adding items updates monto_total incrementally."""
        order = Order(
            id=uuid4(),
            customer_id=uuid4(),
            seller_id=None,
            visit_id=None,
            fecha_pedido=datetime.now(),
            fecha_entrega_estimada=date.today() + timedelta(days=1),
            metodo_creacion=CreationMethod.APP_CLIENTE,
            direccion_entrega="123 Main St",
            ciudad_entrega="City",
            pais_entrega="Country",
            customer_name="John Doe",
        )

        assert order.monto_total == Decimal("0.00")

        item1 = OrderItem(
            id=uuid4(),
            pedido_id=order.id,
            producto_id=uuid4(),
            inventario_id=uuid4(),
            cantidad=2,
            precio_unitario=Decimal("10.00"),
            precio_total=Decimal("20.00"),
            product_name="Product 1",
            product_sku="SKU1",
            warehouse_id=uuid4(),
            warehouse_name="Warehouse",
            warehouse_city="City",
            warehouse_country="Country",
            batch_number="BATCH1",
            expiration_date=date.today() + timedelta(days=30),
        )

        order.add_item(item1)
        assert order.monto_total == Decimal("20.00")
        assert order.item_count == 1

        item2 = OrderItem(
            id=uuid4(),
            pedido_id=order.id,
            producto_id=uuid4(),
            inventario_id=uuid4(),
            cantidad=3,
            precio_unitario=Decimal("15.00"),
            precio_total=Decimal("45.00"),
            product_name="Product 2",
            product_sku="SKU2",
            warehouse_id=uuid4(),
            warehouse_name="Warehouse",
            warehouse_city="City",
            warehouse_country="Country",
            batch_number="BATCH2",
            expiration_date=date.today() + timedelta(days=30),
        )

        order.add_item(item2)
        assert order.monto_total == Decimal("65.00")
        assert order.item_count == 2

    def test_add_item_validates_pedido_id_match(self):
        """Test that item's pedido_id must match order's id."""
        order = Order(
            id=uuid4(),
            customer_id=uuid4(),
            seller_id=None,
            visit_id=None,
            fecha_pedido=datetime.now(),
            fecha_entrega_estimada=date.today() + timedelta(days=1),
            metodo_creacion=CreationMethod.APP_CLIENTE,
            direccion_entrega="123 Main St",
            ciudad_entrega="City",
            pais_entrega="Country",
            customer_name="John Doe",
        )

        wrong_item = OrderItem(
            id=uuid4(),
            pedido_id=uuid4(),  # Different ID
            producto_id=uuid4(),
            inventario_id=uuid4(),
            cantidad=1,
            precio_unitario=Decimal("10.00"),
            precio_total=Decimal("10.00"),
            product_name="Product",
            product_sku="SKU",
            warehouse_id=uuid4(),
            warehouse_name="Warehouse",
            warehouse_city="City",
            warehouse_country="Country",
            batch_number="BATCH",
            expiration_date=date.today() + timedelta(days=30),
        )

        with pytest.raises(ValueError, match="does not match Order id"):
            order.add_item(wrong_item)

    def test_order_items_property_returns_copy(self):
        """Test that items property returns a copy (read-only)."""
        order = Order(
            id=uuid4(),
            customer_id=uuid4(),
            seller_id=None,
            visit_id=None,
            fecha_pedido=datetime.now(),
            fecha_entrega_estimada=date.today() + timedelta(days=1),
            metodo_creacion=CreationMethod.APP_CLIENTE,
            direccion_entrega="123 Main St",
            ciudad_entrega="City",
            pais_entrega="Country",
            customer_name="John Doe",
        )

        items = order.items
        assert len(items) == 0

        # Modifying the returned list should not affect the order
        items.append("fake")
        assert len(order.items) == 0

    def test_order_total_quantity_calculation(self):
        """Test total_quantity property."""
        order = Order(
            id=uuid4(),
            customer_id=uuid4(),
            seller_id=None,
            visit_id=None,
            fecha_pedido=datetime.now(),
            fecha_entrega_estimada=date.today() + timedelta(days=1),
            metodo_creacion=CreationMethod.APP_CLIENTE,
            direccion_entrega="123 Main St",
            ciudad_entrega="City",
            pais_entrega="Country",
            customer_name="John Doe",
        )

        item1 = OrderItem(
            id=uuid4(),
            pedido_id=order.id,
            producto_id=uuid4(),
            inventario_id=uuid4(),
            cantidad=5,
            precio_unitario=Decimal("10.00"),
            precio_total=Decimal("50.00"),
            product_name="Product 1",
            product_sku="SKU1",
            warehouse_id=uuid4(),
            warehouse_name="Warehouse",
            warehouse_city="City",
            warehouse_country="Country",
            batch_number="BATCH1",
            expiration_date=date.today() + timedelta(days=30),
        )

        item2 = OrderItem(
            id=uuid4(),
            pedido_id=order.id,
            producto_id=uuid4(),
            inventario_id=uuid4(),
            cantidad=3,
            precio_unitario=Decimal("15.00"),
            precio_total=Decimal("45.00"),
            product_name="Product 2",
            product_sku="SKU2",
            warehouse_id=uuid4(),
            warehouse_name="Warehouse",
            warehouse_city="City",
            warehouse_country="Country",
            batch_number="BATCH2",
            expiration_date=date.today() + timedelta(days=30),
        )

        order.add_item(item1)
        order.add_item(item2)

        assert order.total_quantity == 8  # 5 + 3

    def test_order_requires_metodo_creacion(self):
        """Test that metodo_creacion is required (covers line 69)."""
        with pytest.raises(ValueError, match="metodo_creacion is required"):
            Order(
                id=uuid4(),
                customer_id=uuid4(),
                seller_id=None,
                visit_id=None,
                fecha_pedido=datetime.now(),
                fecha_entrega_estimada=date.today() + timedelta(days=1),
                metodo_creacion=None,  # Missing
                direccion_entrega="123 Main St",
                ciudad_entrega="City",
                pais_entrega="Country",
                customer_name="John Doe",
            )

    def test_order_visita_vendedor_requires_seller_name(self):
        """Test that seller_name is required for visita_vendedor (covers line 82)."""
        with pytest.raises(ValueError, match="seller_name is required"):
            Order(
                id=uuid4(),
                customer_id=uuid4(),
                seller_id=uuid4(),
                visit_id=uuid4(),
                fecha_pedido=datetime.now(),
                fecha_entrega_estimada=date.today() + timedelta(days=1),
                metodo_creacion=CreationMethod.VISITA_VENDEDOR,
                direccion_entrega="123 Main St",
                ciudad_entrega="City",
                pais_entrega="Country",
                customer_name="John Doe",
                seller_name=None,  # Missing
            )

    def test_order_app_vendedor_requires_seller_name(self):
        """Test that seller_name is required for app_vendedor (covers line 93)."""
        with pytest.raises(ValueError, match="seller_name is required"):
            Order(
                id=uuid4(),
                customer_id=uuid4(),
                seller_id=uuid4(),
                visit_id=None,
                fecha_pedido=datetime.now(),
                fecha_entrega_estimada=date.today() + timedelta(days=1),
                metodo_creacion=CreationMethod.APP_VENDEDOR,
                direccion_entrega="123 Main St",
                ciudad_entrega="City",
                pais_entrega="Country",
                customer_name="John Doe",
                seller_name=None,  # Missing
            )

    def test_order_requires_ciudad_entrega(self):
        """Test that ciudad_entrega is required (covers line 115)."""
        with pytest.raises(ValueError, match="ciudad_entrega is required"):
            Order(
                id=uuid4(),
                customer_id=uuid4(),
                seller_id=None,
                visit_id=None,
                fecha_pedido=datetime.now(),
                fecha_entrega_estimada=date.today() + timedelta(days=1),
                metodo_creacion=CreationMethod.APP_CLIENTE,
                direccion_entrega="123 Main St",
                ciudad_entrega="",  # Empty
                pais_entrega="Country",
                customer_name="John Doe",
            )

    def test_order_requires_pais_entrega(self):
        """Test that pais_entrega is required (covers line 117)."""
        with pytest.raises(ValueError, match="pais_entrega is required"):
            Order(
                id=uuid4(),
                customer_id=uuid4(),
                seller_id=None,
                visit_id=None,
                fecha_pedido=datetime.now(),
                fecha_entrega_estimada=date.today() + timedelta(days=1),
                metodo_creacion=CreationMethod.APP_CLIENTE,
                direccion_entrega="123 Main St",
                ciudad_entrega="City",
                pais_entrega="",  # Empty
                customer_name="John Doe",
            )
