from unittest.mock import AsyncMock, patch

import httpx
import pytest

from web.services.seller_service import SellerService


@pytest.mark.asyncio
async def test_create_seller_success():
    """Test successful seller creation."""
    service = SellerService()

    seller_data = {
        "name": "john doe",
        "email": "john@example.com",
        "phone": "1234567890",
        "city": "miami",
        "country": "us",
    }

    mock_response = {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "message": "Seller created successfully",
    }

    with patch("httpx.AsyncClient.post") as mock_post:
        mock_post.return_value = AsyncMock(
            status_code=201,
            json=lambda: mock_response,
        )
        mock_post.return_value.raise_for_status = lambda: None

        result = await service.create_seller(seller_data)

        assert result == mock_response
        assert "id" in result
        assert result["message"] == "Seller created successfully"


@pytest.mark.asyncio
async def test_create_seller_http_error():
    """Test seller creation with HTTP error."""
    service = SellerService()

    seller_data = {
        "name": "john doe",
        "email": "john@example.com",
        "phone": "1234567890",
        "city": "miami",
        "country": "us",
    }

    with patch("httpx.AsyncClient.post") as mock_post:
        mock_response = AsyncMock(status_code=500)

        def raise_error():
            raise httpx.HTTPStatusError(
                "Internal Server Error",
                request=AsyncMock(),
                response=AsyncMock(status_code=500),
            )

        mock_response.raise_for_status = raise_error
        mock_post.return_value = mock_response

        with pytest.raises(httpx.HTTPStatusError):
            await service.create_seller(seller_data)


@pytest.mark.asyncio
async def test_get_sellers_success():
    """Test successful sellers retrieval."""
    service = SellerService()

    mock_response = {
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

    with patch("httpx.AsyncClient.get") as mock_get:
        mock_get.return_value = AsyncMock(
            status_code=200,
            json=lambda: mock_response,
        )
        mock_get.return_value.raise_for_status = lambda: None

        result = await service.get_sellers(limit=10, offset=0)

        assert result == mock_response
        assert len(result["items"]) == 1


@pytest.mark.asyncio
async def test_get_sellers_all():
    """Test get all sellers without pagination."""
    service = SellerService()

    mock_response = [
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

    with patch("httpx.AsyncClient.get") as mock_get:
        mock_get.return_value = AsyncMock(
            status_code=200,
            json=lambda: mock_response,
        )
        mock_get.return_value.raise_for_status = lambda: None

        result = await service.get_sellers(limit=10, offset=0, all=True)

        assert result == mock_response
        assert len(result) == 1


@pytest.mark.asyncio
async def test_create_sales_plan_success():
    """Test successful sales plan creation."""
    service = SellerService()

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

    with patch("httpx.AsyncClient.post") as mock_post:
        mock_post.return_value = AsyncMock(
            status_code=201,
            json=lambda: mock_response,
        )
        mock_post.return_value.raise_for_status = lambda: None

        result = await service.create_sales_plan(sales_plan_data)

        assert result == mock_response
        assert "id" in result
        assert result["message"] == "Sales plan created successfully"


@pytest.mark.asyncio
async def test_get_sales_plans_success():
    """Test successful sales plans retrieval."""
    service = SellerService()

    mock_response = {
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

    with patch("httpx.AsyncClient.get") as mock_get:
        mock_get.return_value = AsyncMock(
            status_code=200,
            json=lambda: mock_response,
        )
        mock_get.return_value.raise_for_status = lambda: None

        result = await service.get_sales_plans(limit=10, offset=0)

        assert result == mock_response
        assert len(result["items"]) == 1


@pytest.mark.asyncio
async def test_get_sales_plans_http_error():
    """Test sales plans retrieval with HTTP error."""
    service = SellerService()

    with patch("httpx.AsyncClient.get") as mock_get:
        mock_response = AsyncMock(status_code=500)

        def raise_error():
            raise httpx.HTTPStatusError(
                "Internal Server Error",
                request=AsyncMock(),
                response=AsyncMock(status_code=500),
            )

        mock_response.raise_for_status = raise_error
        mock_get.return_value = mock_response

        with pytest.raises(httpx.HTTPStatusError):
            await service.get_sales_plans()


@pytest.mark.asyncio
async def test_get_seller_sales_plans_success():
    """Test successful seller sales plans retrieval."""
    service = SellerService()

    seller_id = "550e8400-e29b-41d4-a716-446655440000"
    mock_response = {
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

    with patch("httpx.AsyncClient.get") as mock_get:
        mock_get.return_value = AsyncMock(
            status_code=200,
            json=lambda: mock_response,
        )
        mock_get.return_value.raise_for_status = lambda: None

        result = await service.get_seller_sales_plans(seller_id=seller_id, limit=10, offset=0)

        assert result == mock_response
        assert len(result["items"]) == 1
        assert result["items"][0]["seller_id"] == seller_id


@pytest.mark.asyncio
async def test_get_seller_sales_plans_empty():
    """Test seller sales plans retrieval when seller has no plans."""
    service = SellerService()

    seller_id = "550e8400-e29b-41d4-a716-446655440000"
    mock_response = {
        "items": [],
        "total": 0,
        "page": 1,
        "size": 0,
        "has_next": False,
        "has_previous": False,
    }

    with patch("httpx.AsyncClient.get") as mock_get:
        mock_get.return_value = AsyncMock(
            status_code=200,
            json=lambda: mock_response,
        )
        mock_get.return_value.raise_for_status = lambda: None

        result = await service.get_seller_sales_plans(seller_id=seller_id, limit=10, offset=0)

        assert result == mock_response
        assert len(result["items"]) == 0


@pytest.mark.asyncio
async def test_get_seller_sales_plans_http_error():
    """Test seller sales plans retrieval with HTTP error."""
    service = SellerService()

    seller_id = "550e8400-e29b-41d4-a716-446655440000"

    with patch("httpx.AsyncClient.get") as mock_get:
        mock_response = AsyncMock(status_code=500)

        def raise_error():
            raise httpx.HTTPStatusError(
                "Internal Server Error",
                request=AsyncMock(),
                response=AsyncMock(status_code=500),
            )

        mock_response.raise_for_status = raise_error
        mock_get.return_value = mock_response

        with pytest.raises(httpx.HTTPStatusError):
            await service.get_seller_sales_plans(seller_id=seller_id)
