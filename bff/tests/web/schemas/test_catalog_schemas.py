import uuid
from datetime import datetime
from decimal import Decimal

import pytest

from web.schemas import CatalogResponse, ProductResponse, ProviderResponse


def test_provider_response_schema():
    """Test ProviderResponse schema validation."""
    provider_id = uuid.uuid4()
    now = datetime.utcnow()

    provider_data = {
        "id": provider_id,
        "name": "test provider",
        "nit": "123456789",
        "contact_name": "john doe",
        "email": "john@test.com",
        "phone": "+1234567890",
        "address": "123 test st",
        "country": "US",
        "created_at": now,
        "updated_at": now,
    }

    provider = ProviderResponse(**provider_data)

    assert provider.id == provider_id
    assert provider.name == "test provider"
    assert provider.nit == "123456789"
    assert provider.email == "john@test.com"


def test_product_response_schema():
    """Test ProductResponse schema validation."""
    product_id = uuid.uuid4()
    provider_id = uuid.uuid4()
    now = datetime.utcnow()

    product_data = {
        "id": product_id,
        "provider_id": provider_id,
        "name": "test product",
        "category": "electronics",
        "description": "test description",
        "price": Decimal("99.99"),
        "status": "active",
        "created_at": now,
        "updated_at": now,
    }

    product = ProductResponse(**product_data)

    assert product.id == product_id
    assert product.provider_id == provider_id
    assert product.name == "test product"
    assert product.price == Decimal("99.99")


def test_catalog_response_schema():
    """Test CatalogResponse schema validation."""
    provider_id = uuid.uuid4()
    product_id = uuid.uuid4()
    now = datetime.utcnow()

    provider = ProviderResponse(
        id=provider_id,
        name="test provider",
        nit="123456789",
        contact_name="john doe",
        email="john@test.com",
        phone="+1234567890",
        address="123 test st",
        country="US",
        created_at=now,
        updated_at=now,
    )

    product = ProductResponse(
        id=product_id,
        provider_id=provider_id,
        name="test product",
        category="electronics",
        description="test description",
        price=Decimal("99.99"),
        status="active",
        created_at=now,
        updated_at=now,
    )

    catalog = CatalogResponse(providers=[provider], products=[product])

    assert len(catalog.providers) == 1
    assert len(catalog.products) == 1
    assert catalog.providers[0].id == provider_id
    assert catalog.products[0].id == product_id


def test_catalog_response_empty():
    """Test CatalogResponse with empty lists."""
    catalog = CatalogResponse(providers=[], products=[])

    assert len(catalog.providers) == 0
    assert len(catalog.products) == 0
    assert catalog.providers == []
    assert catalog.products == []
