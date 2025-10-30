"""Unit tests for reports controller - THIN controller testing pattern."""
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from src.adapters.input.controllers.reports_controller import router
from src.domain.entities.report import Report
from src.domain.exceptions import NotFoundException
from src.domain.value_objects import ReportStatus, ReportType


@pytest.mark.asyncio
async def test_create_report_success():
    """Test successful report creation with background task."""
    from src.application.use_cases.get_report import GetReportOutput
    from src.infrastructure.dependencies import (
        get_create_report_use_case,
        get_generate_report_use_case,
    )

    app = FastAPI()
    app.include_router(router)

    user_id = uuid.uuid4()
    report_id = uuid.uuid4()

    # Mock report entity
    mock_report = MagicMock(spec=Report)
    mock_report.id = report_id
    mock_report.status = ReportStatus.PENDING.value
    mock_report.report_type = ReportType.LOW_STOCK.value
    mock_report.start_date = datetime(2025, 1, 1, tzinfo=timezone.utc)
    mock_report.end_date = datetime(2025, 1, 31, tzinfo=timezone.utc)
    mock_report.filters = {"threshold": 10}
    mock_report.created_at = datetime.now(timezone.utc)
    mock_report.completed_at = None
    mock_report.error_message = None

    # Mock create use case
    mock_create_use_case = AsyncMock()
    mock_create_use_case.execute = AsyncMock(return_value=mock_report)

    # Mock generate use case (background task)
    mock_generate_use_case = AsyncMock()
    mock_generate_use_case.execute = AsyncMock()

    # Override DI dependencies
    app.dependency_overrides[get_create_report_use_case] = lambda: mock_create_use_case
    app.dependency_overrides[get_generate_report_use_case] = (
        lambda: mock_generate_use_case
    )

    request_data = {
        "user_id": str(user_id),
        "report_type": "low_stock",
        "start_date": "2025-01-01T00:00:00Z",
        "end_date": "2025-01-31T00:00:00Z",
        "filters": {"threshold": 10},
    }

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/reports", json=request_data
        )

    assert response.status_code == 202
    data = response.json()
    assert data["report_id"] == str(report_id)
    assert data["status"] == ReportStatus.PENDING.value
    assert "Report generation started" in data["message"]

    # Verify create use case was called
    mock_create_use_case.execute.assert_called_once()


@pytest.mark.asyncio
async def test_create_report_missing_user_id():
    """Test creating report without user_id in body."""
    app = FastAPI()
    app.include_router(router)

    request_data = {
        "report_type": "low_stock",
        "start_date": "2025-01-01T00:00:00Z",
        "end_date": "2025-01-31T00:00:00Z",
    }

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post("/reports", json=request_data)

    # FastAPI should return 422 for missing required field in body
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_report_invalid_data():
    """Test creating report with invalid data (missing required fields)."""
    app = FastAPI()
    app.include_router(router)

    user_id = uuid.uuid4()

    request_data = {
        "user_id": str(user_id),
        "report_type": "low_stock",
        # Missing start_date and end_date
    }

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/reports", json=request_data
        )

    # Pydantic should validate and return 422
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_list_reports_success():
    """Test successful list of reports."""
    from src.application.use_cases.list_reports import ListReportsOutput
    from src.infrastructure.dependencies import get_list_reports_use_case

    app = FastAPI()
    app.include_router(router)

    user_id = uuid.uuid4()
    report_id = uuid.uuid4()

    # Mock report entity
    mock_report = MagicMock(spec=Report)
    mock_report.id = report_id
    mock_report.report_type = ReportType.LOW_STOCK.value
    mock_report.status = ReportStatus.COMPLETED.value
    mock_report.start_date = datetime(2025, 1, 1, tzinfo=timezone.utc)
    mock_report.end_date = datetime(2025, 1, 31, tzinfo=timezone.utc)
    mock_report.filters = {}
    mock_report.created_at = datetime(2025, 1, 1, tzinfo=timezone.utc)
    mock_report.completed_at = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    mock_report.error_message = None

    # Mock use case output
    mock_output = ListReportsOutput(reports=[mock_report], total=1, limit=10, offset=0)

    # Mock use case
    mock_use_case = AsyncMock()
    mock_use_case.execute = AsyncMock(return_value=mock_output)

    # Override DI dependency
    app.dependency_overrides[get_list_reports_use_case] = lambda: mock_use_case

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(f"/reports?user_id={user_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["id"] == str(report_id)
    assert data["has_next"] is False
    assert data["has_previous"] is False


@pytest.mark.asyncio
async def test_list_reports_with_pagination():
    """Test list reports with pagination parameters."""
    from src.application.use_cases.list_reports import ListReportsOutput
    from src.infrastructure.dependencies import get_list_reports_use_case

    app = FastAPI()
    app.include_router(router)

    user_id = uuid.uuid4()

    # Mock multiple reports
    mock_reports = []
    for i in range(2):
        mock_report = MagicMock(spec=Report)
        mock_report.id = uuid.uuid4()
        mock_report.report_type = ReportType.LOW_STOCK.value
        mock_report.status = ReportStatus.PENDING.value
        mock_report.start_date = datetime(2025, 1, 1, tzinfo=timezone.utc)
        mock_report.end_date = datetime(2025, 1, 31, tzinfo=timezone.utc)
        mock_report.filters = {}
        mock_report.created_at = datetime(2025, 1, 1, tzinfo=timezone.utc)
        mock_report.completed_at = None
        mock_report.error_message = None
        mock_reports.append(mock_report)

    # Mock use case output - first page with 2 items out of total 5
    mock_output = ListReportsOutput(reports=mock_reports, total=5, limit=2, offset=0)

    # Mock use case
    mock_use_case = AsyncMock()
    mock_use_case.execute = AsyncMock(return_value=mock_output)

    # Override DI dependency
    app.dependency_overrides[get_list_reports_use_case] = lambda: mock_use_case

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(f"/reports?user_id={user_id}&limit=2&offset=0")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 5
    assert len(data["items"]) == 2
    assert data["page"] == 1
    assert data["has_next"] is True
    assert data["has_previous"] is False


@pytest.mark.asyncio
async def test_list_reports_with_filters():
    """Test list reports with status and report_type filters."""
    from src.application.use_cases.list_reports import ListReportsOutput
    from src.infrastructure.dependencies import get_list_reports_use_case

    app = FastAPI()
    app.include_router(router)

    user_id = uuid.uuid4()

    # Mock use case output
    mock_output = ListReportsOutput(reports=[], total=0, limit=10, offset=0)

    # Mock use case
    mock_use_case = AsyncMock()
    mock_use_case.execute = AsyncMock(return_value=mock_output)

    # Override DI dependency
    app.dependency_overrides[get_list_reports_use_case] = lambda: mock_use_case

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(
            f"/reports?user_id={user_id}&status=completed&report_type=low_stock"
        )

    assert response.status_code == 200
    # Verify use case was called with filters
    mock_use_case.execute.assert_called_once()


@pytest.mark.asyncio
async def test_list_reports_validation_errors():
    """Test list reports with invalid query parameters."""
    app = FastAPI()
    app.include_router(router)

    user_id = uuid.uuid4()

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        # Test limit too high
        response = await client.get(f"/reports?user_id={user_id}&limit=101")
        assert response.status_code == 422

        # Test limit too low
        response = await client.get(f"/reports?user_id={user_id}&limit=0")
        assert response.status_code == 422

        # Test negative offset
        response = await client.get(f"/reports?user_id={user_id}&offset=-1")
        assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_report_success_completed():
    """Test getting a completed report with download URL."""
    from src.application.use_cases.get_report import GetReportOutput
    from src.infrastructure.dependencies import get_get_report_use_case

    app = FastAPI()
    app.include_router(router)

    user_id = uuid.uuid4()
    report_id = uuid.uuid4()

    # Mock report entity
    mock_report = MagicMock(spec=Report)
    mock_report.id = report_id
    mock_report.report_type = ReportType.LOW_STOCK.value
    mock_report.status = ReportStatus.COMPLETED.value
    mock_report.start_date = datetime(2025, 1, 1, tzinfo=timezone.utc)
    mock_report.end_date = datetime(2025, 1, 31, tzinfo=timezone.utc)
    mock_report.filters = {}
    mock_report.created_at = datetime(2025, 1, 1, tzinfo=timezone.utc)
    mock_report.completed_at = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    mock_report.error_message = None

    # Mock use case output
    mock_output = GetReportOutput(
        report=mock_report, download_url="https://s3.amazonaws.com/presigned-url"
    )

    # Mock use case
    mock_use_case = AsyncMock()
    mock_use_case.execute = AsyncMock(return_value=mock_output)

    # Override DI dependency
    app.dependency_overrides[get_get_report_use_case] = lambda: mock_use_case

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(f"/reports/{report_id}?user_id={user_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(report_id)
    assert data["status"] == ReportStatus.COMPLETED.value
    assert data["download_url"] == "https://s3.amazonaws.com/presigned-url"


@pytest.mark.asyncio
async def test_get_report_success_pending():
    """Test getting a pending report (no download URL)."""
    from src.application.use_cases.get_report import GetReportOutput
    from src.infrastructure.dependencies import get_get_report_use_case

    app = FastAPI()
    app.include_router(router)

    user_id = uuid.uuid4()
    report_id = uuid.uuid4()

    # Mock report entity
    mock_report = MagicMock(spec=Report)
    mock_report.id = report_id
    mock_report.report_type = ReportType.LOW_STOCK.value
    mock_report.status = ReportStatus.PENDING.value
    mock_report.start_date = datetime(2025, 1, 1, tzinfo=timezone.utc)
    mock_report.end_date = datetime(2025, 1, 31, tzinfo=timezone.utc)
    mock_report.filters = {}
    mock_report.created_at = datetime(2025, 1, 1, tzinfo=timezone.utc)
    mock_report.completed_at = None
    mock_report.error_message = None

    # Mock use case output
    mock_output = GetReportOutput(report=mock_report, download_url=None)

    # Mock use case
    mock_use_case = AsyncMock()
    mock_use_case.execute = AsyncMock(return_value=mock_output)

    # Override DI dependency
    app.dependency_overrides[get_get_report_use_case] = lambda: mock_use_case

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(f"/reports/{report_id}?user_id={user_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(report_id)
    assert data["status"] == ReportStatus.PENDING.value
    assert data["download_url"] is None


@pytest.mark.asyncio
async def test_get_report_not_found():
    """Test getting a non-existent report raises NotFoundException."""
    from src.infrastructure.api.exception_handlers import register_exception_handlers
    from src.infrastructure.dependencies import get_get_report_use_case

    app = FastAPI()
    app.include_router(router)
    register_exception_handlers(app)  # Register middleware to handle NotFoundException

    user_id = uuid.uuid4()
    report_id = uuid.uuid4()

    # Mock use case that returns None
    mock_use_case = AsyncMock()
    mock_use_case.execute = AsyncMock(return_value=None)

    # Override DI dependency
    app.dependency_overrides[get_get_report_use_case] = lambda: mock_use_case

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(f"/reports/{report_id}?user_id={user_id}")

    # Middleware should convert NotFoundException to 404
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_report_invalid_uuid():
    """Test getting report with invalid UUID format."""
    app = FastAPI()
    app.include_router(router)

    user_id = uuid.uuid4()

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(f"/reports/invalid-uuid?user_id={user_id}")

    # FastAPI should return 422 for invalid UUID
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_report_missing_user_id():
    """Test getting report without user_id query parameter."""
    app = FastAPI()
    app.include_router(router)

    report_id = uuid.uuid4()

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(f"/reports/{report_id}")

    # FastAPI should return 422 for missing required query parameter
    assert response.status_code == 422
