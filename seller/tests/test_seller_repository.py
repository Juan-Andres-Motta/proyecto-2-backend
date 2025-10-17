"""Unit tests for SellerRepository."""
import uuid

import pytest

from src.adapters.output.repositories.seller_repository import SellerRepository


@pytest.mark.asyncio
async def test_create_seller(db_session):
    """Test creating a seller."""
    repo = SellerRepository(db_session)

    seller_data = {
        "name": "john doe",
        "email": "john@example.com",
        "phone": "1234567890",
        "city": "miami",
        "country": "us"
    }

    created = await repo.create(seller_data)

    assert created.id is not None
    assert created.name == "john doe"
    assert created.email == "john@example.com"


@pytest.mark.asyncio
async def test_find_by_id_exists(db_session):
    """Test finding seller that exists."""
    repo = SellerRepository(db_session)

    seller_data = {
        "name": "jane doe",
        "email": "jane@example.com",
        "phone": "9876543210",
        "city": "new york",
        "country": "us"
    }
    created = await repo.create(seller_data)

    found = await repo.find_by_id(created.id)
    assert found is not None
    assert found.email == "jane@example.com"


@pytest.mark.asyncio
async def test_find_by_id_not_exists(db_session):
    """Test finding seller that doesn't exist."""
    repo = SellerRepository(db_session)

    not_found = await repo.find_by_id(uuid.uuid4())
    assert not_found is None


@pytest.mark.asyncio
async def test_list_sellers(db_session):
    """Test listing sellers with pagination."""
    repo = SellerRepository(db_session)

    # Create 3 sellers
    for i in range(3):
        seller_data = {
            "name": f"seller {i}",
            "email": f"seller{i}@example.com",
            "phone": f"12345678{i}0",
            "city": "miami",
            "country": "us"
        }
        await repo.create(seller_data)

    sellers, total = await repo.list_sellers(limit=10, offset=0)
    assert total == 3
    assert len(sellers) == 3

    # Test pagination
    sellers, total = await repo.list_sellers(limit=2, offset=1)
    assert total == 3
    assert len(sellers) == 2
