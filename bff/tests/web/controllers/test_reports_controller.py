"""Unit tests for reports controller."""

from datetime import datetime
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest
from fastapi import HTTPException

from common.exceptions import MicroserviceError, MicroserviceHTTPError, ResourceNotFoundError
from web.controllers.reports_controller import create_report, get_report, list_reports
from web.ports.reports_port import ReportsPort
from web.schemas.report_schemas import (
    PaginatedReportsResponse,
    ReportCreateRequest,
    ReportCreateResponse,
    ReportResponse,
    ReportStatus,
    ReportType,
)


@pytest.fixture
def mock_order_adapter():
    return Mock(spec=ReportsPort)


@pytest.fixture
def mock_inventory_adapter():
    return Mock(spec=ReportsPort)


@pytest.fixture
def mock_user():
    """Mock authenticated user."""
    return {"sub": str(uuid4()), "email": "test@example.com"}


class TestCreateReport:
    """Test create_report controller function."""

    @pytest.mark.asyncio
    async def test_create_orders_per_seller_report(
        self, mock_user, mock_order_adapter, mock_inventory_adapter
    ):
        """Test creating orders_per_seller report routes to Order service."""
        request_data = ReportCreateRequest(
            report_type=ReportType.ORDERS_PER_SELLER,
            start_date=datetime(2025, 1, 1),
            end_date=datetime(2025, 1, 31),
        )

        report_id = uuid4()
        mock_order_adapter.create_report = AsyncMock(
            return_value=ReportCreateResponse(report_id=report_id, status="pending")
        )

        result = await create_report(
            request_data, mock_order_adapter, mock_inventory_adapter, mock_user
        )

        assert result.report_id == report_id
        assert result.status == "pending"
        mock_order_adapter.create_report.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_orders_per_status_report(
        self, mock_user, mock_order_adapter, mock_inventory_adapter
    ):
        """Test creating orders_per_status report routes to Order service."""
        request_data = ReportCreateRequest(
            report_type=ReportType.ORDERS_PER_STATUS,
            start_date=datetime(2025, 1, 1),
            end_date=datetime(2025, 1, 31),
        )

        report_id = uuid4()
        mock_order_adapter.create_report = AsyncMock(
            return_value=ReportCreateResponse(report_id=report_id, status="pending")
        )

        result = await create_report(
            request_data, mock_order_adapter, mock_inventory_adapter, mock_user
        )

        assert result.report_id == report_id
        mock_order_adapter.create_report.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_low_stock_report(
        self, mock_user, mock_order_adapter, mock_inventory_adapter
    ):
        """Test creating low_stock report routes to Inventory service."""
        request_data = ReportCreateRequest(
            report_type=ReportType.LOW_STOCK,
            start_date=datetime(2025, 1, 1),
            end_date=datetime(2025, 1, 31),
        )

        report_id = uuid4()
        mock_inventory_adapter.create_report = AsyncMock(
            return_value=ReportCreateResponse(report_id=report_id, status="pending")
        )

        result = await create_report(
            request_data, mock_order_adapter, mock_inventory_adapter, mock_user
        )

        assert result.report_id == report_id
        mock_inventory_adapter.create_report.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_report_handles_microservice_error(
        self, mock_user, mock_inventory_adapter
    ):
        """Test that microservice errors are handled correctly."""
        request_data = ReportCreateRequest(
            report_type=ReportType.ORDERS_PER_SELLER,
            start_date=datetime(2025, 1, 1),
            end_date=datetime(2025, 1, 31),
        )

        mock_order_adapter = Mock(spec=ReportsPort)
        mock_order_adapter.create_report = AsyncMock(
            side_effect=MicroserviceError("order", "Service unavailable", 503)
        )

        with pytest.raises(HTTPException) as exc_info:
            await create_report(
                request_data, mock_order_adapter, mock_inventory_adapter, mock_user
            )

        assert exc_info.value.status_code == 503

    @pytest.mark.asyncio
    async def test_create_report_handles_unexpected_error(
        self, mock_user, mock_inventory_adapter
    ):
        """Test that unexpected errors return 500."""
        request_data = ReportCreateRequest(
            report_type=ReportType.ORDERS_PER_SELLER,
            start_date=datetime(2025, 1, 1),
            end_date=datetime(2025, 1, 31),
        )

        mock_order_adapter = Mock(spec=ReportsPort)
        mock_order_adapter.create_report = AsyncMock(side_effect=Exception("Unexpected"))

        with pytest.raises(HTTPException) as exc_info:
            await create_report(
                request_data, mock_order_adapter, mock_inventory_adapter, mock_user
            )

        assert exc_info.value.status_code == 500


class TestListReports:
    """Test list_reports controller function."""

    @pytest.mark.asyncio
    async def test_list_reports_filters_by_order_type(
        self, mock_user, mock_order_adapter, mock_inventory_adapter
    ):
        """Test listing reports with order type filter."""
        mock_order_adapter.list_reports = AsyncMock(
            return_value=PaginatedReportsResponse(
                items=[],
                total=0,
                page=1,
                size=0,
                has_next=False,
                has_previous=False,
            )
        )

        result = await list_reports(
            limit=10,
            offset=0,
            status=None,
            report_type="orders_per_seller",
            order_reports=mock_order_adapter,
            inventory_reports=mock_inventory_adapter,
            user=mock_user,
        )

        assert result.total == 0
        mock_order_adapter.list_reports.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_reports_filters_by_inventory_type(
        self, mock_user, mock_order_adapter, mock_inventory_adapter
    ):
        """Test listing reports with inventory type filter."""
        mock_inventory_adapter.list_reports = AsyncMock(
            return_value=PaginatedReportsResponse(
                items=[],
                total=0,
                page=1,
                size=0,
                has_next=False,
                has_previous=False,
            )
        )

        result = await list_reports(
            limit=10,
            offset=0,
            status=None,
            report_type="low_stock",
            order_reports=mock_order_adapter,
            inventory_reports=mock_inventory_adapter,
            user=mock_user,
        )

        assert result.total == 0
        mock_inventory_adapter.list_reports.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_reports_aggregates_from_both_services(
        self, mock_user, mock_order_adapter, mock_inventory_adapter
    ):
        """Test listing reports aggregates from both Order and Inventory."""
        order_report = ReportResponse(
            id=uuid4(),
            report_type="orders_per_seller",
            status="completed",
            created_at=datetime(2025, 1, 15),
            start_date=datetime(2025, 1, 1),
            end_date=datetime(2025, 1, 31),
        )

        inventory_report = ReportResponse(
            id=uuid4(),
            report_type="low_stock",
            status="completed",
            created_at=datetime(2025, 1, 10),
            start_date=datetime(2025, 1, 1),
            end_date=datetime(2025, 1, 31),
        )

        mock_order_adapter.list_reports = AsyncMock(
            return_value=PaginatedReportsResponse(
                items=[order_report],
                total=1,
                page=1,
                size=1,
                has_next=False,
                has_previous=False,
            )
        )

        mock_inventory_adapter.list_reports = AsyncMock(
            return_value=PaginatedReportsResponse(
                items=[inventory_report],
                total=1,
                page=1,
                size=1,
                has_next=False,
                has_previous=False,
            )
        )

        result = await list_reports(
            limit=10,
            offset=0,
            status=None,
            report_type=None,
            order_reports=mock_order_adapter,
            inventory_reports=mock_inventory_adapter,
            user=mock_user,
        )

        # Should aggregate both reports
        assert result.total == 2
        assert len(result.items) == 2

    @pytest.mark.asyncio
    async def test_list_reports_sorts_by_created_at_desc(
        self, mock_user, mock_order_adapter, mock_inventory_adapter
    ):
        """Test that aggregated reports are sorted by created_at DESC."""
        older_report = ReportResponse(
            id=uuid4(),
            report_type="orders_per_seller",
            status="completed",
            created_at=datetime(2025, 1, 10),
            start_date=datetime(2025, 1, 1),
            end_date=datetime(2025, 1, 31),
        )

        newer_report = ReportResponse(
            id=uuid4(),
            report_type="low_stock",
            status="completed",
            created_at=datetime(2025, 1, 20),
            start_date=datetime(2025, 1, 1),
            end_date=datetime(2025, 1, 31),
        )

        mock_order_adapter.list_reports = AsyncMock(
            return_value=PaginatedReportsResponse(
                items=[older_report],
                total=1,
                page=1,
                size=1,
                has_next=False,
                has_previous=False,
            )
        )

        mock_inventory_adapter.list_reports = AsyncMock(
            return_value=PaginatedReportsResponse(
                items=[newer_report],
                total=1,
                page=1,
                size=1,
                has_next=False,
                has_previous=False,
            )
        )

        result = await list_reports(
            limit=10,
            offset=0,
            status=None,
            report_type=None,
            order_reports=mock_order_adapter,
            inventory_reports=mock_inventory_adapter,
            user=mock_user,
        )

        # Newer report should be first
        assert result.items[0].created_at == datetime(2025, 1, 20)
        assert result.items[1].created_at == datetime(2025, 1, 10)

    @pytest.mark.asyncio
    async def test_list_reports_handles_service_errors_gracefully(
        self, mock_user, mock_order_adapter, mock_inventory_adapter
    ):
        """Test that service errors are logged but don't fail the request."""
        mock_order_adapter.list_reports = AsyncMock(
            side_effect=Exception("Order service down")
        )

        inventory_report = ReportResponse(
            id=uuid4(),
            report_type="low_stock",
            status="completed",
            created_at=datetime(2025, 1, 10),
            start_date=datetime(2025, 1, 1),
            end_date=datetime(2025, 1, 31),
        )

        mock_inventory_adapter.list_reports = AsyncMock(
            return_value=PaginatedReportsResponse(
                items=[inventory_report],
                total=1,
                page=1,
                size=1,
                has_next=False,
                has_previous=False,
            )
        )

        result = await list_reports(
            limit=10,
            offset=0,
            status=None,
            report_type=None,
            order_reports=mock_order_adapter,
            inventory_reports=mock_inventory_adapter,
            user=mock_user,
        )

        # Should return inventory reports even though order service failed
        assert result.total == 1
        assert len(result.items) == 1


class TestGetReport:
    """Test get_report controller function."""

    @pytest.mark.asyncio
    async def test_get_report_from_order_service(
        self, mock_user, mock_order_adapter, mock_inventory_adapter
    ):
        """Test getting a report from Order service."""
        report_id = uuid4()
        mock_response = ReportResponse(
            id=report_id,
            report_type="orders_per_seller",
            status="completed",
            created_at=datetime.now(),
            start_date=datetime(2025, 1, 1),
            end_date=datetime(2025, 1, 31),
            download_url="https://s3.example.com/report.json",
        )

        mock_order_adapter.get_report = AsyncMock(return_value=mock_response)

        result = await get_report(
            report_id, mock_order_adapter, mock_inventory_adapter, mock_user
        )

        assert result.id == report_id
        mock_order_adapter.get_report.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_report_falls_back_to_inventory_service(
        self, mock_user, mock_order_adapter, mock_inventory_adapter
    ):
        """Test falling back to Inventory service when not found in Order."""
        report_id = uuid4()

        # Order service doesn't have it (returns 404)
        mock_order_adapter.get_report = AsyncMock(
            side_effect=MicroserviceHTTPError("order", 404, "Not found")
        )

        # Inventory service has it
        mock_response = ReportResponse(
            id=report_id,
            report_type="low_stock",
            status="completed",
            created_at=datetime.now(),
            start_date=datetime(2025, 1, 1),
            end_date=datetime(2025, 1, 31),
            download_url="https://s3.example.com/report.json",
        )
        mock_inventory_adapter.get_report = AsyncMock(return_value=mock_response)

        result = await get_report(
            report_id, mock_order_adapter, mock_inventory_adapter, mock_user
        )

        assert result.id == report_id
        assert result.report_type == "low_stock"

    @pytest.mark.asyncio
    async def test_get_report_not_found_in_any_service(
        self, mock_user, mock_order_adapter, mock_inventory_adapter
    ):
        """Test that 404 is returned when report not found in any service."""
        report_id = uuid4()

        # Both services return 404
        mock_order_adapter.get_report = AsyncMock(
            side_effect=MicroserviceHTTPError("order", 404, "Not found")
        )
        mock_inventory_adapter.get_report = AsyncMock(
            side_effect=MicroserviceHTTPError("inventory", 404, "Not found")
        )

        with pytest.raises(HTTPException) as exc_info:
            await get_report(
                report_id, mock_order_adapter, mock_inventory_adapter, mock_user
            )

        assert exc_info.value.status_code == 404
