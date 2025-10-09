import pytest
from httpx import ASGITransport, AsyncClient


@pytest.mark.asyncio
async def test_list_products_empty(db_session):
    from fastapi import FastAPI

    from src.adapters.input.controllers.product_controller import router
    from src.infrastructure.database.config import get_db

    app = FastAPI()
    app.include_router(router)

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/products")

    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0
    assert data["page"] == 1
    assert data["size"] == 0
    assert data["has_next"] is False
    assert data["has_previous"] is False


@pytest.mark.asyncio
async def test_list_products_with_data(db_session):
    from fastapi import FastAPI

    from src.adapters.input.controllers.product_controller import router
    from src.adapters.output.repositories.provider_repository import (
        ProviderRepository,
    )
    from src.infrastructure.database.config import get_db
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
            description=f"Description {i}",
            price=100.00 + i,
            status="active",
        )
        db_session.add(product)
    await db_session.commit()

    app = FastAPI()
    app.include_router(router)

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/products?limit=3&offset=1")

    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 3
    assert data["total"] == 5
    assert data["page"] == 1  # (1 // 3) + 1 = 1
    assert data["has_next"] is True
    assert data["has_previous"] is True


@pytest.mark.asyncio
async def test_list_products_validation(db_session):
    from fastapi import FastAPI

    from src.adapters.input.controllers.product_controller import router
    from src.infrastructure.database.config import get_db

    app = FastAPI()
    app.include_router(router)

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        # Test invalid limit (too high)
        response = await client.get("/products?limit=101")
        assert response.status_code == 422

        # Test invalid offset (negative)
        response = await client.get("/products?offset=-1")
        assert response.status_code == 422
