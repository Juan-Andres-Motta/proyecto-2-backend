import pytest
from decimal import Decimal
from uuid import uuid4

from src.adapters.output.repositories.product_repository import ProductRepository
from src.application.use_cases.get_product import GetProductUseCase


@pytest.mark.asyncio
async def test_get_product_not_found(db_session):
    """Test getting a product that doesn't exist."""
    repo = ProductRepository(db_session)
    use_case = GetProductUseCase(repo)

    # Use a random UUID that doesn't exist
    product_id = uuid4()
    product = await use_case.execute(product_id)

    assert product is None


@pytest.mark.asyncio
async def test_get_product_success(db_session):
    """Test getting a product that exists."""
    from src.adapters.output.repositories.provider_repository import (
        ProviderRepository,
    )
    from src.infrastructure.database.models import Product

    # Create provider
    provider_repo = ProviderRepository(db_session)
    provider = await provider_repo.create(
        {
            "name": "Test Provider",
            "nit": "123456789",
            "contact_name": "John Doe",
            "email": "john@test.com",
            "phone": "+1234567890",
            "address": "123 Test St",
            "country": "US",
        }
    )

    # Create product
    product = Product(
        provider_id=provider.id,
        name="Test Product",
        category="test_category",
        sku="SKU-GET-TEST",
        price=99.99,
    )
    db_session.add(product)
    await db_session.commit()
    await db_session.refresh(product)

    # Test use case
    repo = ProductRepository(db_session)
    use_case = GetProductUseCase(repo)

    result = await use_case.execute(product.id)

    assert result is not None
    assert result.id == product.id
    assert result.name == "Test Product"
    assert result.sku == "SKU-GET-TEST"
    assert result.price == Decimal("99.99")
    assert result.provider_id == provider.id
