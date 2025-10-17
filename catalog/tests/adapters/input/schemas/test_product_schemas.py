import uuid
from datetime import UTC, datetime
from decimal import Decimal

import pytest
from pydantic import ValidationError

from src.adapters.input.schemas import (
    BatchProductsRequest,
    BatchProductsResponse,
    PaginatedProductsResponse,
    ProductCreate,
    ProductResponse,
)
from src.infrastructure.database.models import ProductCategory


def test_product_response_schema():
    """Test ProductResponse schema validation with enums."""
    product_id = uuid.uuid4()
    provider_id = uuid.uuid4()
    now = datetime.now(UTC)

    product_data = {
        "id": product_id,
        "provider_id": provider_id,
        "name": "test product",
        "category": ProductCategory.SPECIAL_MEDICATIONS,
        "sku": "SKU-TEST-001",
        "price": Decimal("99.99"),
        "created_at": now,
        "updated_at": now,
    }

    product = ProductResponse(**product_data)

    assert product.id == product_id
    assert product.provider_id == provider_id
    assert product.name == "test product"
    assert product.category == ProductCategory.SPECIAL_MEDICATIONS
    assert product.sku == "SKU-TEST-001"
    assert product.price == Decimal("99.99")


def test_product_create_schema():
    """Test ProductCreate schema validation."""
    provider_id = uuid.uuid4()

    product_data = {
        "provider_id": provider_id,
        "name": "New Product",
        "category": ProductCategory.SURGICAL_SUPPLIES,
        "sku": "SKU-NEW-001",
        "price": Decimal("150.00"),
    }

    product = ProductCreate(**product_data)

    assert product.provider_id == provider_id
    assert product.name == "New Product"
    assert product.category == ProductCategory.SURGICAL_SUPPLIES
    assert product.sku == "SKU-NEW-001"


def test_product_create_invalid_category():
    """Test ProductCreate rejects invalid category."""
    provider_id = uuid.uuid4()

    product_data = {
        "provider_id": provider_id,
        "name": "New Product",
        "category": "invalid_category",
        "sku": "SKU-INVALID-001",
        "price": Decimal("150.00"),
    }

    with pytest.raises(ValidationError) as exc_info:
        ProductCreate(**product_data)

    assert "category" in str(exc_info.value)


def test_product_create_invalid_price():
    """Test ProductCreate rejects invalid price (negative or zero)."""
    provider_id = uuid.uuid4()

    product_data = {
        "provider_id": provider_id,
        "name": "New Product",
        "category": ProductCategory.OTHER,
        "sku": "SKU-PRICE-001",
        "price": Decimal("0.00"),
    }

    with pytest.raises(ValidationError) as exc_info:
        ProductCreate(**product_data)

    assert "price" in str(exc_info.value)


def test_batch_products_request():
    """Test BatchProductsRequest schema."""
    provider_id = uuid.uuid4()

    products = [
        ProductCreate(
            provider_id=provider_id,
            name="Product 1",
            category=ProductCategory.SPECIAL_MEDICATIONS,
            sku="SKU-BATCH-REQ-1",
            price=Decimal("100.00"),
        ),
        ProductCreate(
            provider_id=provider_id,
            name="Product 2",
            category=ProductCategory.SURGICAL_SUPPLIES,
            sku="SKU-BATCH-REQ-2",
            price=Decimal("200.00"),
        ),
    ]

    batch_request = BatchProductsRequest(products=products)
    assert len(batch_request.products) == 2


def test_batch_products_request_empty():
    """Test BatchProductsRequest rejects empty list."""
    with pytest.raises(ValidationError) as exc_info:
        BatchProductsRequest(products=[])

    # Pydantic v2 uses 'too_short' instead of 'min_items'
    error_str = str(exc_info.value).lower()
    assert "too_short" in error_str or "at least 1" in error_str


def test_batch_products_response():
    """Test BatchProductsResponse schema."""
    product_id = uuid.uuid4()
    provider_id = uuid.uuid4()
    now = datetime.now(UTC)

    products = [
        ProductResponse(
            id=product_id,
            provider_id=provider_id,
            name="Product",
            category=ProductCategory.OTHER,
            sku="SKU-BATCH-RESP-1",
            price=Decimal("100.00"),
            created_at=now,
            updated_at=now,
        )
    ]

    batch_response = BatchProductsResponse(created=products, count=1)
    assert len(batch_response.created) == 1
    assert batch_response.count == 1


def test_paginated_products_response_schema():
    """Test PaginatedProductsResponse schema validation."""
    product_id = uuid.uuid4()
    provider_id = uuid.uuid4()
    now = datetime.now(UTC)

    product = ProductResponse(
        id=product_id,
        provider_id=provider_id,
        name="test product",
        category=ProductCategory.BIOMEDICAL_EQUIPMENT,
        sku="SKU-PAGINATED-1",
        price=Decimal("99.99"),
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
