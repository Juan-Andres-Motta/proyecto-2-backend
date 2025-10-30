"""Thin controllers for reports - just delegate to use cases.

No business logic, no validation, no try/catch.
All exceptions are handled by global exception handlers.
Background task generation is delegated to a separate use case.
"""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, Query
from fastapi.responses import JSONResponse

from src.adapters.input.schemas import (
    PaginatedReportsResponse,
    ReportCreateInput,
    ReportResponse,
)
from src.application.use_cases.create_report import CreateReportUseCase
from src.application.use_cases.generate_report import GenerateReportUseCase
from src.application.use_cases.get_report import GetReportUseCase
from src.application.use_cases.list_reports import (
    ListReportsInput,
    ListReportsUseCase,
)
from src.infrastructure.dependencies import (
    get_create_report_use_case,
    get_generate_report_use_case,
    get_get_report_use_case,
    get_list_reports_use_case,
)

router = APIRouter(tags=["reports"])


@router.post(
    "/reports",
    responses={
        202: {"description": "Report creation request accepted"},
        422: {"description": "Invalid input"},
    },
)
async def create_report(
    report_input: ReportCreateInput,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    create_use_case: CreateReportUseCase = Depends(get_create_report_use_case),
    generate_use_case: GenerateReportUseCase = Depends(get_generate_report_use_case),
):
    """Create a report generation request - THIN controller.

    The report is generated asynchronously in the background.
    Returns immediately with status 'pending'.
    """
    # Create report from use case input
    from src.application.use_cases.create_report import CreateReportInput as UseCaseInput
    from src.domain.value_objects import ReportType

    use_case_input = UseCaseInput(
        user_id=report_input.user_id,
        report_type=ReportType(report_input.report_type),
        start_date=report_input.start_date,
        end_date=report_input.end_date,
        filters=report_input.filters,
    )

    report = await create_use_case.execute(use_case_input)

    # Schedule background generation
    background_tasks.add_task(generate_use_case.execute, report.id)

    return JSONResponse(
        content={
            "report_id": str(report.id),
            "status": report.status.value,
            "message": "Report generation started. You will be notified when ready.",
        },
        status_code=202,
    )


@router.get(
    "/reports",
    response_model=PaginatedReportsResponse,
    responses={
        200: {"description": "List of reports"},
        422: {"description": "Invalid query parameters"},
    },
)
async def list_reports(
    user_id: UUID = Query(..., description="User ID from authentication"),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    status: Optional[str] = Query(None),
    report_type: Optional[str] = Query(None),
    use_case: ListReportsUseCase = Depends(get_list_reports_use_case),
):
    """List reports for the authenticated user - THIN controller."""
    # Delegate to use case
    input_data = ListReportsInput(
        user_id=user_id,
        limit=limit,
        offset=offset,
        status=status,
        report_type=report_type,
    )

    result = await use_case.execute(input_data)

    # Calculate pagination
    page = (offset // limit) + 1 if limit > 0 else 1
    has_next = (offset + limit) < result.total
    has_previous = offset > 0

    # Convert to response schema
    items = [
        ReportResponse(
            id=r.id,
            report_type=r.report_type.value,
            status=r.status.value,
            start_date=r.start_date,
            end_date=r.end_date,
            filters=r.filters,
            created_at=r.created_at,
            completed_at=r.completed_at,
            download_url=None,  # Not included in list view
            error_message=r.error_message,
        )
        for r in result.reports
    ]

    return PaginatedReportsResponse(
        items=items,
        total=result.total,
        page=page,
        size=len(items),
        has_next=has_next,
        has_previous=has_previous,
    )


@router.get(
    "/reports/{report_id}",
    response_model=ReportResponse,
    responses={
        200: {"description": "Report details"},
        404: {"description": "Report not found"},
        422: {"description": "Invalid parameters"},
    },
)
async def get_report(
    report_id: UUID,
    user_id: UUID = Query(..., description="User ID from authentication"),
    use_case: GetReportUseCase = Depends(get_get_report_use_case),
):
    """Get a report by ID with presigned download URL - THIN controller."""
    # Delegate to use case
    result = await use_case.execute(report_id, user_id)

    if not result:
        # Use case returns None for not found - let middleware handle this
        from src.domain.exceptions import ReportNotFoundException

        raise ReportNotFoundException(report_id)

    report = result.report
    download_url = result.download_url

    return ReportResponse(
        id=report.id,
        report_type=report.report_type.value,
        status=report.status.value,
        start_date=report.start_date,
        end_date=report.end_date,
        filters=report.filters,
        created_at=report.created_at,
        completed_at=report.completed_at,
        download_url=download_url,
        error_message=report.error_message,
    )
