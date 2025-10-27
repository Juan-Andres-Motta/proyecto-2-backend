"""
Unit tests for ReportsAdapter.

Tests OUR logic:
- Calling correct HTTP endpoints
- Passing correct data to HTTP client
"""

from datetime import datetime
from unittest.mock import AsyncMock, Mock
from uuid import UUID, uuid4

import pytest

from common.http_client import HttpClient
from web.adapters.reports_adapter import InventoryReportsAdapter, OrderReportsAdapter
from web.schemas.report_schemas import ReportCreateRequest, ReportStatus, ReportType


@pytest.fixture
def mock_http_client():
    """Create a mock HTTP client."""
    return Mock(spec=HttpClient)


@pytest.fixture
def order_reports_adapter(mock_http_client):
    """Create an order reports adapter with mock HTTP client."""
    return OrderReportsAdapter(mock_http_client)


@pytest.fixture
def inventory_reports_adapter(mock_http_client):
    """Create an inventory reports adapter with mock HTTP client."""
    return InventoryReportsAdapter(mock_http_client)


class TestOrderReportsAdapterCreateReport:
    """Test create_report calls correct endpoint for Order service."""

    @pytest.mark.asyncio
    async def test_calls_correct_endpoint(
        self, order_reports_adapter, mock_http_client
    ):
        """Test that POST /reports is called with correct data."""
        user_id = uuid4()
        request_data = ReportCreateRequest(
            report_type=ReportType.ORDERS_PER_SELLER,
            start_date=datetime(2025, 1, 1),
            end_date=datetime(2025, 1, 31),
        )

        mock_http_client.post = AsyncMock(
            return_value={"report_id": str(uuid4()), "status": "pending"}
        )

        await order_reports_adapter.create_report(user_id, request_data)

        mock_http_client.post.assert_called_once()
        call_args = mock_http_client.post.call_args
        assert "/reports" in call_args.args[0]
        assert f"user_id={user_id}" in call_args.args[0]

    @pytest.mark.asyncio
    async def test_passes_correct_payload(
        self, order_reports_adapter, mock_http_client
    ):
        """Test that correct payload is sent."""
        user_id = uuid4()
        request_data = ReportCreateRequest(
            report_type=ReportType.ORDERS_PER_STATUS,
            start_date=datetime(2025, 1, 1),
            end_date=datetime(2025, 1, 31),
            filters={"status": "delivered"},
        )

        mock_http_client.post = AsyncMock(
            return_value={"report_id": str(uuid4()), "status": "pending"}
        )

        await order_reports_adapter.create_report(user_id, request_data)

        call_args = mock_http_client.post.call_args
        payload = call_args.kwargs["json"]

        assert payload["report_type"] == "orders_per_status"
        assert payload["start_date"] == "2025-01-01T00:00:00"
        assert payload["end_date"] == "2025-01-31T00:00:00"
        assert payload["filters"] == {"status": "delivered"}


class TestOrderReportsAdapterListReports:
    """Test list_reports calls correct endpoint for Order service."""

    @pytest.mark.asyncio
    async def test_calls_correct_endpoint(
        self, order_reports_adapter, mock_http_client
    ):
        """Test that GET /reports is called."""
        user_id = uuid4()

        mock_http_client.get = AsyncMock(
            return_value={
                "items": [],
                "total": 0,
                "page": 1,
                "size": 0,
                "has_next": False,
                "has_previous": False,
            }
        )

        await order_reports_adapter.list_reports(user_id)

        mock_http_client.get.assert_called_once()
        call_args = mock_http_client.get.call_args
        assert call_args.args[0] == "/reports"

    @pytest.mark.asyncio
    async def test_passes_query_parameters(
        self, order_reports_adapter, mock_http_client
    ):
        """Test that query parameters are passed correctly."""
        user_id = uuid4()

        mock_http_client.get = AsyncMock(
            return_value={
                "items": [],
                "total": 0,
                "page": 1,
                "size": 0,
                "has_next": False,
                "has_previous": False,
            }
        )

        await order_reports_adapter.list_reports(
            user_id=user_id,
            limit=20,
            offset=10,
            status=ReportStatus.COMPLETED,
            report_type=ReportType.ORDERS_PER_SELLER,
        )

        call_args = mock_http_client.get.call_args
        params = call_args.kwargs["params"]

        assert params["user_id"] == str(user_id)
        assert params["limit"] == 20
        assert params["offset"] == 10
        assert params["status"] == "completed"
        assert params["report_type"] == "orders_per_seller"


class TestOrderReportsAdapterGetReport:
    """Test get_report calls correct endpoint for Order service."""

    @pytest.mark.asyncio
    async def test_calls_correct_endpoint(
        self, order_reports_adapter, mock_http_client
    ):
        """Test that GET /reports/{report_id} is called."""
        user_id = uuid4()
        report_id = uuid4()

        mock_http_client.get = AsyncMock(
            return_value={
                "report_id": str(report_id),
                "status": "completed",
                "download_url": "https://s3.example.com/report.json",
            }
        )

        await order_reports_adapter.get_report(user_id, report_id)

        mock_http_client.get.assert_called_once()
        call_args = mock_http_client.get.call_args
        assert f"/reports/{report_id}" in call_args.args[0]

    @pytest.mark.asyncio
    async def test_passes_user_id_parameter(
        self, order_reports_adapter, mock_http_client
    ):
        """Test that user_id is passed as query parameter."""
        user_id = uuid4()
        report_id = uuid4()

        mock_http_client.get = AsyncMock(
            return_value={
                "report_id": str(report_id),
                "status": "completed",
            }
        )

        await order_reports_adapter.get_report(user_id, report_id)

        call_args = mock_http_client.get.call_args
        params = call_args.kwargs["params"]
        assert params["user_id"] == str(user_id)


class TestInventoryReportsAdapterCreateReport:
    """Test create_report calls correct endpoint for Inventory service."""

    @pytest.mark.asyncio
    async def test_calls_correct_endpoint(
        self, inventory_reports_adapter, mock_http_client
    ):
        """Test that POST /reports is called with correct data."""
        user_id = uuid4()
        request_data = ReportCreateRequest(
            report_type=ReportType.LOW_STOCK,
            start_date=datetime(2025, 1, 1),
            end_date=datetime(2025, 1, 31),
        )

        mock_http_client.post = AsyncMock(
            return_value={"report_id": str(uuid4()), "status": "pending"}
        )

        await inventory_reports_adapter.create_report(user_id, request_data)

        mock_http_client.post.assert_called_once()
        call_args = mock_http_client.post.call_args
        assert "/reports" in call_args.args[0]

    @pytest.mark.asyncio
    async def test_passes_correct_payload(
        self, inventory_reports_adapter, mock_http_client
    ):
        """Test that correct payload is sent for low_stock report."""
        user_id = uuid4()
        request_data = ReportCreateRequest(
            report_type=ReportType.LOW_STOCK,
            start_date=datetime(2025, 1, 1),
            end_date=datetime(2025, 1, 31),
            filters={"threshold": 10},
        )

        mock_http_client.post = AsyncMock(
            return_value={"report_id": str(uuid4()), "status": "pending"}
        )

        await inventory_reports_adapter.create_report(user_id, request_data)

        call_args = mock_http_client.post.call_args
        payload = call_args.kwargs["json"]

        assert payload["report_type"] == "low_stock"
        assert payload["filters"] == {"threshold": 10}


class TestInventoryReportsAdapterListReports:
    """Test list_reports calls correct endpoint for Inventory service."""

    @pytest.mark.asyncio
    async def test_calls_correct_endpoint(
        self, inventory_reports_adapter, mock_http_client
    ):
        """Test that GET /reports is called."""
        user_id = uuid4()

        mock_http_client.get = AsyncMock(
            return_value={
                "items": [],
                "total": 0,
                "page": 1,
                "size": 0,
                "has_next": False,
                "has_previous": False,
            }
        )

        await inventory_reports_adapter.list_reports(user_id)

        mock_http_client.get.assert_called_once()
        call_args = mock_http_client.get.call_args
        assert call_args.args[0] == "/reports"


class TestInventoryReportsAdapterGetReport:
    """Test get_report calls correct endpoint for Inventory service."""

    @pytest.mark.asyncio
    async def test_calls_correct_endpoint(
        self, inventory_reports_adapter, mock_http_client
    ):
        """Test that GET /reports/{report_id} is called."""
        user_id = uuid4()
        report_id = uuid4()

        mock_http_client.get = AsyncMock(
            return_value={
                "report_id": str(report_id),
                "status": "completed",
            }
        )

        await inventory_reports_adapter.get_report(user_id, report_id)

        mock_http_client.get.assert_called_once()
        call_args = mock_http_client.get.call_args
        assert f"/reports/{report_id}" in call_args.args[0]
