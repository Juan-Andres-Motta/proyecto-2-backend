import pytest

from src.adapters.output.repositories.seller_repository import SellerRepository


@pytest.mark.asyncio
async def test_create_seller(db_session):
    repo = SellerRepository(db_session)
    seller_data = {
        "name": "Test Seller",
        "email": "seller@test.com",
        "phone": "+1234567890",
        "city": "Test City",
        "country": "US",
    }

    seller = await repo.create(seller_data)

    assert seller.id is not None
    assert seller.name == "Test Seller"
    assert seller.email == "seller@test.com"


@pytest.mark.asyncio
async def test_list_sellers_empty(db_session):
    repo = SellerRepository(db_session)
    sellers, total = await repo.list_sellers()

    assert sellers == []
    assert total == 0


@pytest.mark.asyncio
async def test_list_sellers_with_data(db_session):
    repo = SellerRepository(db_session)

    # Create some test data
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

    sellers, total = await repo.list_sellers(limit=3, offset=1)

    assert len(sellers) == 3
    assert total == 5
    assert sellers[0].name == "Seller 1"
