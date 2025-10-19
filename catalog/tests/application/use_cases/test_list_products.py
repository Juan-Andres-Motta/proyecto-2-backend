import pytest

from src.adapters.output.repositories.product_repository import ProductRepository
from src.application.use_cases.list_products import ListProductsUseCase


@pytest.mark.asyncio
async def test_list_products_use_case_empty(db_session):
    repo = ProductRepository(db_session)
    use_case = ListProductsUseCase(repo)

    products, total = await use_case.execute()

    assert products == []
    assert total == 0


@pytest.mark.asyncio
async def test_list_products_use_case_with_data(db_session):
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

    # Create products
    for i in range(5):
        product = Product(
            provider_id=provider.id,
            name=f"Product {i}",
            category="test_category",
            sku=f"SKU-LIST-{i}",
            price=100.00 + i,
        )
        db_session.add(product)
    await db_session.commit()

    repo = ProductRepository(db_session)
    use_case = ListProductsUseCase(repo)

    products, total = await use_case.execute(limit=3, offset=1)

    assert len(products) == 3
    assert total == 5
    # Verify provider_name is included
    assert all(hasattr(p, "provider_name") for p in products)
    assert products[0].provider_name == "Test Provider"


@pytest.mark.asyncio
async def test_list_products_use_case_default_pagination(db_session):
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

    for i in range(15):
        product = Product(
            provider_id=provider.id,
            name=f"Product {i}",
            category="test_category",
            sku=f"SKU-DEFAULT-{i}",
            price=100.00 + i,
        )
        db_session.add(product)
    await db_session.commit()

    repo = ProductRepository(db_session)
    use_case = ListProductsUseCase(repo)

    products, total = await use_case.execute()

    assert len(products) == 10  # Default limit
    assert total == 15
    # Verify provider_name is included
    assert all(hasattr(p, "provider_name") for p in products)
    assert products[0].provider_name == "Test Provider"
