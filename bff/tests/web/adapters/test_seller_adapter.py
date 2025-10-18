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
            nit="123456789",
            contact_name="John Doe",
            email="john@test.com",
            phone="+1234567890",
            city="Test City",
            country="Test Country",
        )

        mock_http_client.post = AsyncMock(
            return_value={"id": "test-id", "message": "Created"}
        )

        await seller_adapter.create_seller(seller_data)

        mock_http_client.post.assert_called_once()
        call_args = mock_http_client.post.call_args
        assert call_args.args[0] == "/sellers"


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
        assert call_args.args[0] == "/sellers"


class TestSellerAdapterCreateSalesPlan:
    """Test create_sales_plan calls correct endpoint."""

    @pytest.mark.asyncio
    async def test_calls_correct_endpoint(self, seller_adapter, mock_http_client):
        """Test that POST /sales-plans is called."""
        sales_plan_data = SalesPlanCreate(
            seller_id=UUID("550e8400-e29b-41d4-a716-446655440000"),
            name="Test Plan",
            description="Test Description",
            sales_period="2025-Q1",
            goal=10000.0,
        )

        mock_http_client.post = AsyncMock(
            return_value={"id": "test-id", "message": "Created"}
        )

        await seller_adapter.create_sales_plan(sales_plan_data)

        mock_http_client.post.assert_called_once()
        call_args = mock_http_client.post.call_args
        assert call_args.args[0] == "/sales-plans"


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
        assert call_args.args[0] == "/sales-plans"


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
        assert call_args.args[0] == f"/sellers/{seller_id}/sales-plans"
