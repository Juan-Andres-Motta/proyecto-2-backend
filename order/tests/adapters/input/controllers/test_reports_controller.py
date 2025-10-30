"""Unit tests for reports controller - THIN controller testing pattern."""
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from src.adapters.input.controllers.reports_controller import router
from src.domain.entities import Report
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
    mock_report.status = ReportStatus.PENDING
    mock_report.report_type = ReportType.ORDERS_PER_SELLER
    mock_report.start_date = datetime(2025, 1, 1, tzinfo=timezone.utc)
    mock_report.end_date = datetime(2025, 1, 31, tzinfo=timezone.utc)
    mock_report.filters = {}
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
        "report_type": "orders_per_seller",
        "start_date": "2025-01-01T00:00:00Z",
        "end_date": "2025-01-31T00:00:00Z",
        "filters": {},
    }

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post("/reports", json=request_data)

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
        "report_type": "orders_per_seller",
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
async def test_list_reports_success():
    """Test listing reports for a user."""
    from src.application.use_cases.list_reports import ListReportsOutput
    from src.infrastructure.dependencies import get_list_reports_use_case

    app = FastAPI()
    app.include_router(router)

    user_id = uuid.uuid4()
    report_id = uuid.uuid4()

    # Mock report entity
    mock_report = MagicMock(spec=Report)
    mock_report.id = report_id
    mock_report.report_type = ReportType.ORDERS_PER_SELLER
    mock_report.status = ReportStatus.COMPLETED
    mock_report.start_date = datetime(2025, 1, 1, tzinfo=timezone.utc)
    mock_report.end_date = datetime(2025, 1, 31, tzinfo=timezone.utc)
    mock_report.filters = {}
    mock_report.created_at = datetime.now(timezone.utc)
    mock_report.completed_at = datetime.now(timezone.utc)
    mock_report.error_message = None

    # Mock list use case output
    mock_output = ListReportsOutput(
        reports=[mock_report], total=1, limit=10, offset=0
    )

    mock_use_case = AsyncMock()
    mock_use_case.execute = AsyncMock(return_value=mock_output)

    app.dependency_overrides[get_list_reports_use_case] = lambda: mock_use_case

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(f"/reports?user_id={str(user_id)}&limit=10&offset=0")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["id"] == str(report_id)
    assert data["items"][0]["status"] == ReportStatus.COMPLETED.value


@pytest.mark.asyncio
async def test_list_reports_with_filters():
    """Test listing reports with status and type filters."""
    from src.application.use_cases.list_reports import ListReportsOutput
    from src.infrastructure.dependencies import get_list_reports_use_case

    app = FastAPI()
    app.include_router(router)

    user_id = uuid.uuid4()

    mock_output = ListReportsOutput(reports=[], total=0, limit=10, offset=0)
    mock_use_case = AsyncMock()
    mock_use_case.execute = AsyncMock(return_value=mock_output)

    app.dependency_overrides[get_list_reports_use_case] = lambda: mock_use_case

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(
            f"/reports?user_id={str(user_id)}&status=completed&report_type=orders_per_seller"
        )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert len(data["items"]) == 0


@pytest.mark.asyncio
async def test_list_reports_missing_user_id():
    """Test listing reports without user_id query param."""
    app = FastAPI()
    app.include_router(router)

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/reports")

    # Should return 422 for missing required query param
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_list_reports_pagination():
    """Test pagination in list reports."""
    from src.application.use_cases.list_reports import ListReportsOutput
    from src.infrastructure.dependencies import get_list_reports_use_case

    app = FastAPI()
    app.include_router(router)

    user_id = uuid.uuid4()

    # Mock output with pagination
    mock_reports = []
    for i in range(5):
        mock_report = MagicMock(spec=Report)
        mock_report.id = uuid.uuid4()
        mock_report.report_type = ReportType.ORDERS_PER_SELLER
        mock_report.status = ReportStatus.COMPLETED
        mock_report.start_date = datetime(2025, 1, 1, tzinfo=timezone.utc)
        mock_report.end_date = datetime(2025, 1, 31, tzinfo=timezone.utc)
        mock_report.filters = {}
        mock_report.created_at = datetime.now(timezone.utc)
        mock_report.completed_at = datetime.now(timezone.utc)
        mock_report.error_message = None
        mock_reports.append(mock_report)

    mock_output = ListReportsOutput(reports=mock_reports, total=15, limit=5, offset=5)
    mock_use_case = AsyncMock()
    mock_use_case.execute = AsyncMock(return_value=mock_output)

    app.dependency_overrides[get_list_reports_use_case] = lambda: mock_use_case

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(
            f"/reports?user_id={str(user_id)}&limit=5&offset=5"
        )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 15
    assert data["size"] == 5
    assert data["page"] == 2  # Page 2 (offset=5, limit=5)
    assert data["has_next"] is True
    assert data["has_previous"] is True


@pytest.mark.asyncio
async def test_get_report_success():
    """Test getting a single report by ID."""
    from src.application.use_cases.get_report import GetReportOutput
    from src.infrastructure.dependencies import get_get_report_use_case

    app = FastAPI()
    app.include_router(router)

    user_id = uuid.uuid4()
    report_id = uuid.uuid4()

    # Mock report entity
    mock_report = MagicMock(spec=Report)
    mock_report.id = report_id
    mock_report.report_type = ReportType.ORDERS_PER_SELLER
    mock_report.status = ReportStatus.COMPLETED
    mock_report.start_date = datetime(2025, 1, 1, tzinfo=timezone.utc)
    mock_report.end_date = datetime(2025, 1, 31, tzinfo=timezone.utc)
    mock_report.filters = {}
    mock_report.created_at = datetime.now(timezone.utc)
    mock_report.completed_at = datetime.now(timezone.utc)
    mock_report.error_message = None
    mock_report.s3_key = "reports/test.json"

    mock_output = GetReportOutput(
        report=mock_report,
        download_url="https://s3.amazonaws.com/bucket/reports/test.json?presigned",
    )

    mock_use_case = AsyncMock()
    mock_use_case.execute = AsyncMock(return_value=mock_output)

    app.dependency_overrides[get_get_report_use_case] = lambda: mock_use_case

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(f"/reports/{str(report_id)}?user_id={str(user_id)}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(report_id)
    assert data["status"] == ReportStatus.COMPLETED.value
    assert data["download_url"] is not None
    assert "presigned" in data["download_url"]


@pytest.mark.asyncio
async def test_get_report_not_found():
    """Test getting a report that doesn't exist."""
    from src.infrastructure.api.exception_handlers import register_exception_handlers
    from src.infrastructure.dependencies import get_get_report_use_case

    app = FastAPI()
    app.include_router(router)
    register_exception_handlers(app)  # Register exception handlers to convert NotFoundException to 404

    user_id = uuid.uuid4()
    report_id = uuid.uuid4()

    # Mock use case returns None for not found
    mock_use_case = AsyncMock()
    mock_use_case.execute = AsyncMock(return_value=None)

    app.dependency_overrides[get_get_report_use_case] = lambda: mock_use_case

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(f"/reports/{str(report_id)}?user_id={str(user_id)}")

    # Exception handler should convert ReportNotFoundException to 404
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_report_missing_user_id():
    """Test getting a report without user_id query param."""
    app = FastAPI()
    app.include_router(router)

    report_id = uuid.uuid4()

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(f"/reports/{str(report_id)}")

    # Should return 422 for missing required query param
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_report_pending_no_download_url():
    """Test getting a pending report has no download URL."""
    from src.application.use_cases.get_report import GetReportOutput
    from src.infrastructure.dependencies import get_get_report_use_case

    app = FastAPI()
    app.include_router(router)

    user_id = uuid.uuid4()
    report_id = uuid.uuid4()

    # Mock pending report
    mock_report = MagicMock(spec=Report)
    mock_report.id = report_id
    mock_report.report_type = ReportType.ORDERS_PER_SELLER
    mock_report.status = ReportStatus.PENDING
    mock_report.start_date = datetime(2025, 1, 1, tzinfo=timezone.utc)
    mock_report.end_date = datetime(2025, 1, 31, tzinfo=timezone.utc)
    mock_report.filters = {}
    mock_report.created_at = datetime.now(timezone.utc)
    mock_report.completed_at = None
    mock_report.error_message = None

    mock_output = GetReportOutput(report=mock_report, download_url=None)

    mock_use_case = AsyncMock()
    mock_use_case.execute = AsyncMock(return_value=mock_output)

    app.dependency_overrides[get_get_report_use_case] = lambda: mock_use_case

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(f"/reports/{str(report_id)}?user_id={str(user_id)}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(report_id)
    assert data["status"] == ReportStatus.PENDING.value
    assert data["download_url"] is None


@pytest.mark.asyncio
async def test_get_report_failed_with_error_message():
    """Test getting a failed report includes error message."""
    from src.application.use_cases.get_report import GetReportOutput
    from src.infrastructure.dependencies import get_get_report_use_case

    app = FastAPI()
    app.include_router(router)

    user_id = uuid.uuid4()
    report_id = uuid.uuid4()

    # Mock failed report
    mock_report = MagicMock(spec=Report)
    mock_report.id = report_id
    mock_report.report_type = ReportType.ORDERS_PER_SELLER
    mock_report.status = ReportStatus.FAILED
    mock_report.start_date = datetime(2025, 1, 1, tzinfo=timezone.utc)
    mock_report.end_date = datetime(2025, 1, 31, tzinfo=timezone.utc)
    mock_report.filters = {}
    mock_report.created_at = datetime.now(timezone.utc)
    mock_report.completed_at = datetime.now(timezone.utc)
    mock_report.error_message = "S3 upload failed"

    mock_output = GetReportOutput(report=mock_report, download_url=None)

    mock_use_case = AsyncMock()
    mock_use_case.execute = AsyncMock(return_value=mock_output)

    app.dependency_overrides[get_get_report_use_case] = lambda: mock_use_case

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(f"/reports/{str(report_id)}?user_id={str(user_id)}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(report_id)
    assert data["status"] == ReportStatus.FAILED.value
    assert data["error_message"] == "S3 upload failed"
    assert data["download_url"] is None
