from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from web.controllers.sales_plans_controller import router


@pytest.mark.asyncio
async def test_create_sales_plan_success():
    """Test successful sales plan creation."""
    app = FastAPI()
    app.include_router(router)

    sales_plan_data = {
        "seller_id": "550e8400-e29b-41d4-a716-446655440000",
        "sales_period": "Q1_2024",
        "goal_type": "sales",
        "goal": "100000.00",
        "accumulate": "25000.00",
        "status": "active",
    }

    mock_response = {
        "id": "660e8400-e29b-41d4-a716-446655440000",
        "message": "Sales plan created successfully",
    }

    with patch("web.controllers.sales_plans_controller.SellerService") as MockSellerService:
        mock_service = MockSellerService.return_value
        mock_service.create_sales_plan = AsyncMock(return_value=mock_response)

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post("/sales-plans", json=sales_plan_data)

        assert response.status_code == 201
        data = response.json()
        assert data["id"] == "660e8400-e29b-41d4-a716-446655440000"
        assert data["message"] == "Sales plan created successfully"


@pytest.mark.asyncio
async def test_create_sales_plan_service_error():
    """Test sales plan creation when service raises an error."""
    app = FastAPI()
    app.include_router(router)

    sales_plan_data = {
        "seller_id": "550e8400-e29b-41d4-a716-446655440000",
        "sales_period": "Q1_2024",
        "goal_type": "sales",
        "goal": "100000.00",
        "accumulate": "25000.00",
        "status": "active",
    }

    with patch("web.controllers.sales_plans_controller.SellerService") as MockSellerService:
        mock_service = MockSellerService.return_value
        mock_service.create_sales_plan = AsyncMock(
            side_effect=Exception("Service unavailable")
        )

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post("/sales-plans", json=sales_plan_data)

        assert response.status_code == 500
        assert "error" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_get_sales_plans_success():
    """Test successful sales plans retrieval."""
    app = FastAPI()
    app.include_router(router)

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

    with patch("web.controllers.sales_plans_controller.SellerService") as MockSellerService:
        mock_service = MockSellerService.return_value
        mock_service.get_sales_plans = AsyncMock(return_value=mock_sales_plans_data)

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/sales-plans")

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert len(data["items"]) == 1


@pytest.mark.asyncio
async def test_get_sales_plans_with_pagination():
    """Test sales plans retrieval with custom pagination."""
    app = FastAPI()
    app.include_router(router)

    mock_sales_plans_data = {
        "items": [],
        "total": 0,
        "page": 1,
        "size": 0,
        "has_next": False,
        "has_previous": False,
    }

    with patch("web.controllers.sales_plans_controller.SellerService") as MockSellerService:
        mock_service = MockSellerService.return_value
        mock_service.get_sales_plans = AsyncMock(return_value=mock_sales_plans_data)

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/sales-plans?limit=5&offset=10")

        assert response.status_code == 200
        mock_service.get_sales_plans.assert_called_once_with(limit=5, offset=10)


@pytest.mark.asyncio
async def test_get_sales_plans_service_error():
    """Test sales plans retrieval when service raises an error."""
    app = FastAPI()
    app.include_router(router)

    with patch("web.controllers.sales_plans_controller.SellerService") as MockSellerService:
        mock_service = MockSellerService.return_value
        mock_service.get_sales_plans = AsyncMock(
            side_effect=Exception("Service unavailable")
        )

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/sales-plans")

        assert response.status_code == 500
        assert "error" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_get_sales_plans_validation():
    """Test sales plans endpoint parameter validation."""
    app = FastAPI()
    app.include_router(router)

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        # Test limit too high
        response = await client.get("/sales-plans?limit=101")
        assert response.status_code == 422

        # Test limit too low
        response = await client.get("/sales-plans?limit=0")
        assert response.status_code == 422

        # Test negative offset
        response = await client.get("/sales-plans?offset=-1")
        assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_sales_plan_missing_fields():
    """Test sales plan creation with missing required fields."""
    app = FastAPI()
    app.include_router(router)

    sales_plan_data = {
        "sales_period": "Q1_2024",
        "goal_type": "sales",
    }

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post("/sales-plans", json=sales_plan_data)

    assert response.status_code == 422
