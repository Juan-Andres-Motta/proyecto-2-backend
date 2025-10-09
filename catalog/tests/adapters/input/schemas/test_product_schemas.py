import uuid
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from src.adapters.input.schemas import (
    PaginatedProductsResponse,
    ProductResponse,
)


def test_product_response_schema():
    """Test ProductResponse schema validation."""
    product_id = uuid.uuid4()
    provider_id = uuid.uuid4()
    now = datetime.now(UTC)

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
    assert product.category == "electronics"
    assert product.description == "test description"
    assert product.price == Decimal("99.99")
    assert product.status == "active"


def test_paginated_products_response_schema():
    """Test PaginatedProductsResponse schema validation."""
    product_id = uuid.uuid4()
    provider_id = uuid.uuid4()
    now = datetime.now(UTC)

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

    paginated_response = PaginatedProductsResponse(
        items=[product],
        total=1,
        page=1,
        size=1,
        has_next=False,
        has_previous=False,
    )

    assert len(paginated_response.items) == 1
    assert paginated_response.total == 1
    assert paginated_response.page == 1
    assert paginated_response.size == 1
    assert paginated_response.has_next is False
    assert paginated_response.has_previous is False


def test_paginated_products_response_empty():
    """Test PaginatedProductsResponse with empty items."""
    paginated_response = PaginatedProductsResponse(
        items=[],
        total=0,
        page=1,
        size=0,
        has_next=False,
        has_previous=False,
    )

    assert len(paginated_response.items) == 0
    assert paginated_response.total == 0
