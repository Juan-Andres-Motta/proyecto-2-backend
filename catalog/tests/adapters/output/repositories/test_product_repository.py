import pytest

from src.adapters.output.repositories.product_repository import ProductRepository


@pytest.mark.asyncio
async def test_list_products_empty(db_session):
    repo = ProductRepository(db_session)
    products, total = await repo.list_products()

    assert products == []
    assert total == 0


@pytest.mark.asyncio
async def test_list_products_with_data(db_session):
    from src.adapters.output.repositories.provider_repository import (
        ProviderRepository,
    )
    from src.infrastructure.database.models import Product

    # First create a provider
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

    # Create some test products
    repo = ProductRepository(db_session)
    for i in range(5):
        product = Product(
            provider_id=provider.id,
            name=f"Product {i}",
            category="test_category",
            description=f"Description {i}",
            price=100.00 + i,
            status="active",
        )
        db_session.add(product)
    await db_session.commit()

    products, total = await repo.list_products(limit=3, offset=1)

    assert len(products) == 3
    assert total == 5
    assert products[0].name == "Product 1"


@pytest.mark.asyncio
async def test_list_products_pagination(db_session):
    from src.adapters.output.repositories.provider_repository import (
        ProviderRepository,
    )
    from src.infrastructure.database.models import Product

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

    repo = ProductRepository(db_session)
    for i in range(10):
        product = Product(
            provider_id=provider.id,
            name=f"Product {i}",
            category="test_category",
            description=f"Description {i}",
            price=100.00 + i,
            status="active",
        )
        db_session.add(product)
    await db_session.commit()

    # Test first page
    products, total = await repo.list_products(limit=5, offset=0)
    assert len(products) == 5
    assert total == 10

    # Test second page
    products, total = await repo.list_products(limit=5, offset=5)
    assert len(products) == 5
    assert total == 10
