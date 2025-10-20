import pytest

from src.adapters.output.repositories.provider_repository import ProviderRepository


@pytest.mark.asyncio
async def test_create_provider(async_client):
    provider_data = {
        "name": "Test Provider",
        "nit": "123456789",
        "contact_name": "John Doe",
        "email": "john@test.com",
        "phone": "+1234567890",
        "address": "123 Test St",
        "country": "United States",
    }

    response = await async_client.post("/catalog/provider", json=provider_data)

    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["message"] == "Provider created successfully"


@pytest.mark.asyncio
async def test_list_providers_empty(async_client):
    response = await async_client.get("/catalog/providers")

    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0
    assert data["page"] == 1
    assert data["size"] == 0
    assert not data["has_next"]
    assert not data["has_previous"]


@pytest.mark.asyncio
async def test_list_providers_with_data(async_client, db_session):
    # Create test data
    repo = ProviderRepository(db_session)
    for i in range(5):
        await repo.create(
            {
                "name": f"Provider {i}",
                "nit": f"12345678{i}",
                "contact_name": f"Contact {i}",
                "email": f"contact{i}@test.com",
                "phone": f"+123456789{i}",
                "address": f"{i} Test St",
                "country": "US",
            }
        )

    response = await async_client.get("/catalog/providers?limit=2&offset=2")

    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 2
    assert data["total"] == 5
    assert data["page"] == 2
    assert data["size"] == 2
    assert data["has_next"]
    assert data["has_previous"]
