"""Tests for reports controller endpoints."""

import uuid
from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from src.adapters.input.controllers.reports_controller import router
from src.domain.entities.report import Report
from src.domain.value_objects import ReportStatus, ReportType


@pytest.mark.asyncio
async def test_create_report_orders_per_seller():
    """Test creating an orders_per_seller report."""
    app = FastAPI()
    app.include_router(router)

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
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.post(
                    f"/reports?user_id={user_id}", json=report_data
                )

    assert response.status_code == 202
    data = response.json()
    assert "report_id" in data
    assert data["status"] == "pending"
    assert uuid.UUID(data["report_id"]) == report_id


@pytest.mark.asyncio
async def test_create_report_orders_per_status():
    """Test creating an orders_per_status report."""
    app = FastAPI()
    app.include_router(router)

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
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.post(
                    f"/reports?user_id={user_id}", json=report_data
                )

    assert response.status_code == 202
    data = response.json()
    assert data["status"] == "pending"


@pytest.mark.asyncio
async def test_create_report_with_filters():
    """Test creating a report with filters."""
    app = FastAPI()
    app.include_router(router)

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
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.post(
                    f"/reports?user_id={user_id}", json=report_data
                )

    assert response.status_code == 202


@pytest.mark.asyncio
async def test_create_report_missing_required_fields():
    """Test creating report with missing required fields."""
    app = FastAPI()
    app.include_router(router)

    user_id = uuid.uuid4()
    # Missing end_date
    report_data = {
        "report_type": "orders_per_seller",
        "start_date": "2025-01-01T00:00:00",
    }

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(f"/reports?user_id={user_id}", json=report_data)

    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_create_report_invalid_report_type():
    """Test creating report with invalid report_type."""
    app = FastAPI()
    app.include_router(router)

    user_id = uuid.uuid4()
    report_data = {
        "report_type": "invalid_type",
        "start_date": "2025-01-01T00:00:00",
        "end_date": "2025-01-31T23:59:59",
    }

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(f"/reports?user_id={user_id}", json=report_data)

    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_list_reports_empty():
    """Test listing reports when empty."""
    app = FastAPI()
    app.include_router(router)

    user_id = uuid.uuid4()

    with patch(
        "src.application.use_cases.list_reports.ListReportsUseCase"
    ) as MockUseCase:
        mock_use_case = MockUseCase.return_value
        mock_use_case.execute = AsyncMock(return_value=([], 0))

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
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
async def test_list_reports_with_data():
    """Test listing reports with data."""
    app = FastAPI()
    app.include_router(router)

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
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get(f"/reports?user_id={user_id}")

    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 2
    assert data["total"] == 2


@pytest.mark.asyncio
async def test_list_reports_with_status_filter():
    """Test listing reports with status filter."""
    app = FastAPI()
    app.include_router(router)

    user_id = uuid.uuid4()

    with patch(
        "src.application.use_cases.list_reports.ListReportsUseCase"
    ) as MockUseCase:
        mock_use_case = MockUseCase.return_value
        mock_use_case.execute = AsyncMock(return_value=([], 0))

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get(
                f"/reports?user_id={user_id}&status=completed"
            )

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_list_reports_with_report_type_filter():
    """Test listing reports with report_type filter."""
    app = FastAPI()
    app.include_router(router)

    user_id = uuid.uuid4()

    with patch(
        "src.application.use_cases.list_reports.ListReportsUseCase"
    ) as MockUseCase:
        mock_use_case = MockUseCase.return_value
        mock_use_case.execute = AsyncMock(return_value=([], 0))

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get(
                f"/reports?user_id={user_id}&report_type=orders_per_seller"
            )

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_get_report_by_id():
    """Test getting a report by ID."""
    app = FastAPI()
    app.include_router(router)

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
        mock_get_use_case.execute = AsyncMock(return_value=mock_report)

        # Mock S3 service for presigned URL
        mock_s3 = MockS3Service.return_value
        mock_s3.generate_presigned_url = AsyncMock(
            return_value="https://s3.amazonaws.com/presigned-url"
        )

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get(f"/reports/{report_id}?user_id={user_id}")

    assert response.status_code == 200
    data = response.json()
    assert uuid.UUID(data["report_id"]) == report_id
    assert data["status"] == "completed"
    assert "download_url" in data


@pytest.mark.asyncio
async def test_get_report_not_found():
    """Test getting a non-existent report."""
    app = FastAPI()
    app.include_router(router)

    user_id = uuid.uuid4()
    report_id = uuid.uuid4()

    with patch(
        "src.application.use_cases.get_report.GetReportUseCase"
    ) as MockUseCase:
        mock_use_case = MockUseCase.return_value
        mock_use_case.execute = AsyncMock(return_value=None)

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get(f"/reports/{report_id}?user_id={user_id}")

    assert response.status_code == 404
    data = response.json()
    assert "Report not found" in data["detail"]


@pytest.mark.asyncio
async def test_get_report_pending_no_download_url():
    """Test getting a pending report returns no download URL."""
    app = FastAPI()
    app.include_router(router)

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
        mock_use_case.execute = AsyncMock(return_value=mock_report)

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get(f"/reports/{report_id}?user_id={user_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "pending"
    assert data.get("download_url") is None
