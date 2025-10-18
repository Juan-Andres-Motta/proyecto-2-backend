"""
Unit tests for SellerAdapter.

Tests OUR logic:
- Calling correct HTTP endpoints
"""

from unittest.mock import AsyncMock, Mock
from uuid import UUID

import pytest

from web.adapters.seller_adapter import SellerAdapter
from web.adapters.http_client import HttpClient
from web.schemas.seller_schemas import SellerCreate, SalesPlanCreate


@pytest.fixture
def mock_http_client():
    """Create a mock HTTP client."""
    return Mock(spec=HttpClient)


@pytest.fixture
def seller_adapter(mock_http_client):
    """Create a seller adapter with mock HTTP client."""
    return SellerAdapter(mock_http_client)


class TestSellerAdapterCreateSeller:
    """Test create_seller calls correct endpoint."""

    @pytest.mark.asyncio
    async def test_calls_correct_endpoint(self, seller_adapter, mock_http_client):
        """Test that POST /sellers is called."""
        seller_data = SellerCreate(
            name="Test Seller",
            email="john@test.com",
            phone="+1234567890",
            city="Test City",
            country="CO",
        )

        mock_http_client.post = AsyncMock(
            return_value={"id": "test-id", "message": "Created"}
        )

        await seller_adapter.create_seller(seller_data)

        mock_http_client.post.assert_called_once()
        call_args = mock_http_client.post.call_args
        assert call_args.args[0] == "/seller/sellers"


class TestSellerAdapterGetSellers:
    """Test get_sellers calls correct endpoint."""

    @pytest.mark.asyncio
    async def test_calls_correct_endpoint(self, seller_adapter, mock_http_client):
        """Test that GET /sellers is called."""
        mock_http_client.get = AsyncMock(
            return_value={
                "items": [],
                "total": 0,
                "page": 1,
                "size": 10,
                "has_next": False,
                "has_previous": False,
            }
        )

        await seller_adapter.get_sellers()

        mock_http_client.get.assert_called_once()
        call_args = mock_http_client.get.call_args
        assert call_args.args[0] == "/seller/sellers"


class TestSellerAdapterCreateSalesPlan:
    """Test create_sales_plan calls correct endpoint."""

    @pytest.mark.asyncio
    async def test_calls_correct_endpoint(self, seller_adapter, mock_http_client):
        """Test that POST /sales-plans is called and response is parsed correctly."""
        sales_plan_data = SalesPlanCreate(
            seller_id=UUID("550e8400-e29b-41d4-a716-446655440000"),
            sales_period="Q1-2025",
            goal=10000.0,
        )

        # Mock seller service response - returns full sales plan object
        mock_http_client.post = AsyncMock(
            return_value={
                "id": "test-id",
                "seller": {
                    "id": "550e8400-e29b-41d4-a716-446655440000",
                    "name": "Test Seller",
                    "email": "test@example.com",
                    "phone": "1234567890",
                    "city": "Test City",
                    "country": "CO",
                    "created_at": "2025-10-18T00:00:00Z",
                    "updated_at": "2025-10-18T00:00:00Z"
                },
                "sales_period": "Q1-2025",
                "goal": "10000.00",
                "accumulate": "0.00",
                "status": "in_progress",
                "created_at": "2025-10-18T00:00:00Z",
                "updated_at": "2025-10-18T00:00:00Z"
            }
        )

        result = await seller_adapter.create_sales_plan(sales_plan_data)

        mock_http_client.post.assert_called_once()
        call_args = mock_http_client.post.call_args
        assert call_args.args[0] == "/seller/sales-plans"

        # Verify adapter extracts id and constructs response correctly
        assert result.id == "test-id"
        assert result.message == "Sales plan created successfully"


class TestSellerAdapterGetSalesPlans:
    """Test get_sales_plans calls correct endpoint."""

    @pytest.mark.asyncio
    async def test_calls_correct_endpoint(self, seller_adapter, mock_http_client):
        """Test that GET /sales-plans is called."""
        mock_http_client.get = AsyncMock(
            return_value={
                "items": [],
                "total": 0,
                "page": 1,
                "size": 10,
                "has_next": False,
                "has_previous": False,
            }
        )

        await seller_adapter.get_sales_plans()

        mock_http_client.get.assert_called_once()
        call_args = mock_http_client.get.call_args
        assert call_args.args[0] == "/seller/sales-plans"


class TestSellerAdapterGetSellerSalesPlans:
    """Test get_seller_sales_plans calls correct endpoint."""

    @pytest.mark.asyncio
    async def test_calls_correct_endpoint(self, seller_adapter, mock_http_client):
        """Test that GET /sellers/{id}/sales-plans is called."""
        seller_id = UUID("550e8400-e29b-41d4-a716-446655440000")

        mock_http_client.get = AsyncMock(
            return_value={
                "items": [],
                "total": 0,
                "page": 1,
                "size": 10,
                "has_next": False,
                "has_previous": False,
            }
        )

        await seller_adapter.get_seller_sales_plans(seller_id)

        mock_http_client.get.assert_called_once()
        call_args = mock_http_client.get.call_args
        assert call_args.args[0] == f"/seller/sellers/{seller_id}/sales-plans"
