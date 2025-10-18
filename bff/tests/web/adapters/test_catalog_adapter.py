"""
Unit tests for CatalogAdapter.

Tests OUR logic:
- Calling correct HTTP endpoints
- Passing correct data to HTTP client
"""

from unittest.mock import AsyncMock, Mock
from uuid import UUID
from decimal import Decimal

import pytest

from web.adapters.catalog_adapter import CatalogAdapter
from web.adapters.http_client import HttpClient
from web.schemas.catalog_schemas import ProductCategory, ProviderCreate


@pytest.fixture
def mock_http_client():
    """Create a mock HTTP client."""
    return Mock(spec=HttpClient)


@pytest.fixture
def catalog_adapter(mock_http_client):
    """Create a catalog adapter with mock HTTP client."""
    return CatalogAdapter(mock_http_client)


class TestCatalogAdapterCreateProvider:
    """Test create_provider calls correct endpoint."""

    @pytest.mark.asyncio
    async def test_calls_correct_endpoint(self, catalog_adapter, mock_http_client):
        """Test that POST /catalog/provider is called."""
        provider_data = ProviderCreate(
            name="Test Provider",
            nit="123456789",
            contact_name="John Doe",
            email="john@test.com",
            phone="+1234567890",
            address="123 Test St",
            country="United States",
        )

        mock_http_client.post = AsyncMock(
            return_value={"id": "test-id", "message": "Created"}
        )

        await catalog_adapter.create_provider(provider_data)

        mock_http_client.post.assert_called_once()
        call_args = mock_http_client.post.call_args
        assert call_args.args[0] == "/catalog/provider"


class TestCatalogAdapterGetProviders:
    """Test get_providers calls correct endpoint."""

    @pytest.mark.asyncio
    async def test_calls_correct_endpoint(self, catalog_adapter, mock_http_client):
        """Test that GET /catalog/providers is called."""
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

        await catalog_adapter.get_providers()

        mock_http_client.get.assert_called_once()
        call_args = mock_http_client.get.call_args
        assert call_args.args[0] == "/catalog/providers"


class TestCatalogAdapterCreateProducts:
    """Test create_products calls correct endpoint."""

    @pytest.mark.asyncio
    async def test_calls_correct_endpoint(self, catalog_adapter, mock_http_client):
        """Test that POST /catalog/products is called."""
        from web.schemas.catalog_schemas import ProductCreate

        products = [
            ProductCreate(
                provider_id=UUID("550e8400-e29b-41d4-a716-446655440000"),
                name="Product 1",
                category=ProductCategory.SPECIAL_MEDICATIONS,
                sku="PROD-001",
                price=Decimal("100.50"),
            )
        ]

        mock_http_client.post = AsyncMock(
            return_value={"created": [], "count": 0}
        )

        await catalog_adapter.create_products(products)

        mock_http_client.post.assert_called_once()
        call_args = mock_http_client.post.call_args
        assert call_args.args[0] == "/catalog/products"


class TestCatalogAdapterGetProducts:
    """Test get_products calls correct endpoint."""

    @pytest.mark.asyncio
    async def test_calls_correct_endpoint(self, catalog_adapter, mock_http_client):
        """Test that GET /catalog/products is called."""
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

        await catalog_adapter.get_products()

        mock_http_client.get.assert_called_once()
        call_args = mock_http_client.get.call_args
        assert call_args.args[0] == "/catalog/products"
