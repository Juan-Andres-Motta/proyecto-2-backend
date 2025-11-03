"""Reports controller for BFF."""

import asyncio
import logging
from typing import Dict, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from common.auth.dependencies import require_web_user
from common.error_schemas import NotFoundErrorResponse, ValidationErrorResponse
from common.exceptions import MicroserviceError, MicroserviceHTTPError, ResourceNotFoundError
from dependencies import get_inventory_reports_adapter, get_order_reports_adapter

from ..adapters.reports_adapter import InventoryReportsAdapter, OrderReportsAdapter
from ..schemas.report_schemas import (
    PaginatedReportsResponse,
    ReportCreateRequest,
    ReportCreateResponse,
    ReportResponse,
    ReportStatus,
    ReportType,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/reports",
    response_model=ReportCreateResponse,
    status_code=status.HTTP_202_ACCEPTED,
    responses={
        202: {"description": "Report generation request accepted"},
        401: {"description": "Unauthorized - Invalid or missing token"},
        403: {"description": "Forbidden - Requires web_users group"},
        422: {"description": "Invalid request data", "model": ValidationErrorResponse},
    },
)
async def create_report(
    request: ReportCreateRequest,
    order_reports: OrderReportsAdapter = Depends(get_order_reports_adapter),
    inventory_reports: InventoryReportsAdapter = Depends(get_inventory_reports_adapter),
    user: Dict = Depends(require_web_user),
):
    """
    Create a report generation request.

    Routes to appropriate microservice based on report type:
    - orders_per_seller, orders_per_status → Order microservice
    - low_stock → Inventory microservice

    Args:
        request: Report creation request
        order_reports: Order reports adapter (injected)
        inventory_reports: Inventory reports adapter (injected)
        user: Authenticated user (from JWT)

    Returns:
        ReportCreateResponse with report_id and status
    """
    user_id = UUID(user["sub"])
    logger.info(f"Creating report: type={request.report_type}, user={user_id}")

    try:
        # Route to appropriate microservice based on report type
        if request.report_type in [
            ReportType.ORDERS_PER_SELLER,
            ReportType.ORDERS_PER_STATUS,
        ]:
            # Order microservice
            adapter = order_reports
        elif request.report_type == ReportType.LOW_STOCK:
            # Inventory microservice
            adapter = inventory_reports
        else:
            raise HTTPException(status_code=400, detail="Invalid report type")

        # Create report
        response = await adapter.create_report(user_id=user_id, request=request)

        logger.info(f"Report {response.report_id} created successfully")
        return response

    except MicroserviceError as e:
        logger.error(f"Microservice error creating report: {e}")
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error creating report: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/reports",
    response_model=PaginatedReportsResponse,
    responses={
        200: {"description": "List of reports"},
        401: {"description": "Unauthorized - Invalid or missing token"},
        403: {"description": "Forbidden - Requires web_users group"},
    },
)
async def list_reports(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    status: Optional[str] = Query(None),
    report_type: Optional[str] = Query(None),
    order_reports: OrderReportsAdapter = Depends(get_order_reports_adapter),
    inventory_reports: InventoryReportsAdapter = Depends(get_inventory_reports_adapter),
    user: Dict = Depends(require_web_user),
):
    """
    List all reports for the authenticated user.

    Aggregates reports from Order and Inventory microservices.

    Args:
        limit: Maximum number of reports to return
        offset: Number of reports to skip
        status: Optional status filter
        report_type: Optional report type filter
        order_reports: Order reports adapter (injected)
        inventory_reports: Inventory reports adapter (injected)
        user: Authenticated user (from JWT)

    Returns:
        PaginatedReportsResponse with list of reports
    """
    user_id = UUID(user["sub"])
    logger.info(f"Listing reports for user {user_id}")

    try:
        # Parse filters
        status_filter = ReportStatus(status) if status else None
        type_filter = ReportType(report_type) if report_type else None

        # If type filter is specified, only query relevant microservice
        if type_filter in [ReportType.ORDERS_PER_SELLER, ReportType.ORDERS_PER_STATUS]:
            # Only Order microservice
            response = await order_reports.list_reports(
                user_id=user_id,
                limit=limit,
                offset=offset,
                status=status_filter,
                report_type=type_filter,
            )
            return response

        elif type_filter == ReportType.LOW_STOCK:
            # Only Inventory microservice
            response = await inventory_reports.list_reports(
                user_id=user_id,
                limit=limit,
                offset=offset,
                status=status_filter,
                report_type=type_filter,
            )
            return response

        else:
            # No type filter - aggregate from both microservices
            # Query both in parallel
            order_task = order_reports.list_reports(
                user_id=user_id,
                limit=limit,
                offset=offset,
                status=status_filter,
                report_type=None,
            )
            inventory_task = inventory_reports.list_reports(
                user_id=user_id,
                limit=limit,
                offset=offset,
                status=status_filter,
                report_type=None,
            )

            order_response, inventory_response = await asyncio.gather(
                order_task, inventory_task, return_exceptions=True
            )

            # Handle errors gracefully
            all_items = []
            total = 0

            if isinstance(order_response, Exception):
                logger.error(f"Order service error: {order_response}")
            else:
                all_items.extend(order_response.items)
                total += order_response.total

            if isinstance(inventory_response, Exception):
                logger.error(f"Inventory service error: {inventory_response}")
            else:
                all_items.extend(inventory_response.items)
                total += inventory_response.total

            # Sort by created_at DESC
            all_items.sort(key=lambda x: x.created_at, reverse=True)

            # Apply pagination to aggregated results
            paginated_items = all_items[offset : offset + limit]

            # Calculate pagination
            page = (offset // limit) + 1 if limit > 0 else 1
            has_next = (offset + limit) < total
            has_previous = offset > 0

            return PaginatedReportsResponse(
                items=paginated_items,
                total=total,
                page=page,
                size=len(paginated_items),
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
        200: {"description": "Report details with download URL"},
        401: {"description": "Unauthorized - Invalid or missing token"},
        403: {"description": "Forbidden - Requires web_users group"},
        404: {"description": "Report not found", "model": NotFoundErrorResponse},
    },
)
async def get_report(
    report_id: UUID,
    order_reports: OrderReportsAdapter = Depends(get_order_reports_adapter),
    inventory_reports: InventoryReportsAdapter = Depends(get_inventory_reports_adapter),
    user: Dict = Depends(require_web_user),
):
    """
    Get a single report with download URL.

    Tries Order microservice first, then Inventory microservice.

    Args:
        report_id: Report UUID
        order_reports: Order reports adapter (injected)
        inventory_reports: Inventory reports adapter (injected)
        user: Authenticated user (from JWT)

    Returns:
        ReportResponse with report details and download URL
    """
    user_id = UUID(user["sub"])
    logger.info(f"Getting report {report_id} for user {user_id}")

    try:
        # Try Order microservice first
        try:
            response = await order_reports.get_report(user_id=user_id, report_id=report_id)
            return response
        except MicroserviceHTTPError as e:
            # If 404, try Inventory; otherwise raise
            if e.status_code != 404:
                raise
            # Not found in Order, try Inventory
            pass

        # Try Inventory microservice
        try:
            response = await inventory_reports.get_report(
                user_id=user_id, report_id=report_id
            )
            return response
        except MicroserviceHTTPError as e:
            # If 404, report not found in either service
            if e.status_code == 404:
                raise HTTPException(status_code=404, detail="Report not found")
            # For other errors, let it bubble up
            raise

    except HTTPException:
        raise
    except MicroserviceError as e:
        logger.error(f"Microservice error getting report: {e}")
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error getting report {report_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
