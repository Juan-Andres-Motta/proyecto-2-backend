"""Tests for Product domain entity."""
from datetime import datetime
from decimal import Decimal
from uuid import uuid4
from unittest.mock import MagicMock

import pytest

from src.domain.entities.product import Product


def test_product_category_display_medicamentos_especiales():
    """Test category_display property for medicamentos_especiales."""
    product = Product(
        id=uuid4(),
        provider_id=uuid4(),
        provider_name="Test Provider",
        name="Test Product",
        category="medicamentos_especiales",
        sku="SKU-001",
        price=Decimal("100.00"),
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )

    assert product.category_display == "Medicamentos Especiales"


def test_product_category_display_insumos_quirurgicos():
    """Test category_display property for insumos_quirurgicos."""
    product = Product(
        id=uuid4(),
        provider_id=uuid4(),
        provider_name="Test Provider",
        name="Test Product",
        category="insumos_quirurgicos",
        sku="SKU-002",
        price=Decimal("50.00"),
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )

    assert product.category_display == "Insumos Quirúrgicos"


def test_product_category_display_reactivos_diagnosticos():
    """Test category_display property for reactivos_diagnosticos."""
    product = Product(
        id=uuid4(),
        provider_id=uuid4(),
        provider_name="Test Provider",
        name="Test Product",
        category="reactivos_diagnosticos",
        sku="SKU-003",
        price=Decimal("75.00"),
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )

    assert product.category_display == "Reactivos Diagnósticos"


def test_product_category_display_equipos_biomedicos():
    """Test category_display property for equipos_biomedicos."""
    product = Product(
        id=uuid4(),
        provider_id=uuid4(),
        provider_name="Test Provider",
        name="Test Product",
        category="equipos_biomedicos",
        sku="SKU-004",
        price=Decimal("500.00"),
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )

    assert product.category_display == "Equipos Biomédicos"


def test_product_category_display_otros():
    """Test category_display property for otros."""
    product = Product(
        id=uuid4(),
        provider_id=uuid4(),
        provider_name="Test Provider",
        name="Test Product",
        category="otros",
        sku="SKU-005",
        price=Decimal("25.00"),
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )

    assert product.category_display == "Otros"


def test_product_category_display_unknown_category():
    """Test category_display property returns category as-is for unknown categories."""
    product = Product(
        id=uuid4(),
        provider_id=uuid4(),
        provider_name="Test Provider",
        name="Test Product",
        category="unknown_category",
        sku="SKU-006",
        price=Decimal("30.00"),
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )

    assert product.category_display == "unknown_category"


def test_product_from_orm():
    """Test from_orm class method converts ORM model to domain entity."""
    product_id = uuid4()
    provider_id = uuid4()
    now = datetime.now()

    # Mock ORM product
    orm_product = MagicMock()
    orm_product.id = product_id
    orm_product.provider_id = provider_id
    orm_product.provider.name = "Test Provider"
    orm_product.name = "Test Product"
    orm_product.category = "medicamentos_especiales"
    orm_product.sku = "SKU-007"
    orm_product.price = Decimal("150.00")
    orm_product.created_at = now
    orm_product.updated_at = now

    # Convert using from_orm
    product = Product.from_orm(orm_product)

    assert product.id == product_id
    assert product.provider_id == provider_id
    assert product.provider_name == "Test Provider"
    assert product.name == "Test Product"
    assert product.category == "medicamentos_especiales"
    assert product.sku == "SKU-007"
    assert product.price == Decimal("150.00")
    assert product.created_at == now
    assert product.updated_at == now
