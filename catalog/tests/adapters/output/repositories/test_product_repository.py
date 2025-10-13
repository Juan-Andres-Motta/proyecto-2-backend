import pytest

from src.adapters.output.repositories.product_repository import ProductRepository
from src.infrastructure.database.models import ProductCategory, ProductStatus


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
            category=ProductCategory.SPECIAL_MEDICATIONS.value,
            description=f"Description {i}",
            price=100.00 + i,
            status=ProductStatus.ACTIVE.value,
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
            category=ProductCategory.OTHER.value,
            description=f"Description {i}",
            price=100.00 + i,
            status=ProductStatus.ACTIVE.value,
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


@pytest.mark.asyncio
async def test_batch_create_products_success(db_session):
    """Test batch product creation with transaction support."""
    from src.adapters.output.repositories.provider_repository import (
        ProviderRepository,
    )

    # Create a provider
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

    # Prepare products data
    products_data = [
        {
            "provider_id": provider.id,
            "name": "Product 1",
            "category": ProductCategory.SPECIAL_MEDICATIONS.value,
            "description": "Description 1",
            "price": 100.00,
            "status": ProductStatus.ACTIVE.value,
        },
        {
            "provider_id": provider.id,
            "name": "Product 2",
            "category": ProductCategory.SURGICAL_SUPPLIES.value,
            "description": "Description 2",
            "price": 200.00,
            "status": ProductStatus.PENDING_APPROVAL.value,
        },
    ]

    # Create products in batch
    repo = ProductRepository(db_session)
    created_products = await repo.batch_create(products_data)

    assert len(created_products) == 2
    assert created_products[0].name == "Product 1"
    assert created_products[1].name == "Product 2"
    assert created_products[0].id is not None
    assert created_products[1].id is not None


@pytest.mark.asyncio
async def test_batch_create_products_rollback_on_error(db_session):
    """Test that batch creation rolls back all products on error."""
    from sqlalchemy.exc import IntegrityError
    import uuid

    # Prepare products data with one invalid (non-existent provider)
    invalid_provider_id = uuid.uuid4()
    products_data = [
        {
            "provider_id": invalid_provider_id,  # This will fail
            "name": "Product 1",
            "category": ProductCategory.SPECIAL_MEDICATIONS.value,
            "description": "Description 1",
            "price": 100.00,
            "status": ProductStatus.ACTIVE.value,
        },
    ]

    # Attempt batch creation - should fail and rollback
    repo = ProductRepository(db_session)
    with pytest.raises(IntegrityError):
        await repo.batch_create(products_data)

    # Verify no products were created (transaction rolled back)
    products, total = await repo.list_products()
    assert total == 0
