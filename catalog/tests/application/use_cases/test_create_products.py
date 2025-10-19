from decimal import Decimal
from unittest.mock import AsyncMock
from uuid import UUID

import pytest

from src.application.use_cases.create_products import CreateProductsUseCase
from src.domain.entities.product import Product
from src.domain.entities.provider import Provider
from src.domain.exceptions import BatchProductCreationException


@pytest.mark.asyncio
async def test_create_products_use_case_success():
    """Test successful batch product creation with validation."""
    # Mock repositories
    mock_product_repo = AsyncMock()
    mock_provider_repo = AsyncMock()

    # Setup provider exists
    provider = Provider(
        id=UUID("550e8400-e29b-41d4-a716-446655440000"),
        name="test provider",
        nit="123",
        contact_name="john",
        email="test@test.com",
        phone="+123",
        address="address",
        country="US",
        created_at="2024-01-01T00:00:00",
        updated_at="2024-01-01T00:00:00",
    )
    mock_provider_repo.find_by_id.return_value = provider

    # Setup no existing SKUs
    mock_product_repo.find_existing_skus.return_value = set()

    # Setup successful creation
    created_products = [
        Product(
            id=UUID("660e8400-e29b-41d4-a716-446655440000"),
            provider_id=UUID("550e8400-e29b-41d4-a716-446655440000"),
            provider_name="test provider",
            name="Product 1",
            category="medicamentos_especiales",
            sku="SKU-001",
            price=Decimal("100.00"),
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-01T00:00:00",
        ),
    ]
    mock_product_repo.batch_create.return_value = created_products

    use_case = CreateProductsUseCase(mock_product_repo, mock_provider_repo)
    products_data = [
        {
            "provider_id": UUID("550e8400-e29b-41d4-a716-446655440000"),
            "name": "Product 1",
            "category": "medicamentos_especiales",
            "sku": "SKU-001",
            "price": Decimal("100.00"),
        }
    ]

    result = await use_case.execute(products_data)

    assert result == created_products
    mock_provider_repo.find_by_id.assert_called_once()
    mock_product_repo.find_existing_skus.assert_called_once_with(["SKU-001"])
    mock_product_repo.batch_create.assert_called_once_with(products_data)


@pytest.mark.asyncio
async def test_create_products_provider_not_found():
    """Test that provider not found raises exception."""
    mock_product_repo = AsyncMock()
    mock_provider_repo = AsyncMock()

    # Provider doesn't exist
    mock_provider_repo.find_by_id.return_value = None

    use_case = CreateProductsUseCase(mock_product_repo, mock_provider_repo)
    products_data = [
        {
            "provider_id": UUID("550e8400-e29b-41d4-a716-446655440000"),
            "name": "Product 1",
            "category": "medicamentos_especiales",
            "sku": "SKU-001",
            "price": Decimal("100.00"),
        }
    ]

    with pytest.raises(BatchProductCreationException) as exc_info:
        await use_case.execute(products_data)

    assert exc_info.value.index == 0
    assert "Provider" in exc_info.value.error_detail
    assert "not found" in exc_info.value.error_detail
    mock_product_repo.batch_create.assert_not_called()


@pytest.mark.asyncio
async def test_create_products_duplicate_sku_in_database():
    """Test that duplicate SKU in database raises exception."""
    mock_product_repo = AsyncMock()
    mock_provider_repo = AsyncMock()

    # Provider exists
    provider = Provider(
        id=UUID("550e8400-e29b-41d4-a716-446655440000"),
        name="test provider",
        nit="123",
        contact_name="john",
        email="test@test.com",
        phone="+123",
        address="address",
        country="US",
        created_at="2024-01-01T00:00:00",
        updated_at="2024-01-01T00:00:00",
    )
    mock_provider_repo.find_by_id.return_value = provider

    # SKU already exists in database
    mock_product_repo.find_existing_skus.return_value = {"SKU-001"}

    use_case = CreateProductsUseCase(mock_product_repo, mock_provider_repo)
    products_data = [
        {
            "provider_id": UUID("550e8400-e29b-41d4-a716-446655440000"),
            "name": "Product 1",
            "category": "medicamentos_especiales",
            "sku": "SKU-001",
            "price": Decimal("100.00"),
        }
    ]

    with pytest.raises(BatchProductCreationException) as exc_info:
        await use_case.execute(products_data)

    assert exc_info.value.index == 0
    assert "SKU-001" in exc_info.value.error_detail
    assert "already exists" in exc_info.value.error_detail
    mock_product_repo.batch_create.assert_not_called()


@pytest.mark.asyncio
async def test_create_products_duplicate_sku_in_batch():
    """Test that duplicate SKU within batch raises exception."""
    mock_product_repo = AsyncMock()
    mock_provider_repo = AsyncMock()

    # Provider exists
    provider = Provider(
        id=UUID("550e8400-e29b-41d4-a716-446655440000"),
        name="test provider",
        nit="123",
        contact_name="john",
        email="test@test.com",
        phone="+123",
        address="address",
        country="US",
        created_at="2024-01-01T00:00:00",
        updated_at="2024-01-01T00:00:00",
    )
    mock_provider_repo.find_by_id.return_value = provider

    # No existing SKUs in database
    mock_product_repo.find_existing_skus.return_value = set()

    use_case = CreateProductsUseCase(mock_product_repo, mock_provider_repo)
    products_data = [
        {
            "provider_id": UUID("550e8400-e29b-41d4-a716-446655440000"),
            "name": "Product 1",
            "category": "medicamentos_especiales",
            "sku": "SKU-001",
            "price": Decimal("100.00"),
        },
        {
            "provider_id": UUID("550e8400-e29b-41d4-a716-446655440000"),
            "name": "Product 2",
            "category": "medicamentos_especiales",
            "sku": "SKU-001",  # Duplicate!
            "price": Decimal("200.00"),
        },
    ]

    with pytest.raises(BatchProductCreationException) as exc_info:
        await use_case.execute(products_data)

    assert exc_info.value.index == 1
    assert "SKU-001" in exc_info.value.error_detail
    assert "within batch" in exc_info.value.error_detail
    mock_product_repo.batch_create.assert_not_called()


@pytest.mark.asyncio
async def test_create_products_negative_price():
    """Test that negative price raises exception."""
    mock_product_repo = AsyncMock()
    mock_provider_repo = AsyncMock()

    # Provider exists
    provider = Provider(
        id=UUID("550e8400-e29b-41d4-a716-446655440000"),
        name="test provider",
        nit="123",
        contact_name="john",
        email="test@test.com",
        phone="+123",
        address="address",
        country="US",
        created_at="2024-01-01T00:00:00",
        updated_at="2024-01-01T00:00:00",
    )
    mock_provider_repo.find_by_id.return_value = provider

    use_case = CreateProductsUseCase(mock_product_repo, mock_provider_repo)
    products_data = [
        {
            "provider_id": UUID("550e8400-e29b-41d4-a716-446655440000"),
            "name": "Product 1",
            "category": "medicamentos_especiales",
            "sku": "SKU-001",
            "price": Decimal("-100.00"),  # Negative price!
        }
    ]

    with pytest.raises(BatchProductCreationException) as exc_info:
        await use_case.execute(products_data)

    assert exc_info.value.index == 0
    assert "Price must be greater than 0" in exc_info.value.error_detail
    mock_product_repo.batch_create.assert_not_called()
