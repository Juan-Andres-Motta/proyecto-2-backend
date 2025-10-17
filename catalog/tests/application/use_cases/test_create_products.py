from unittest.mock import AsyncMock

import pytest

from src.application.use_cases.create_products import CreateProductsUseCase
from src.infrastructure.database.models import Product, ProductCategory


@pytest.mark.asyncio
async def test_create_products_use_case_success():
    """Test successful batch product creation via use case."""
    mock_repo = AsyncMock()

    mock_products = [
        Product(
            id="660e8400-e29b-41d4-a716-446655440000",
            provider_id="550e8400-e29b-41d4-a716-446655440000",
            name="Product 1",
            category=ProductCategory.SPECIAL_MEDICATIONS.value,
            sku="SKU-USE-CASE-1",
            price=100.00,
        ),
        Product(
            id="770e8400-e29b-41d4-a716-446655440000",
            provider_id="550e8400-e29b-41d4-a716-446655440000",
            name="Product 2",
            category=ProductCategory.SURGICAL_SUPPLIES.value,
            sku="SKU-USE-CASE-2",
            price=200.00,
        ),
    ]
    mock_repo.batch_create.return_value = mock_products

    use_case = CreateProductsUseCase(mock_repo)
    products_data = [
        {
            "provider_id": "550e8400-e29b-41d4-a716-446655440000",
            "name": "Product 1",
            "category": ProductCategory.SPECIAL_MEDICATIONS.value,
            "sku": "SKU-USE-CASE-1",
            "price": 100.00,
        },
        {
            "provider_id": "550e8400-e29b-41d4-a716-446655440000",
            "name": "Product 2",
            "category": ProductCategory.SURGICAL_SUPPLIES.value,
            "sku": "SKU-USE-CASE-2",
            "price": 200.00,
        },
    ]

    result = await use_case.execute(products_data)

    assert result == mock_products
    assert len(result) == 2
    mock_repo.batch_create.assert_called_once_with(products_data)


@pytest.mark.asyncio
async def test_create_products_use_case_empty_list():
    """Test batch product creation with empty list."""
    mock_repo = AsyncMock()
    mock_repo.batch_create.return_value = []

    use_case = CreateProductsUseCase(mock_repo)
    products_data = []

    result = await use_case.execute(products_data)

    assert result == []
    assert len(result) == 0
    mock_repo.batch_create.assert_called_once_with(products_data)


@pytest.mark.asyncio
async def test_create_products_use_case_repository_error():
    """Test batch product creation when repository raises an error."""
    mock_repo = AsyncMock()
    mock_repo.batch_create.side_effect = Exception("Database error")

    use_case = CreateProductsUseCase(mock_repo)
    products_data = [
        {
            "provider_id": "550e8400-e29b-41d4-a716-446655440000",
            "name": "Product 1",
            "category": ProductCategory.SPECIAL_MEDICATIONS.value,
            "sku": "SKU-ERROR-1",
            "price": 100.00,
        },
    ]

    with pytest.raises(Exception) as exc_info:
        await use_case.execute(products_data)

    assert str(exc_info.value) == "Database error"
    mock_repo.batch_create.assert_called_once_with(products_data)
