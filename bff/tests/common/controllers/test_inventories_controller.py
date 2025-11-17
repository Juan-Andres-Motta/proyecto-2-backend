"""
Unit tests for common inventories controller.

Tests the shared inventories endpoint accessible to all users.
"""

from unittest.mock import AsyncMock, Mock

import pytest
from fastapi import HTTPException, status

from common.controllers.inventories_controller import get_inventories
from common.ports.inventory_port import InventoryPort


@pytest.fixture
def mock_inventory_port():
    """Create a mock inventory port."""
    return Mock(spec=InventoryPort)


class TestCommonInventoriesController:
    """Test get_inventories controller for common/shared endpoint."""

    @pytest.mark.asyncio
    async def test_lists_inventories_without_filters(self, mock_inventory_port):
        """Test listing inventories without filters."""
        expected_response = {
            "items": [],
            "total": 0,
            "page": 1,
            "size": 10,
            "has_next": False,
            "has_previous": False,
        }
        mock_inventory_port.get_inventories = AsyncMock(return_value=expected_response)

        result = await get_inventories(
            limit=10,
            offset=0,
            name=None,
            sku=None,
            category=None,
            inventory=mock_inventory_port,
        )

        mock_inventory_port.get_inventories.assert_called_once_with(
            limit=10,
            offset=0,
            name=None,
            sku=None,
            category=None,
        )
        assert result == expected_response

    @pytest.mark.asyncio
    async def test_lists_inventories_with_name_filter(self, mock_inventory_port):
        """Test listing inventories with name filter."""
        expected_response = {
            "items": [],
            "total": 0,
            "page": 1,
            "size": 10,
            "has_next": False,
            "has_previous": False,
        }
        mock_inventory_port.get_inventories = AsyncMock(return_value=expected_response)

        result = await get_inventories(
            limit=10,
            offset=0,
            name="Test Product",
            sku=None,
            category=None,
            inventory=mock_inventory_port,
        )

        mock_inventory_port.get_inventories.assert_called_once_with(
            limit=10,
            offset=0,
            name="Test Product",
            sku=None,
            category=None,
        )
        assert result == expected_response

    @pytest.mark.asyncio
    async def test_lists_inventories_with_sku_filter(self, mock_inventory_port):
        """Test listing inventories with SKU filter."""
        expected_response = {
            "items": [],
            "total": 0,
            "page": 1,
            "size": 10,
            "has_next": False,
            "has_previous": False,
        }
        mock_inventory_port.get_inventories = AsyncMock(return_value=expected_response)

        result = await get_inventories(
            limit=10,
            offset=0,
            name=None,
            sku="PROD-001",
            category=None,
            inventory=mock_inventory_port,
        )

        mock_inventory_port.get_inventories.assert_called_once_with(
            limit=10,
            offset=0,
            name=None,
            sku="PROD-001",
            category=None,
        )
        assert result == expected_response

    @pytest.mark.asyncio
    async def test_lists_inventories_with_category_filter(self, mock_inventory_port):
        """Test listing inventories with category filter."""
        expected_response = {
            "items": [],
            "total": 0,
            "page": 1,
            "size": 10,
            "has_next": False,
            "has_previous": False,
        }
        mock_inventory_port.get_inventories = AsyncMock(return_value=expected_response)

        result = await get_inventories(
            limit=10,
            offset=0,
            name=None,
            sku=None,
            category="electronics",
            inventory=mock_inventory_port,
        )

        mock_inventory_port.get_inventories.assert_called_once_with(
            limit=10,
            offset=0,
            name=None,
            sku=None,
            category="electronics",
        )
        assert result == expected_response

    @pytest.mark.asyncio
    async def test_rejects_multiple_filters(self, mock_inventory_port):
        """Test that multiple filters are rejected (name + sku)."""
        with pytest.raises(HTTPException) as exc_info:
            await get_inventories(
                limit=10,
                offset=0,
                name="Test Product",
                sku="PROD-001",
                category=None,
                inventory=mock_inventory_port,
            )

        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert exc_info.value.detail == "Only one filter allowed at a time"
        mock_inventory_port.get_inventories.assert_not_called()

    @pytest.mark.asyncio
    async def test_rejects_multiple_filters_all_three(self, mock_inventory_port):
        """Test that multiple filters are rejected (all three filters)."""
        with pytest.raises(HTTPException) as exc_info:
            await get_inventories(
                limit=10,
                offset=0,
                name="Test Product",
                sku="PROD-001",
                category="electronics",
                inventory=mock_inventory_port,
            )

        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert exc_info.value.detail == "Only one filter allowed at a time"
        mock_inventory_port.get_inventories.assert_not_called()

    @pytest.mark.asyncio
    async def test_rejects_multiple_filters_sku_category(self, mock_inventory_port):
        """Test that multiple filters are rejected (sku + category)."""
        with pytest.raises(HTTPException) as exc_info:
            await get_inventories(
                limit=10,
                offset=0,
                name=None,
                sku="PROD-001",
                category="electronics",
                inventory=mock_inventory_port,
            )

        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert exc_info.value.detail == "Only one filter allowed at a time"
        mock_inventory_port.get_inventories.assert_not_called()

    @pytest.mark.asyncio
    async def test_lists_inventories_with_custom_pagination(self, mock_inventory_port):
        """Test listing inventories with custom limit and offset."""
        expected_response = {
            "items": [],
            "total": 0,
            "page": 3,
            "size": 20,
            "has_next": False,
            "has_previous": True,
        }
        mock_inventory_port.get_inventories = AsyncMock(return_value=expected_response)

        result = await get_inventories(
            limit=20,
            offset=40,
            name=None,
            sku=None,
            category=None,
            inventory=mock_inventory_port,
        )

        mock_inventory_port.get_inventories.assert_called_once_with(
            limit=20,
            offset=40,
            name=None,
            sku=None,
            category=None,
        )
        assert result == expected_response
