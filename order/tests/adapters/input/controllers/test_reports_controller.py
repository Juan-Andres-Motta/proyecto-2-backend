"""Tests for reports controller endpoints."""

import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from src.adapters.input.controllers.reports_controller import router
from src.domain.entities.report import Report
from src.domain.value_objects import ReportStatus, ReportType


# Mock database dependency
@pytest.fixture
def mock_db():
    """Mock database session."""
    mock_session = MagicMock()
    mock_session.commit = AsyncMock()
    mock_session.flush = AsyncMock()  # Add flush for repository save operations
    return mock_session


@pytest.fixture
def app_with_db(mock_db):
    """Create FastAPI app with mocked database dependency."""
    from src.infrastructure.database.config import get_db

    app = FastAPI()
    app.include_router(router)

    # Override the get_db dependency
    async def override_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_get_db
    return app


@pytest.mark.asyncio
async def test_create_report_orders_per_seller(app_with_db):
    """Test creating an orders_per_seller report."""
    user_id = uuid.uuid4()
    report_data = {
        "report_type": "orders_per_seller",
        "start_date": "2025-01-01T00:00:00",
        "end_date": "2025-01-31T23:59:59",
    }

    # Create mock report entity
    report_id = uuid.uuid4()
    mock_report = Report(
        id=report_id,
        user_id=user_id,
        report_type=ReportType.ORDERS_PER_SELLER,
        status=ReportStatus.PENDING,
        start_date=datetime(2025, 1, 1),
        end_date=datetime(2025, 1, 31, 23, 59, 59),
        created_at=datetime.now(),
    )

    with patch(
        "src.application.use_cases.create_report.CreateReportUseCase"
    ) as MockUseCase:
        mock_use_case = MockUseCase.return_value
        mock_use_case.execute = AsyncMock(return_value=mock_report)

        # Mock background task
        with patch(
            "src.adapters.input.controllers.reports_controller.asyncio.create_task"
        ):
            async with AsyncClient(
                transport=ASGITransport(app=app_with_db), base_url="http://test"
            ) as client:
                response = await client.post(
                    f"/reports?user_id={user_id}", json=report_data
                )

    assert response.status_code == 202
    data = response.json()
    assert "report_id" in data
    assert data["status"] == "pending"
    # Verify report_id is a valid UUID (actual ID comes from repository)
    assert uuid.UUID(data["report_id"])


@pytest.mark.asyncio
async def test_create_report_orders_per_status(app_with_db):
    """Test creating an orders_per_status report."""

    user_id = uuid.uuid4()
    report_data = {
        "report_type": "orders_per_status",
        "start_date": "2025-01-01T00:00:00",
        "end_date": "2025-01-31T23:59:59",
    }

    report_id = uuid.uuid4()
    mock_report = Report(
        id=report_id,
        user_id=user_id,
        report_type=ReportType.ORDERS_PER_STATUS,
        status=ReportStatus.PENDING,
        start_date=datetime(2025, 1, 1),
        end_date=datetime(2025, 1, 31, 23, 59, 59),
        created_at=datetime.now(),
    )

    with patch(
        "src.application.use_cases.create_report.CreateReportUseCase"
    ) as MockUseCase:
        mock_use_case = MockUseCase.return_value
        mock_use_case.execute = AsyncMock(return_value=mock_report)

        with patch(
            "src.adapters.input.controllers.reports_controller.asyncio.create_task"
        ):
            async with AsyncClient(
                transport=ASGITransport(app=app_with_db), base_url="http://test"
            ) as client:
                response = await client.post(
                    f"/reports?user_id={user_id}", json=report_data
                )

    assert response.status_code == 202
    data = response.json()
    assert data["status"] == "pending"


@pytest.mark.asyncio
async def test_create_report_with_filters(app_with_db):
    """Test creating a report with filters."""

    user_id = uuid.uuid4()
    seller_id = uuid.uuid4()
    report_data = {
        "report_type": "orders_per_seller",
        "start_date": "2025-01-01T00:00:00",
        "end_date": "2025-01-31T23:59:59",
        "filters": {"seller_id": str(seller_id)},
    }

    report_id = uuid.uuid4()
    mock_report = Report(
        id=report_id,
        user_id=user_id,
        report_type=ReportType.ORDERS_PER_SELLER,
        status=ReportStatus.PENDING,
        start_date=datetime(2025, 1, 1),
        end_date=datetime(2025, 1, 31, 23, 59, 59),
        created_at=datetime.now(),
        filters={"seller_id": str(seller_id)},
    )

    with patch(
        "src.application.use_cases.create_report.CreateReportUseCase"
    ) as MockUseCase:
        mock_use_case = MockUseCase.return_value
        mock_use_case.execute = AsyncMock(return_value=mock_report)

        with patch(
            "src.adapters.input.controllers.reports_controller.asyncio.create_task"
        ):
            async with AsyncClient(
                transport=ASGITransport(app=app_with_db), base_url="http://test"
            ) as client:
                response = await client.post(
                    f"/reports?user_id={user_id}", json=report_data
                )

    assert response.status_code == 202


@pytest.mark.asyncio
async def test_create_report_missing_required_fields(app_with_db):
    """Test creating report with missing required fields."""

    user_id = uuid.uuid4()
    # Missing end_date
    report_data = {
        "report_type": "orders_per_seller",
        "start_date": "2025-01-01T00:00:00",
    }

    async with AsyncClient(
        transport=ASGITransport(app=app_with_db), base_url="http://test"
    ) as client:
        response = await client.post(f"/reports?user_id={user_id}", json=report_data)

    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_create_report_invalid_report_type(app_with_db):
    """Test creating report with invalid report_type."""

    user_id = uuid.uuid4()
    report_data = {
        "report_type": "invalid_type",
        "start_date": "2025-01-01T00:00:00",
        "end_date": "2025-01-31T23:59:59",
    }

    async with AsyncClient(
        transport=ASGITransport(app=app_with_db), base_url="http://test"
    ) as client:
        response = await client.post(f"/reports?user_id={user_id}", json=report_data)

    assert response.status_code == 400  # Bad request (invalid report_type)


@pytest.mark.asyncio
async def test_list_reports_empty(app_with_db):
    """Test listing reports when empty."""

    user_id = uuid.uuid4()

    with patch(
        "src.application.use_cases.list_reports.ListReportsUseCase"
    ) as MockUseCase:
        mock_use_case = MockUseCase.return_value
        mock_use_case.execute = AsyncMock(return_value=([], 0))

        async with AsyncClient(
            transport=ASGITransport(app=app_with_db), base_url="http://test"
        ) as client:
            response = await client.get(f"/reports?user_id={user_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0
    assert data["page"] == 1
    assert data["size"] == 0
    assert data["has_next"] is False
    assert data["has_previous"] is False


@pytest.mark.asyncio
async def test_list_reports_with_data(app_with_db):
    """Test listing reports with data."""

    user_id = uuid.uuid4()

    report1 = Report(
        id=uuid.uuid4(),
        user_id=user_id,
        report_type=ReportType.ORDERS_PER_SELLER,
        status=ReportStatus.COMPLETED,
        start_date=datetime(2025, 1, 1),
        end_date=datetime(2025, 1, 31),
        created_at=datetime.now(),
        s3_bucket="test-bucket",
        s3_key="test-key",
    )

    report2 = Report(
        id=uuid.uuid4(),
        user_id=user_id,
        report_type=ReportType.ORDERS_PER_STATUS,
        status=ReportStatus.PENDING,
        start_date=datetime(2025, 1, 1),
        end_date=datetime(2025, 1, 31),
        created_at=datetime.now(),
    )

    with patch(
        "src.application.use_cases.list_reports.ListReportsUseCase"
    ) as MockUseCase:
        mock_use_case = MockUseCase.return_value
        mock_use_case.execute = AsyncMock(return_value=([report1, report2], 2))

        async with AsyncClient(
            transport=ASGITransport(app=app_with_db), base_url="http://test"
        ) as client:
            response = await client.get(f"/reports?user_id={user_id}")

    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 2
    assert data["total"] == 2


@pytest.mark.asyncio
async def test_list_reports_with_status_filter(app_with_db):
    """Test listing reports with status filter."""

    user_id = uuid.uuid4()

    with patch(
        "src.application.use_cases.list_reports.ListReportsUseCase"
    ) as MockUseCase:
        mock_use_case = MockUseCase.return_value
        mock_use_case.execute = AsyncMock(return_value=([], 0))

        async with AsyncClient(
            transport=ASGITransport(app=app_with_db), base_url="http://test"
        ) as client:
            response = await client.get(
                f"/reports?user_id={user_id}&status=completed"
            )

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_list_reports_with_report_type_filter(app_with_db):
    """Test listing reports with report_type filter."""

    user_id = uuid.uuid4()

    with patch(
        "src.application.use_cases.list_reports.ListReportsUseCase"
    ) as MockUseCase:
        mock_use_case = MockUseCase.return_value
        mock_use_case.execute = AsyncMock(return_value=([], 0))

        async with AsyncClient(
            transport=ASGITransport(app=app_with_db), base_url="http://test"
        ) as client:
            response = await client.get(
                f"/reports?user_id={user_id}&report_type=orders_per_seller"
            )

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_get_report_by_id(app_with_db):
    """Test getting a report by ID."""

    user_id = uuid.uuid4()
    report_id = uuid.uuid4()

    mock_report = Report(
        id=report_id,
        user_id=user_id,
        report_type=ReportType.ORDERS_PER_SELLER,
        status=ReportStatus.COMPLETED,
        start_date=datetime(2025, 1, 1),
        end_date=datetime(2025, 1, 31),
        created_at=datetime.now(),
        s3_bucket="test-bucket",
        s3_key="test-key",
        completed_at=datetime.now(),
    )

    with patch(
        "src.application.use_cases.get_report.GetReportUseCase"
    ) as MockGetUseCase, patch(
        "src.domain.services.s3_service.S3Service"
    ) as MockS3Service:
        mock_get_use_case = MockGetUseCase.return_value
        # Fix: GetReportUseCase.execute returns a tuple (report, download_url)
        mock_get_use_case.execute = AsyncMock(
            return_value=(mock_report, "https://s3.amazonaws.com/presigned-url")
        )

        # Mock S3 service for presigned URL
        mock_s3 = MockS3Service.return_value
        mock_s3.generate_presigned_url = AsyncMock(
            return_value="https://s3.amazonaws.com/presigned-url"
        )

        async with AsyncClient(
            transport=ASGITransport(app=app_with_db), base_url="http://test"
        ) as client:
            response = await client.get(f"/reports/{report_id}?user_id={user_id}")

    assert response.status_code == 200
    data = response.json()
    assert uuid.UUID(data["report_id"]) == report_id
    assert data["status"] == "completed"
    assert "download_url" in data


@pytest.mark.asyncio
async def test_get_report_not_found(app_with_db):
    """Test getting a non-existent report."""

    user_id = uuid.uuid4()
    report_id = uuid.uuid4()

    with patch(
        "src.application.use_cases.get_report.GetReportUseCase"
    ) as MockUseCase:
        mock_use_case = MockUseCase.return_value
        # Fix: Return tuple (None, None) instead of just None
        mock_use_case.execute = AsyncMock(return_value=(None, None))

        async with AsyncClient(
            transport=ASGITransport(app=app_with_db), base_url="http://test"
        ) as client:
            response = await client.get(f"/reports/{report_id}?user_id={user_id}")

    assert response.status_code == 404
    data = response.json()
    assert "Report not found" in data["detail"]


@pytest.mark.asyncio
async def test_get_report_pending_no_download_url(app_with_db):
    """Test getting a pending report returns no download URL."""

    user_id = uuid.uuid4()
    report_id = uuid.uuid4()

    mock_report = Report(
        id=report_id,
        user_id=user_id,
        report_type=ReportType.ORDERS_PER_SELLER,
        status=ReportStatus.PENDING,
        start_date=datetime(2025, 1, 1),
        end_date=datetime(2025, 1, 31),
        created_at=datetime.now(),
    )

    with patch(
        "src.application.use_cases.get_report.GetReportUseCase"
    ) as MockUseCase:
        mock_use_case = MockUseCase.return_value
        # Fix: Return tuple (report, None) since no download URL for pending reports
        mock_use_case.execute = AsyncMock(return_value=(mock_report, None))

        async with AsyncClient(
            transport=ASGITransport(app=app_with_db), base_url="http://test"
        ) as client:
            response = await client.get(f"/reports/{report_id}?user_id={user_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "pending"
    assert data.get("download_url") is None
