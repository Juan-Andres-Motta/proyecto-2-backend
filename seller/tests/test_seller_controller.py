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


@pytest.mark.asyncio
async def test_list_seller_sales_plans_empty(async_client, db_session):
    """Test listing sales plans for a seller with no plans."""
    # Create a seller
    repo = SellerRepository(db_session)
    seller = await repo.create(
        {
            "name": "test seller",
            "email": "seller@test.com",
            "phone": "+1234567890",
            "city": "test city",
            "country": "US",
        }
    )

    response = await async_client.get(f"/sellers/{seller.id}/sales-plans")

    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0
    assert data["page"] == 1
    assert data["size"] == 0
    assert not data["has_next"]
    assert not data["has_previous"]


@pytest.mark.asyncio
async def test_list_seller_sales_plans_with_data(async_client, db_session):
    """Test listing sales plans for a seller with data."""
    from decimal import Decimal

    from src.adapters.output.repositories.sales_plan_repository import (
        SalesPlanRepository,
    )
    from src.domain.entities.sales_plan import SalesPlan as DomainSalesPlan
    from src.domain.entities.seller import Seller as DomainSeller

    # Create two sellers
    seller_repo = SellerRepository(db_session)
    orm_seller1 = await seller_repo.create(
        {
            "name": "seller 1",
            "email": "seller1@test.com",
            "phone": "+1234567890",
            "city": "city 1",
            "country": "US",
        }
    )
    orm_seller2 = await seller_repo.create(
        {
            "name": "seller 2",
            "email": "seller2@test.com",
            "phone": "+0987654321",
            "city": "city 2",
            "country": "US",
        }
    )

    # Convert ORM sellers to domain entities
    domain_seller1 = DomainSeller(
        id=orm_seller1.id,
        name=orm_seller1.name,
        email=orm_seller1.email,
        phone=orm_seller1.phone,
        city=orm_seller1.city,
        country=orm_seller1.country,
        created_at=orm_seller1.created_at,
        updated_at=orm_seller1.updated_at
    )
    domain_seller2 = DomainSeller(
        id=orm_seller2.id,
        name=orm_seller2.name,
        email=orm_seller2.email,
        phone=orm_seller2.phone,
        city=orm_seller2.city,
        country=orm_seller2.country,
        created_at=orm_seller2.created_at,
        updated_at=orm_seller2.updated_at
    )

    # Create sales plans for both sellers
    sales_plan_repo = SalesPlanRepository(db_session)
    # 3 plans for seller1
    for i in range(3):
        sales_plan = DomainSalesPlan.create_new(
            seller=domain_seller1,
            sales_period=f"Q{i+1}-2024",
            goal=Decimal(f"{10000 * (i+1)}.00"),
        )
        await sales_plan_repo.create(sales_plan)

    # 2 plans for seller2
    for i in range(2):
        sales_plan = DomainSalesPlan.create_new(
            seller=domain_seller2,
            sales_period=f"Q{i+1}-2024",
            goal=Decimal(f"{20000 * (i+1)}.00"),
        )
        await sales_plan_repo.create(sales_plan)

    # Get sales plans for seller1
    response = await async_client.get(f"/sellers/{orm_seller1.id}/sales-plans")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 3
    assert data["total"] == 3
    assert all(item["seller"]["id"] == str(orm_seller1.id) for item in data["items"])

    # Get sales plans for seller2
    response = await async_client.get(f"/sellers/{orm_seller2.id}/sales-plans")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 2
    assert data["total"] == 2
    assert all(item["seller"]["id"] == str(orm_seller2.id) for item in data["items"])


@pytest.mark.asyncio
async def test_list_seller_sales_plans_pagination(async_client, db_session):
    """Test pagination of sales plans for a seller."""
    from decimal import Decimal

    from src.adapters.output.repositories.sales_plan_repository import (
        SalesPlanRepository,
    )
    from src.domain.entities.sales_plan import SalesPlan as DomainSalesPlan
    from src.domain.entities.seller import Seller as DomainSeller

    # Create a seller
    seller_repo = SellerRepository(db_session)
    orm_seller = await seller_repo.create(
        {
            "name": "test seller",
            "email": "seller@test.com",
            "phone": "+1234567890",
            "city": "test city",
            "country": "US",
        }
    )

    # Convert to domain entity
    domain_seller = DomainSeller(
        id=orm_seller.id,
        name=orm_seller.name,
        email=orm_seller.email,
        phone=orm_seller.phone,
        city=orm_seller.city,
        country=orm_seller.country,
        created_at=orm_seller.created_at,
        updated_at=orm_seller.updated_at
    )

    # Create 5 sales plans for the seller
    sales_plan_repo = SalesPlanRepository(db_session)
    for i in range(5):
        sales_plan = DomainSalesPlan.create_new(
            seller=domain_seller,
            sales_period=f"Q{i+1}-2024",
            goal=Decimal(f"{10000 * (i+1)}.00"),
        )
        await sales_plan_repo.create(sales_plan)

    # Get first page
    response = await async_client.get(
        f"/sellers/{orm_seller.id}/sales-plans?limit=2&offset=0"
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 2
    assert data["total"] == 5
    assert data["page"] == 1
    assert data["size"] == 2
    assert data["has_next"]
    assert not data["has_previous"]

    # Get second page
    response = await async_client.get(
        f"/sellers/{orm_seller.id}/sales-plans?limit=2&offset=2"
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 2
    assert data["total"] == 5
    assert data["page"] == 2
    assert data["size"] == 2
    assert data["has_next"]
    assert data["has_previous"]
