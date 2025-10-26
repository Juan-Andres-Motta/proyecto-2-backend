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


@pytest.mark.asyncio
async def test_find_by_id_database_error(db_session):
    """Test find_by_id with database error (covers exception handler lines 36-38)."""
    from unittest.mock import AsyncMock, patch

    repo = SellerRepository(db_session)

    # Mock session.execute to raise an exception
    with patch.object(db_session, 'execute', new_callable=AsyncMock) as mock_execute:
        mock_execute.side_effect = Exception("Database connection error")

        with pytest.raises(Exception) as exc_info:
            await repo.find_by_id(uuid.uuid4())

        assert "Database connection error" in str(exc_info.value)


@pytest.mark.asyncio
async def test_create_seller_database_error(db_session):
    """Test create seller with database error (covers exception handler lines 52-55)."""
    from unittest.mock import AsyncMock, patch

    repo = SellerRepository(db_session)

    seller_data = {
        "name": "test seller",
        "email": "test@example.com",
        "phone": "1234567890",
        "city": "miami",
        "country": "us"
    }

    # Mock session.commit to raise an exception
    with patch.object(db_session, 'commit', new_callable=AsyncMock) as mock_commit:
        mock_commit.side_effect = Exception("Database commit error")

        with pytest.raises(Exception) as exc_info:
            await repo.create(seller_data)

        assert "Database commit error" in str(exc_info.value)


@pytest.mark.asyncio
async def test_list_sellers_database_error(db_session):
    """Test list_sellers with database error (covers exception handler lines 76-78)."""
    from unittest.mock import AsyncMock, patch

    repo = SellerRepository(db_session)

    # Mock session.execute to raise an exception
    with patch.object(db_session, 'execute', new_callable=AsyncMock) as mock_execute:
        mock_execute.side_effect = Exception("Database query error")

        with pytest.raises(Exception) as exc_info:
            await repo.list_sellers(limit=10, offset=0)

        assert "Database query error" in str(exc_info.value)
