import pytest

from src.adapters.output.repositories.seller_repository import SellerRepository


@pytest.mark.asyncio
async def test_create_seller(async_client):
    seller_data = {
        "name": "Test Seller",
        "email": "seller@test.com",
        "phone": "+1234567890",
        "city": "Test City",
        "country": "United States",
    }

    response = await async_client.post("/sellers", json=seller_data)

    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["message"] == "Seller created successfully"


@pytest.mark.asyncio
async def test_list_sellers_empty(async_client):
    response = await async_client.get("/sellers")

    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0
    assert data["page"] == 1
    assert data["size"] == 0
    assert not data["has_next"]
    assert not data["has_previous"]


@pytest.mark.asyncio
async def test_list_sellers_with_data(async_client, db_session):
    # Create test data
    repo = SellerRepository(db_session)
    for i in range(5):
        await repo.create(
            {
                "name": f"Seller {i}",
                "email": f"seller{i}@test.com",
                "phone": f"+123456789{i}",
                "city": f"City {i}",
                "country": "US",
            }
        )

    response = await async_client.get("/sellers?limit=2&offset=2")

    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 2
    assert data["total"] == 5
    assert data["page"] == 2
    assert data["size"] == 2
    assert data["has_next"]
    assert data["has_previous"]
