"""
Unit tests for InventoryAdapter.

Tests OUR logic:
- Calling correct HTTP endpoints
"""

from unittest.mock import AsyncMock, Mock

import pytest

from web.adapters.inventory_adapter import InventoryAdapter
from web.adapters.http_client import HttpClient
from web.schemas.inventory_schemas import WarehouseCreate


@pytest.fixture
def mock_http_client():
    """Create a mock HTTP client."""
    return Mock(spec=HttpClient)


@pytest.fixture
def inventory_adapter(mock_http_client):
    """Create an inventory adapter with mock HTTP client."""
    return InventoryAdapter(mock_http_client)


class TestInventoryAdapterCreateWarehouse:
    """Test create_warehouse calls correct endpoint."""

    @pytest.mark.asyncio
    async def test_calls_correct_endpoint(self, inventory_adapter, mock_http_client):
        """Test that POST /warehouse is called."""
        warehouse_data = WarehouseCreate(
            name="Test Warehouse",
            location="Test Location",
            capacity=1000,
            country="Test Country",
            city="Test City",
            address="Test Address",
        )

        mock_http_client.post = AsyncMock(
            return_value={"id": "test-id", "message": "Created"}
        )

        await inventory_adapter.create_warehouse(warehouse_data)

        mock_http_client.post.assert_called_once()
        call_args = mock_http_client.post.call_args
        assert call_args.args[0] == "/inventory/warehouse"


class TestInventoryAdapterGetWarehouses:
    """Test get_warehouses calls correct endpoint."""

    @pytest.mark.asyncio
    async def test_calls_correct_endpoint(self, inventory_adapter, mock_http_client):
        """Test that GET /warehouses is called."""
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

        await inventory_adapter.get_warehouses()

        mock_http_client.get.assert_called_once()
        call_args = mock_http_client.get.call_args
        assert call_args.args[0] == "/inventory/warehouses"


class TestInventoryAdapterCreateInventory:
    """Test create_inventory calls correct endpoint."""

    @pytest.mark.asyncio
    async def test_calls_correct_endpoint(self, inventory_adapter, mock_http_client):
        """Test that POST /inventory is called."""
        from web.schemas.inventory_schemas import InventoryCreate
        from datetime import date
        from uuid import uuid4

        inventory_data = InventoryCreate(
            product_id=uuid4(),
            warehouse_id=uuid4(),
            total_quantity=100,
            batch_number="BATCH-001",
            expiration_date=date(2025, 12, 31),
            product_sku="TEST-SKU",
            product_name="Test Product",
            product_price=100.50,
        )

        mock_http_client.post = AsyncMock(
            return_value={"id": "test-id", "message": "Created"}
        )

        await inventory_adapter.create_inventory(inventory_data)

        mock_http_client.post.assert_called_once()
        call_args = mock_http_client.post.call_args
        assert call_args.args[0] == "/inventory/inventory"


class TestInventoryAdapterGetInventories:
    """Test get_inventories calls correct endpoint."""

    @pytest.mark.asyncio
    async def test_calls_correct_endpoint(self, inventory_adapter, mock_http_client):
        """Test that GET /inventories is called."""
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

        await inventory_adapter.get_inventories()

        mock_http_client.get.assert_called_once()
        call_args = mock_http_client.get.call_args
        assert call_args.args[0] == "/inventory/inventories"

    @pytest.mark.asyncio
    async def test_includes_sku_filter_when_provided(self, inventory_adapter, mock_http_client):
        """Test that SKU filter is included in query params."""
        from uuid import uuid4

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

        await inventory_adapter.get_inventories(sku="PRODUCT-001")

        mock_http_client.get.assert_called_once()
        call_args = mock_http_client.get.call_args
        params = call_args.kwargs["params"]
        assert params["sku"] == "PRODUCT-001"
        assert "warehouse_id" not in params

    @pytest.mark.asyncio
    async def test_includes_warehouse_id_filter_when_provided(self, inventory_adapter, mock_http_client):
        """Test that warehouse_id filter is included in query params."""
        from uuid import uuid4

        warehouse_id = uuid4()
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

        await inventory_adapter.get_inventories(warehouse_id=warehouse_id)

        mock_http_client.get.assert_called_once()
        call_args = mock_http_client.get.call_args
        params = call_args.kwargs["params"]
        assert params["warehouse_id"] == str(warehouse_id)
        assert "sku" not in params

    @pytest.mark.asyncio
    async def test_includes_both_filters_when_provided(self, inventory_adapter, mock_http_client):
        """Test that both filters are included together."""
        from uuid import uuid4

        warehouse_id = uuid4()
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

        await inventory_adapter.get_inventories(sku="SKU-123", warehouse_id=warehouse_id)

        mock_http_client.get.assert_called_once()
        call_args = mock_http_client.get.call_args
        params = call_args.kwargs["params"]
        assert params["sku"] == "SKU-123"
        assert params["warehouse_id"] == str(warehouse_id)
        assert params["limit"] == 10
        assert params["offset"] == 0


class TestInventoryAdapterCreateReport:
    """Test create_report calls correct endpoint."""

    @pytest.mark.asyncio
    async def test_creates_report_with_user_id(self, inventory_adapter, mock_http_client):
        """Test that POST /reports is called with user_id in payload."""
        from uuid import uuid4
        from web.schemas.inventory_schemas import ReportCreateRequest

        user_id = uuid4()
        report_data = ReportCreateRequest(
            report_type="low_stock",
            start_date="2025-01-01T00:00:00Z",
            end_date="2025-01-31T00:00:00Z",
        )

        mock_http_client.post = AsyncMock(
            return_value={"report_id": str(uuid4()), "status": "pending", "message": "Report created successfully"}
        )

        await inventory_adapter.create_report(user_id, report_data)

        mock_http_client.post.assert_called_once()
        call_args = mock_http_client.post.call_args
        assert call_args.args[0] == "/inventory/reports"
        payload = call_args.kwargs["json"]
        assert payload["user_id"] == str(user_id)
        assert payload["report_type"] == "low_stock"


class TestInventoryAdapterGetReports:
    """Test get_reports calls correct endpoint."""

    @pytest.mark.asyncio
    async def test_get_reports_basic(self, inventory_adapter, mock_http_client):
        """Test that GET /reports is called with user_id."""
        from uuid import uuid4

        user_id = uuid4()
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

        await inventory_adapter.get_reports(user_id)

        mock_http_client.get.assert_called_once()
        call_args = mock_http_client.get.call_args
        assert call_args.args[0] == "/inventory/reports"
        params = call_args.kwargs["params"]
        assert params["user_id"] == str(user_id)
        assert params["limit"] == 10
        assert params["offset"] == 0

    @pytest.mark.asyncio
    async def test_get_reports_with_status_filter(self, inventory_adapter, mock_http_client):
        """Test get_reports includes status filter when provided."""
        from uuid import uuid4

        user_id = uuid4()
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

        await inventory_adapter.get_reports(user_id, status="completed")

        call_args = mock_http_client.get.call_args
        params = call_args.kwargs["params"]
        assert params["status"] == "completed"

    @pytest.mark.asyncio
    async def test_get_reports_with_report_type_filter(self, inventory_adapter, mock_http_client):
        """Test get_reports includes report_type filter when provided."""
        from uuid import uuid4

        user_id = uuid4()
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

        await inventory_adapter.get_reports(user_id, report_type="low_stock")

        call_args = mock_http_client.get.call_args
        params = call_args.kwargs["params"]
        assert params["report_type"] == "low_stock"

    @pytest.mark.asyncio
    async def test_get_reports_with_all_filters(self, inventory_adapter, mock_http_client):
        """Test get_reports includes all filters when provided."""
        from uuid import uuid4

        user_id = uuid4()
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

        await inventory_adapter.get_reports(
            user_id,
            limit=20,
            offset=10,
            status="completed",
            report_type="low_stock"
        )

        call_args = mock_http_client.get.call_args
        params = call_args.kwargs["params"]
        assert params["user_id"] == str(user_id)
        assert params["limit"] == 20
        assert params["offset"] == 10
        assert params["status"] == "completed"
        assert params["report_type"] == "low_stock"


class TestInventoryAdapterGetReport:
    """Test get_report calls correct endpoint."""

    @pytest.mark.asyncio
    async def test_gets_single_report(self, inventory_adapter, mock_http_client):
        """Test that GET /reports/{report_id} is called with correct params."""
        from uuid import uuid4

        user_id = uuid4()
        report_id = uuid4()
        mock_http_client.get = AsyncMock(
            return_value={
                "id": str(report_id),
                "status": "completed",
                "report_type": "low_stock",
                "created_at": "2025-10-18T00:00:00Z",
                "start_date": "2025-10-01T00:00:00Z",
                "end_date": "2025-10-31T00:00:00Z",
                "filters": {},
            }
        )

        result = await inventory_adapter.get_report(user_id, report_id)

        mock_http_client.get.assert_called_once()
        call_args = mock_http_client.get.call_args
        assert call_args.args[0] == f"/inventory/reports/{report_id}"
        assert call_args.kwargs["params"]["user_id"] == str(user_id)
