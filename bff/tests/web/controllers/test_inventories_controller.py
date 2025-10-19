"""
Unit tests for inventories controller.

Tests the orchestration between catalog and inventory services.
"""

from datetime import date, datetime
from unittest.mock import AsyncMock, Mock
from uuid import UUID

import pytest
from fastapi import status

from web.controllers.inventories_controller import create_inventory, get_inventories
from web.ports.catalog_port import CatalogPort
from web.ports.inventory_port import InventoryPort
from web.schemas.catalog_schemas import ProductCategory, ProductResponse
from web.schemas.inventory_schemas import InventoryCreateRequest, InventoryCreateResponse


@pytest.fixture
def mock_catalog_port():
    """Create a mock catalog port."""
    return Mock(spec=CatalogPort)


@pytest.fixture
def mock_inventory_port():
    """Create a mock inventory port."""
    return Mock(spec=InventoryPort)


@pytest.fixture
def sample_product():
    """Sample product response from catalog."""
    return ProductResponse(
        id=UUID("550e8400-e29b-41d4-a716-446655440000"),
        provider_id=UUID("660e8400-e29b-41d4-a716-446655440000"),
        provider_name="Test Provider",
        name="Test Product",
        category=ProductCategory.SPECIAL_MEDICATIONS,
        sku="PROD-001",
        price=99.99,
        created_at=datetime(2024, 1, 1, 12, 0, 0),
        updated_at=datetime(2024, 1, 1, 12, 0, 0),
    )


class TestInventoriesControllerCreate:
    """Test create_inventory controller."""

    @pytest.mark.asyncio
    async def test_creates_inventory_with_denormalized_data(
        self, mock_catalog_port, mock_inventory_port, sample_product
    ):
        """Test successful inventory creation with product denormalization."""
        product_id = UUID("550e8400-e29b-41d4-a716-446655440000")
        warehouse_id = UUID("770e8400-e29b-41d4-a716-446655440000")

        # Create request data from client (JSON body) - NO denormalized fields
        request_data = InventoryCreateRequest(
            product_id=product_id,
            warehouse_id=warehouse_id,
            total_quantity=100,
            batch_number="BATCH-001",
            expiration_date=date(2025, 12, 31),
        )

        # Mock catalog returning product
        mock_catalog_port.get_product_by_id = AsyncMock(return_value=sample_product)

        # Mock inventory creation
        expected_response = InventoryCreateResponse(
            id="880e8400-e29b-41d4-a716-446655440000",
            message="Inventory created successfully"
        )
        mock_inventory_port.create_inventory = AsyncMock(return_value=expected_response)

        # Call controller
        result = await create_inventory(
            request_data=request_data,
            catalog=mock_catalog_port,
            inventory=mock_inventory_port,
        )

        # Verify catalog was called
        mock_catalog_port.get_product_by_id.assert_called_once_with(product_id)

        # Verify inventory was called with denormalized data
        mock_inventory_port.create_inventory.assert_called_once()
        call_args = mock_inventory_port.create_inventory.call_args[0][0]

        assert call_args.product_id == product_id
        assert call_args.warehouse_id == warehouse_id
        assert call_args.total_quantity == 100
        assert call_args.batch_number == "BATCH-001"
        # Denormalized fields from catalog
        assert call_args.product_sku == sample_product.sku
        assert call_args.product_name == sample_product.name
        assert call_args.product_price == float(sample_product.price)

        assert result == expected_response

    @pytest.mark.asyncio
    async def test_returns_404_when_product_not_found(
        self, mock_catalog_port, mock_inventory_port
    ):
        """Test that 404 is returned when product doesn't exist."""
        product_id = UUID("550e8400-e29b-41d4-a716-446655440000")
        warehouse_id = UUID("770e8400-e29b-41d4-a716-446655440000")

        # Create request data from client (JSON body) - NO denormalized fields
        request_data = InventoryCreateRequest(
            product_id=product_id,
            warehouse_id=warehouse_id,
            total_quantity=100,
            batch_number="BATCH-001",
            expiration_date=date(2025, 12, 31),
        )

        # Mock catalog returning None (product not found)
        mock_catalog_port.get_product_by_id = AsyncMock(return_value=None)

        # Call controller
        result = await create_inventory(
            request_data=request_data,
            catalog=mock_catalog_port,
            inventory=mock_inventory_port,
        )

        # Verify catalog was called
        mock_catalog_port.get_product_by_id.assert_called_once_with(product_id)

        # Verify inventory was NOT called
        mock_inventory_port.create_inventory.assert_not_called()

        # Verify response is JSONResponse with 404
        assert result.status_code == status.HTTP_404_NOT_FOUND

        # Verify error format
        import json
        error_body = json.loads(result.body.decode())
        assert error_body["error_code"] == "PRODUCT_NOT_FOUND"
        assert error_body["type"] == "not_found"
        assert "details" in error_body
        assert error_body["details"]["resource"] == "Product"
        assert error_body["details"]["id"] == str(product_id)


class TestInventoriesControllerList:
    """Test get_inventories controller."""

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
            sku=None,
            warehouse_id=None,
            inventory=mock_inventory_port
        )

        mock_inventory_port.get_inventories.assert_called_once_with(
            limit=10,
            offset=0,
            sku=None,
            warehouse_id=None,
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
            sku="PROD-001",
            warehouse_id=None,
            inventory=mock_inventory_port
        )

        mock_inventory_port.get_inventories.assert_called_once_with(
            limit=10,
            offset=0,
            sku="PROD-001",
            warehouse_id=None,
        )
        assert result == expected_response

    @pytest.mark.asyncio
    async def test_lists_inventories_with_warehouse_filter(self, mock_inventory_port):
        """Test listing inventories with warehouse_id filter."""
        warehouse_id = UUID("770e8400-e29b-41d4-a716-446655440000")
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
            sku=None,
            warehouse_id=warehouse_id,
            inventory=mock_inventory_port
        )

        mock_inventory_port.get_inventories.assert_called_once_with(
            limit=10,
            offset=0,
            sku=None,
            warehouse_id=warehouse_id,
        )
        assert result == expected_response

    @pytest.mark.asyncio
    async def test_lists_inventories_with_both_filters(self, mock_inventory_port):
        """Test listing inventories with both SKU and warehouse_id filters."""
        warehouse_id = UUID("770e8400-e29b-41d4-a716-446655440000")
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
            sku="PROD-001",
            warehouse_id=warehouse_id,
            inventory=mock_inventory_port
        )

        mock_inventory_port.get_inventories.assert_called_once_with(
            limit=10,
            offset=0,
            sku="PROD-001",
            warehouse_id=warehouse_id,
        )
        assert result == expected_response

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
            sku=None,
            warehouse_id=None,
            inventory=mock_inventory_port
        )

        mock_inventory_port.get_inventories.assert_called_once_with(
            limit=20,
            offset=40,
            sku=None,
            warehouse_id=None,
        )
        assert result == expected_response
