from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from web.controllers.sellers_controller import router


@pytest.mark.asyncio
async def test_create_seller_success():
    """Test successful seller creation."""
    app = FastAPI()
    app.include_router(router)

    seller_data = {
        "name": "john doe",
        "email": "john@example.com",
        "phone": "1234567890",
        "city": "miami",
        "country": "US",
    }

    mock_response = {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "message": "Seller created successfully",
    }

    with patch("web.controllers.sellers_controller.SellerService") as MockSellerService:
        mock_service = MockSellerService.return_value
        mock_service.create_seller = AsyncMock(return_value=mock_response)

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post("/sellers", json=seller_data)

        assert response.status_code == 201
        data = response.json()
        assert data["id"] == "550e8400-e29b-41d4-a716-446655440000"
        assert data["message"] == "Seller created successfully"


@pytest.mark.asyncio
async def test_create_seller_service_error():
    """Test seller creation when service raises an error."""
    app = FastAPI()
    app.include_router(router)

    seller_data = {
        "name": "john doe",
        "email": "john@example.com",
        "phone": "1234567890",
        "city": "miami",
        "country": "US",
    }

    with patch("web.controllers.sellers_controller.SellerService") as MockSellerService:
        mock_service = MockSellerService.return_value
        mock_service.create_seller = AsyncMock(side_effect=Exception("Service unavailable"))

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post("/sellers", json=seller_data)

        assert response.status_code == 500
        assert "error" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_get_sellers_success():
    """Test successful sellers retrieval."""
    app = FastAPI()
    app.include_router(router)

    mock_sellers_data = {
        "items": [
            {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "john doe",
                "email": "john@example.com",
                "phone": "1234567890",
                "city": "miami",
                "country": "us",
                "created_at": "2025-01-15T10:30:00Z",
                "updated_at": "2025-01-15T10:30:00Z",
            }
        ],
        "total": 1,
        "page": 1,
        "size": 1,
        "has_next": False,
        "has_previous": False,
    }

    with patch("web.controllers.sellers_controller.SellerService") as MockSellerService:
        mock_service = MockSellerService.return_value
        mock_service.get_sellers = AsyncMock(return_value=mock_sellers_data)

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/sellers")

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert len(data["items"]) == 1


@pytest.mark.asyncio
async def test_get_sellers_all():
    """Test get all sellers without pagination."""
    app = FastAPI()
    app.include_router(router)

    mock_sellers_data = [
        {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "name": "john doe",
            "email": "john@example.com",
            "phone": "1234567890",
            "city": "miami",
            "country": "us",
            "created_at": "2025-01-15T10:30:00Z",
            "updated_at": "2025-01-15T10:30:00Z",
        }
    ]

    with patch("web.controllers.sellers_controller.SellerService") as MockSellerService:
        mock_service = MockSellerService.return_value
        mock_service.get_sellers = AsyncMock(return_value=mock_sellers_data)

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/sellers?all=true")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1


@pytest.mark.asyncio
async def test_get_sellers_with_pagination():
    """Test sellers retrieval with custom pagination."""
    app = FastAPI()
    app.include_router(router)

    mock_sellers_data = {"items": [], "total": 0, "page": 1, "size": 0, "has_next": False, "has_previous": False}

    with patch("web.controllers.sellers_controller.SellerService") as MockSellerService:
        mock_service = MockSellerService.return_value
        mock_service.get_sellers = AsyncMock(return_value=mock_sellers_data)

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/sellers?limit=5&offset=10")

        assert response.status_code == 200
        mock_service.get_sellers.assert_called_once_with(limit=5, offset=10, all=False)


@pytest.mark.asyncio
async def test_get_sellers_service_error():
    """Test sellers retrieval when service raises an error."""
    app = FastAPI()
    app.include_router(router)

    with patch("web.controllers.sellers_controller.SellerService") as MockSellerService:
        mock_service = MockSellerService.return_value
        mock_service.get_sellers = AsyncMock(side_effect=Exception("Service unavailable"))

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/sellers")

        assert response.status_code == 500
        assert "error" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_get_sellers_validation():
    """Test sellers endpoint parameter validation."""
    app = FastAPI()
    app.include_router(router)

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        # Test limit too high
        response = await client.get("/sellers?limit=101")
        assert response.status_code == 422

        # Test limit too low
        response = await client.get("/sellers?limit=0")
        assert response.status_code == 422

        # Test negative offset
        response = await client.get("/sellers?offset=-1")
        assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_seller_sales_plans_success():
    """Test successful seller sales plans retrieval."""
    app = FastAPI()
    app.include_router(router)

    seller_id = "550e8400-e29b-41d4-a716-446655440000"
    mock_sales_plans_data = {
        "items": [
            {
                "id": "660e8400-e29b-41d4-a716-446655440000",
                "seller_id": "550e8400-e29b-41d4-a716-446655440000",
                "sales_period": "Q1_2024",
                "goal_type": "sales",
                "goal": "100000.00",
                "accumulate": "25000.00",
                "status": "active",
                "created_at": "2025-01-15T10:30:00Z",
                "updated_at": "2025-01-15T10:30:00Z",
            }
        ],
        "total": 1,
        "page": 1,
        "size": 1,
        "has_next": False,
        "has_previous": False,
    }

    with patch("web.controllers.sellers_controller.SellerService") as MockSellerService:
        mock_service = MockSellerService.return_value
        mock_service.get_seller_sales_plans = AsyncMock(return_value=mock_sales_plans_data)

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get(f"/sellers/{seller_id}/sales-plans")

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert len(data["items"]) == 1
        assert data["items"][0]["seller_id"] == seller_id


@pytest.mark.asyncio
async def test_get_seller_sales_plans_empty():
    """Test seller sales plans retrieval when seller has no plans."""
    app = FastAPI()
    app.include_router(router)

    seller_id = "550e8400-e29b-41d4-a716-446655440000"
    mock_sales_plans_data = {
        "items": [],
        "total": 0,
        "page": 1,
        "size": 0,
        "has_next": False,
        "has_previous": False,
    }

    with patch("web.controllers.sellers_controller.SellerService") as MockSellerService:
        mock_service = MockSellerService.return_value
        mock_service.get_seller_sales_plans = AsyncMock(return_value=mock_sales_plans_data)

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get(f"/sellers/{seller_id}/sales-plans")

        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0


@pytest.mark.asyncio
async def test_get_seller_sales_plans_with_pagination():
    """Test seller sales plans retrieval with custom pagination."""
    app = FastAPI()
    app.include_router(router)

    seller_id = "550e8400-e29b-41d4-a716-446655440000"
    mock_sales_plans_data = {
        "items": [],
        "total": 0,
        "page": 1,
        "size": 0,
        "has_next": False,
        "has_previous": False,
    }

    with patch("web.controllers.sellers_controller.SellerService") as MockSellerService:
        mock_service = MockSellerService.return_value
        mock_service.get_seller_sales_plans = AsyncMock(return_value=mock_sales_plans_data)

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get(f"/sellers/{seller_id}/sales-plans?limit=5&offset=10")

        assert response.status_code == 200
        mock_service.get_seller_sales_plans.assert_called_once_with(
            seller_id=seller_id, limit=5, offset=10
        )


@pytest.mark.asyncio
async def test_get_seller_sales_plans_service_error():
    """Test seller sales plans retrieval when service raises an error."""
    app = FastAPI()
    app.include_router(router)

    seller_id = "550e8400-e29b-41d4-a716-446655440000"

    with patch("web.controllers.sellers_controller.SellerService") as MockSellerService:
        mock_service = MockSellerService.return_value
        mock_service.get_seller_sales_plans = AsyncMock(
            side_effect=Exception("Service unavailable")
        )

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get(f"/sellers/{seller_id}/sales-plans")

        assert response.status_code == 500
        assert "error" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_get_seller_sales_plans_invalid_uuid():
    """Test seller sales plans endpoint with invalid seller UUID."""
    app = FastAPI()
    app.include_router(router)

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        # Test invalid UUID
        response = await client.get("/sellers/invalid-uuid/sales-plans")
        assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_seller_sales_plans_validation():
    """Test seller sales plans endpoint parameter validation."""
    app = FastAPI()
    app.include_router(router)

    seller_id = "550e8400-e29b-41d4-a716-446655440000"

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        # Test limit too high
        response = await client.get(f"/sellers/{seller_id}/sales-plans?limit=101")
        assert response.status_code == 422

        # Test limit too low
        response = await client.get(f"/sellers/{seller_id}/sales-plans?limit=0")
        assert response.status_code == 422

        # Test negative offset
        response = await client.get(f"/sellers/{seller_id}/sales-plans?offset=-1")
        assert response.status_code == 422
