"""
Unit tests for the common inventory adapter.

Tests the InventoryAdapter implementation for common/shared functionality.
"""

from datetime import datetime
from unittest.mock import AsyncMock, Mock
from uuid import UUID

import pytest

from common.adapters.inventory_adapter import InventoryAdapter
from common.http_client import HttpClient
from common.schemas import PaginatedInventoriesResponse, InventoryResponse


@pytest.fixture
def mock_http_client():
    """Create a mock HTTP client."""
    return Mock(spec=HttpClient)


@pytest.fixture
def inventory_adapter(mock_http_client):
    """Create an InventoryAdapter instance with mock HTTP client."""
    return InventoryAdapter(mock_http_client)


@pytest.fixture
def sample_inventory_response():
    """Sample inventory item response."""
    return {
        "id": "123e4567-e89b-12d3-a456-426614174000",
        "product_id": "223e4567-e89b-12d3-a456-426614174001",
        "warehouse_id": "323e4567-e89b-12d3-a456-426614174002",
        "total_quantity": 100,
        "reserved_quantity": 20,
        "batch_number": "BATCH-2024-001",
        "expiration_date": "2025-12-31T00:00:00Z",
        "product_sku": "MED-12345",
        "product_name": "Aspirin 500mg",
        "product_price": 5.99,
        "product_category": "Analgesics",
        "warehouse_name": "Main Warehouse",
        "warehouse_city": "Bogota",
        "warehouse_country": "Colombia",
        "created_at": "2024-01-15T10:30:00Z",
        "updated_at": "2024-01-20T14:45:00Z",
    }


@pytest.fixture
def sample_paginated_response(sample_inventory_response):
    """Sample paginated inventories response."""
    return {
        "items": [sample_inventory_response],
        "total": 50,
        "page": 1,
        "size": 10,
        "has_next": True,
        "has_previous": False,
    }


class TestInventoryAdapterGetInventories:
    """Tests for the get_inventories method."""

    @pytest.mark.asyncio
    async def test_get_inventories_basic(self, inventory_adapter, mock_http_client, sample_paginated_response):
        """Test basic get_inventories call with default parameters."""
        mock_http_client.get = AsyncMock(return_value=sample_paginated_response)

        result = await inventory_adapter.get_inventories()

        # Verify the HTTP client was called correctly
        mock_http_client.get.assert_called_once_with(
            "/inventory/inventories",
            params={"limit": 10, "offset": 0},
        )

        # Verify result is a PaginatedInventoriesResponse
        assert isinstance(result, PaginatedInventoriesResponse)
        assert len(result.items) == 1
        assert result.total == 50
        assert result.page == 1
        assert result.size == 10
        assert result.has_next is True
        assert result.has_previous is False

    @pytest.mark.asyncio
    async def test_get_inventories_with_custom_limit_and_offset(
        self, inventory_adapter, mock_http_client, sample_paginated_response
    ):
        """Test get_inventories with custom limit and offset."""
        mock_http_client.get = AsyncMock(return_value=sample_paginated_response)

        result = await inventory_adapter.get_inventories(limit=25, offset=50)

        mock_http_client.get.assert_called_once_with(
            "/inventory/inventories",
            params={"limit": 25, "offset": 50},
        )

        assert result.total == 50

    @pytest.mark.asyncio
    async def test_get_inventories_with_name_filter(
        self, inventory_adapter, mock_http_client, sample_paginated_response
    ):
        """Test get_inventories with name filter."""
        mock_http_client.get = AsyncMock(return_value=sample_paginated_response)

        result = await inventory_adapter.get_inventories(name="Aspirin")

        mock_http_client.get.assert_called_once_with(
            "/inventory/inventories",
            params={"limit": 10, "offset": 0, "name": "Aspirin"},
        )

        assert len(result.items) == 1

    @pytest.mark.asyncio
    async def test_get_inventories_with_sku_filter(
        self, inventory_adapter, mock_http_client, sample_paginated_response
    ):
        """Test get_inventories with SKU filter."""
        mock_http_client.get = AsyncMock(return_value=sample_paginated_response)

        result = await inventory_adapter.get_inventories(sku="MED-12345")

        mock_http_client.get.assert_called_once_with(
            "/inventory/inventories",
            params={"limit": 10, "offset": 0, "sku": "MED-12345"},
        )

        assert isinstance(result, PaginatedInventoriesResponse)

    @pytest.mark.asyncio
    async def test_get_inventories_with_category_filter(
        self, inventory_adapter, mock_http_client, sample_paginated_response
    ):
        """Test get_inventories with category filter."""
        mock_http_client.get = AsyncMock(return_value=sample_paginated_response)

        result = await inventory_adapter.get_inventories(category="Analgesics")

        mock_http_client.get.assert_called_once_with(
            "/inventory/inventories",
            params={"limit": 10, "offset": 0, "category": "Analgesics"},
        )

        assert result.size == 10

    @pytest.mark.asyncio
    async def test_get_inventories_with_multiple_filters(
        self, inventory_adapter, mock_http_client, sample_paginated_response
    ):
        """Test get_inventories with multiple filters combined."""
        mock_http_client.get = AsyncMock(return_value=sample_paginated_response)

        result = await inventory_adapter.get_inventories(
            limit=20,
            offset=10,
            name="Aspirin",
            sku="MED-12345",
            category="Analgesics"
        )

        mock_http_client.get.assert_called_once_with(
            "/inventory/inventories",
            params={
                "limit": 20,
                "offset": 10,
                "name": "Aspirin",
                "sku": "MED-12345",
                "category": "Analgesics",
            },
        )

        assert len(result.items) == 1

    @pytest.mark.asyncio
    async def test_get_inventories_with_none_filters(
        self, inventory_adapter, mock_http_client, sample_paginated_response
    ):
        """Test that None filter values are not included in params."""
        mock_http_client.get = AsyncMock(return_value=sample_paginated_response)

        result = await inventory_adapter.get_inventories(
            name=None,
            sku=None,
            category=None
        )

        # Should only include limit and offset
        mock_http_client.get.assert_called_once_with(
            "/inventory/inventories",
            params={"limit": 10, "offset": 0},
        )

        assert isinstance(result, PaginatedInventoriesResponse)

    @pytest.mark.asyncio
    async def test_get_inventories_empty_response(
        self, inventory_adapter, mock_http_client
    ):
        """Test get_inventories with empty inventory list."""
        empty_response = {
            "items": [],
            "total": 0,
            "page": 1,
            "size": 10,
            "has_next": False,
            "has_previous": False,
        }
        mock_http_client.get = AsyncMock(return_value=empty_response)

        result = await inventory_adapter.get_inventories()

        assert len(result.items) == 0
        assert result.total == 0
        assert result.has_next is False
        assert result.has_previous is False

    @pytest.mark.asyncio
    async def test_get_inventories_validation(
        self, inventory_adapter, mock_http_client
    ):
        """Test that response is properly validated by Pydantic."""
        invalid_response = {
            "items": [
                {
                    "id": "invalid-uuid",  # Invalid UUID format
                    "product_id": "invalid",
                    "warehouse_id": "invalid",
                    "total_quantity": "not-a-number",  # Invalid type
                    # Missing required fields
                }
            ],
            "total": "not-a-number",
            "page": 1,
            "size": 10,
            "has_next": True,
            "has_previous": False,
        }
        mock_http_client.get = AsyncMock(return_value=invalid_response)

        with pytest.raises(Exception):
            await inventory_adapter.get_inventories()

    @pytest.mark.asyncio
    async def test_get_inventories_response_fields(
        self, inventory_adapter, mock_http_client, sample_paginated_response
    ):
        """Test that all response fields are correctly accessible."""
        mock_http_client.get = AsyncMock(return_value=sample_paginated_response)

        result = await inventory_adapter.get_inventories()
        item = result.items[0]

        # Verify all fields are correctly parsed
        assert str(item.id) == "123e4567-e89b-12d3-a456-426614174000"
        assert item.product_sku == "MED-12345"
        assert item.product_name == "Aspirin 500mg"
        assert item.product_price == 5.99
        assert item.product_category == "Analgesics"
        assert item.warehouse_name == "Main Warehouse"
        assert item.warehouse_city == "Bogota"
        assert item.warehouse_country == "Colombia"
        assert item.total_quantity == 100
        assert item.reserved_quantity == 20

    @pytest.mark.asyncio
    async def test_get_inventories_computed_field(
        self, inventory_adapter, mock_http_client, sample_paginated_response
    ):
        """Test that computed field available_quantity is calculated correctly."""
        mock_http_client.get = AsyncMock(return_value=sample_paginated_response)

        result = await inventory_adapter.get_inventories()
        item = result.items[0]

        # Verify computed field
        expected_available = item.total_quantity - item.reserved_quantity
        assert item.available_quantity == expected_available
        assert item.available_quantity == 80
