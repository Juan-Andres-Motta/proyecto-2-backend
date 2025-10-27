"""Reports controller for HTTP endpoints."""

import asyncio
import logging
import os
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.adapters.input.schemas import (
    PaginatedReportsResponse,
    ReportCreateInput,
    ReportCreateResponse,
    ReportResponse,
)
from src.adapters.output.repositories.report_repository import ReportRepository
from src.application.use_cases.create_report import CreateReportInput, CreateReportUseCase
from src.domain.value_objects import ReportStatus, ReportType
from src.infrastructure.database.config import get_db

logger = logging.getLogger(__name__)
router = APIRouter(tags=["reports"])


@router.post(
    "/reports",
    response_model=ReportCreateResponse,
    status_code=202,
    responses={
        202: {"description": "Report creation request accepted"},
        400: {"description": "Invalid input"},
    },
)
async def create_report(
    report_input: ReportCreateInput,
    user_id: UUID = Query(..., description="User ID from authentication"),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a report generation request.

    The report is generated asynchronously. Returns immediately with status 'pending'.
    User will be notified via Ably when the report is ready.

    Args:
        report_input: Report creation input
        user_id: Authenticated user ID
        db: Database session

    Returns:
        ReportCreateResponse with report_id and status
    """
    logger.info(f"Creating report for user {user_id}: {report_input.report_type}")

    try:
        # Validate report type
        try:
            report_type = ReportType(report_input.report_type)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid report_type. Must be one of: {[t.value for t in ReportType]}",
            )

        # Initialize repository and use case
        repository = ReportRepository(db)
        use_case = CreateReportUseCase(repository)

        # Create report
        use_case_input = CreateReportInput(
            user_id=user_id,
            report_type=report_type,
            start_date=report_input.start_date,
            end_date=report_input.end_date,
            filters=report_input.filters,
        )

        report = await use_case.execute(use_case_input)
        await db.commit()

        # Spawn async background task for report generation
        asyncio.create_task(_generate_report_background(report.id))

        logger.info(f"Report {report.id} created successfully")

        return ReportCreateResponse(
            report_id=report.id,
            status=report.status.value,
            message="Report generation started. You will be notified when ready.",
        )

    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error creating report: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/reports",
    response_model=PaginatedReportsResponse,
    responses={
        200: {"description": "List of reports"},
    },
)
async def list_reports(
    user_id: UUID = Query(..., description="User ID from authentication"),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    status: Optional[str] = Query(None),
    report_type: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """
    List reports for the authenticated user.

    Args:
        user_id: Authenticated user ID
        limit: Maximum number of reports to return
        offset: Number of reports to skip
        status: Optional status filter
        report_type: Optional report type filter
        db: Database session

    Returns:
        PaginatedReportsResponse with list of reports
    """
    logger.info(f"Listing reports for user {user_id}")

    try:
        # Import use case here to avoid module-level import issues
        from src.application.use_cases.list_reports import ListReportsUseCase

        # Parse filters
        status_filter = ReportStatus(status) if status else None
        type_filter = ReportType(report_type) if report_type else None

        # Initialize repository and use case
        repository = ReportRepository(db)
        use_case = ListReportsUseCase(repository)

        # List reports
        reports, total = await use_case.execute(
            user_id=user_id,
            limit=limit,
            offset=offset,
            status=status_filter,
            report_type=type_filter,
        )

        # Calculate pagination
        page = (offset // limit) + 1 if limit > 0 else 1
        has_next = (offset + limit) < total
        has_previous = offset > 0

        # Convert to response schema
        items = [
            ReportResponse(
                id=r.id,
                report_type=r.report_type.value,
                status=r.status.value,
                start_date=r.start_date,
                end_date=r.end_date,
                created_at=r.created_at,
                completed_at=r.completed_at,
                download_url=None,  # Not included in list view
                error_message=r.error_message,
            )
            for r in reports
        ]

        return PaginatedReportsResponse(
            items=items,
            total=total,
            page=page,
            size=len(items),
            has_next=has_next,
            has_previous=has_previous,
        )

    except Exception as e:
        logger.error(f"Error listing reports: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/reports/{report_id}",
    response_model=ReportResponse,
    responses={
        200: {"description": "Report details"},
        404: {"description": "Report not found"},
        403: {"description": "Unauthorized"},
    },
)
async def get_report(
    report_id: UUID,
    user_id: UUID = Query(..., description="User ID from authentication"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get a report by ID with presigned download URL.

    Args:
        report_id: Report UUID
        user_id: Authenticated user ID
        db: Database session

    Returns:
        ReportResponse with report details and download URL if completed
    """
    logger.info(f"Getting report {report_id} for user {user_id}")

    try:
        # Import dependencies here to avoid module-level import issues
        from src.application.use_cases.get_report import GetReportUseCase
        from src.domain.services.s3_service import S3Service

        # Initialize services
        repository = ReportRepository(db)
        s3_bucket = os.getenv("S3_REPORTS_BUCKET")
        aws_region = os.getenv("AWS_REGION", "us-east-1")
        s3_service = S3Service(bucket_name=s3_bucket, region=aws_region)

        # Initialize use case
        use_case = GetReportUseCase(repository, s3_service)

        # Get report
        report, download_url = await use_case.execute(report_id, user_id)

        if not report:
            raise HTTPException(status_code=404, detail="Report not found")

        return ReportResponse(
            id=report.id,
            report_type=report.report_type.value,
            status=report.status.value,
            start_date=report.start_date,
            end_date=report.end_date,
            created_at=report.created_at,
            completed_at=report.completed_at,
            download_url=download_url,
            error_message=report.error_message,
        )

    except ValueError as e:
        logger.error(f"Authorization error: {e}")
        raise HTTPException(status_code=403, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting report {report_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


async def _generate_report_background(report_id: UUID):
    """
    Background task for generating reports.

    This runs asynchronously after the API responds.
    """
    logger.info(f"Starting background task for report {report_id}")

    # Import dependencies here to avoid module-level import issues
    from src.application.use_cases.generate_report import GenerateReportUseCase
    from src.domain.services.s3_service import S3Service
    from src.domain.services.sqs_publisher import SQSPublisher
    from src.infrastructure.database.config import async_session_maker

    async with async_session_maker() as session:
        try:
            # Initialize services
            s3_bucket = os.getenv("S3_REPORTS_BUCKET")
            sqs_queue_url = os.getenv("SQS_REPORTS_QUEUE_URL")
            aws_region = os.getenv("AWS_REGION", "us-east-1")

            repository = ReportRepository(session)
            s3_service = S3Service(bucket_name=s3_bucket, region=aws_region)
            sqs_publisher = SQSPublisher(queue_url=sqs_queue_url, region=aws_region)

            # Generate report
            use_case = GenerateReportUseCase(
                report_repository=repository,
                s3_service=s3_service,
                sqs_publisher=sqs_publisher,
                db_session=session,
            )

            await use_case.execute(report_id)

        except Exception as e:
            logger.error(
                f"Background task failed for report {report_id}: {e}", exc_info=True
            )
