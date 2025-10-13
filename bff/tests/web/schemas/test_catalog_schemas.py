import uuid
from datetime import datetime
from decimal import Decimal

import pytest

from web.schemas import (
    PaginatedProductsResponse,
    PaginatedProvidersResponse,
    ProductResponse,
    ProviderResponse,
)
from web.schemas.enums import ProductCategory, ProductStatus


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
        "category": ProductCategory.SPECIAL_MEDICATIONS.value,
        "description": "test description",
        "price": Decimal("99.99"),
        "status": ProductStatus.ACTIVE.value,
        "created_at": now,
        "updated_at": now,
    }

    product = ProductResponse(**product_data)

    assert product.id == product_id
    assert product.provider_id == provider_id
    assert product.name == "test product"
    assert product.price == Decimal("99.99")


def test_paginated_providers_response_schema():
    """Test PaginatedProvidersResponse schema validation."""
    provider_id = uuid.uuid4()
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

    paginated_response = PaginatedProvidersResponse(
        items=[provider], total=1, page=1, size=10, has_next=False, has_previous=False
    )

    assert len(paginated_response.items) == 1
    assert paginated_response.total == 1
    assert paginated_response.page == 1
    assert paginated_response.size == 10
    assert paginated_response.has_next is False
    assert paginated_response.has_previous is False
    assert paginated_response.items[0].id == provider_id


def test_paginated_providers_response_empty():
    """Test PaginatedProvidersResponse with empty items."""
    paginated_response = PaginatedProvidersResponse(
        items=[], total=0, page=1, size=10, has_next=False, has_previous=False
    )

    assert len(paginated_response.items) == 0
    assert paginated_response.total == 0
    assert paginated_response.items == []


def test_paginated_products_response_schema():
    """Test PaginatedProductsResponse schema validation."""
    provider_id = uuid.uuid4()
    product_id = uuid.uuid4()
    now = datetime.utcnow()

    product = ProductResponse(
        id=product_id,
        provider_id=provider_id,
        name="test product",
        category=ProductCategory.SPECIAL_MEDICATIONS.value,
        description="test description",
        price=Decimal("99.99"),
        status=ProductStatus.ACTIVE.value,
        created_at=now,
        updated_at=now,
    )

    paginated_response = PaginatedProductsResponse(
        items=[product], total=1, page=1, size=10, has_next=False, has_previous=False
    )

    assert len(paginated_response.items) == 1
    assert paginated_response.total == 1
    assert paginated_response.page == 1
    assert paginated_response.size == 10
    assert paginated_response.has_next is False
    assert paginated_response.has_previous is False
    assert paginated_response.items[0].id == product_id


def test_paginated_products_response_empty():
    """Test PaginatedProductsResponse with empty items."""
    paginated_response = PaginatedProductsResponse(
        items=[], total=0, page=1, size=10, has_next=False, has_previous=False
    )

    assert len(paginated_response.items) == 0
    assert paginated_response.total == 0
    assert paginated_response.items == []
