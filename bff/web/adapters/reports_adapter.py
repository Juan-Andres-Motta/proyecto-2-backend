"""Reports adapter for communicating with microservices."""

import logging
from typing import Any, Dict, Optional
from uuid import UUID

from common.http_client import HttpClient

from ..ports.reports_port import ReportsPort
from ..schemas.report_schemas import (
    PaginatedReportsResponse,
    ReportCreateRequest,
    ReportCreateResponse,
    ReportResponse,
    ReportStatus,
    ReportType,
)

logger = logging.getLogger(__name__)


class OrderReportsAdapter(ReportsPort):
    """Adapter for Order microservice reports."""

    def __init__(self, http_client: HttpClient):
        self.http_client = http_client

    async def create_report(
        self, user_id: UUID, request: ReportCreateRequest
    ) -> ReportCreateResponse:
        """Create a report via Order microservice."""
        logger.info(
            f"Creating report via Order service: type={request.report_type}, user={user_id}"
        )

        payload = {
            "user_id": str(user_id),
            "report_type": request.report_type.value,
            "start_date": request.start_date.isoformat(),
            "end_date": request.end_date.isoformat(),
            "filters": request.filters,
        }

        response = await self.http_client.post(
            "/order/reports", json=payload
        )

        return ReportCreateResponse(**response)

    async def list_reports(
        self,
        user_id: UUID,
        limit: int = 10,
        offset: int = 0,
        status: Optional[ReportStatus] = None,
        report_type: Optional[ReportType] = None,
    ) -> PaginatedReportsResponse:
        """List reports from Order microservice."""
        logger.info(f"Listing reports from Order service for user {user_id}")

        params = {"user_id": str(user_id), "limit": limit, "offset": offset}

        if status:
            params["status"] = status.value
        if report_type:
            params["report_type"] = report_type.value

        response = await self.http_client.get("/order/reports", params=params)

        return PaginatedReportsResponse(**response)

    async def get_report(self, user_id: UUID, report_id: UUID) -> ReportResponse:
        """Get a report from Order microservice."""
        logger.info(f"Getting report {report_id} from Order service")

        response = await self.http_client.get(
            f"/order/reports/{report_id}", params={"user_id": str(user_id)}
        )

        return ReportResponse(**response)


class InventoryReportsAdapter(ReportsPort):
    """Adapter for Inventory microservice reports."""

    def __init__(self, http_client: HttpClient):
        self.http_client = http_client

    async def create_report(
        self, user_id: UUID, request: ReportCreateRequest
    ) -> ReportCreateResponse:
        """Create a report via Inventory microservice."""
        logger.info(
            f"Creating report via Inventory service: type={request.report_type}, user={user_id}"
        )

        payload = {
            "user_id": str(user_id),  # Added user_id to body
            "report_type": request.report_type.value,
            "start_date": request.start_date.isoformat(),
            "end_date": request.end_date.isoformat(),
            "filters": request.filters,
        }

        response = await self.http_client.post(
            "/inventory/reports", json=payload  # Changed to /inventory/reports without query param
        )

        return ReportCreateResponse(**response)

    async def list_reports(
        self,
        user_id: UUID,
        limit: int = 10,
        offset: int = 0,
        status: Optional[ReportStatus] = None,
        report_type: Optional[ReportType] = None,
    ) -> PaginatedReportsResponse:
        """List reports from Inventory microservice."""
        logger.info(f"Listing reports from Inventory service for user {user_id}")

        params = {"user_id": str(user_id), "limit": limit, "offset": offset}

        if status:
            params["status"] = status.value
        if report_type:
            params["report_type"] = report_type.value

        response = await self.http_client.get("/inventory/reports", params=params)

        return PaginatedReportsResponse(**response)

    async def get_report(self, user_id: UUID, report_id: UUID) -> ReportResponse:
        """Get a report from Inventory microservice."""
        logger.info(f"Getting report {report_id} from Inventory service")

        response = await self.http_client.get(
            f"/inventory/reports/{report_id}", params={"user_id": str(user_id)}
        )

        return ReportResponse(**response)
