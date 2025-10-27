"""Report repository implementation."""

import logging
from datetime import datetime
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.ports.report_repository import ReportRepository as ReportRepositoryPort
from src.domain.entities import Report as ReportEntity
from src.domain.value_objects import ReportStatus, ReportType
from src.infrastructure.database.models import Report as ReportModel

logger = logging.getLogger(__name__)


class ReportRepository(ReportRepositoryPort):
    """
    SQLAlchemy implementation of ReportRepository port.

    Handles translation between Report domain entities and database models.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, report: ReportEntity) -> ReportEntity:
        """
        Save a report entity (converts to ORM model).

        Args:
            report: Domain report entity

        Returns:
            Saved report entity
        """
        logger.debug(f"Saving report {report.id} for user {report.user_id}")

        # Convert domain entity to ORM model
        report_model = ReportModel(
            id=report.id,
            report_type=report.report_type.value,
            status=report.status.value,
            user_id=report.user_id,
            start_date=report.start_date,
            end_date=report.end_date,
            filters=report.filters,
            s3_bucket=report.s3_bucket,
            s3_key=report.s3_key,
            error_message=report.error_message,
            created_at=report.created_at,
            completed_at=report.completed_at,
        )

        self.session.add(report_model)
        await self.session.flush()

        logger.info(f"Report {report.id} saved successfully")
        return report

    async def find_by_id(self, report_id: UUID) -> Optional[ReportEntity]:
        """
        Find a report by ID.

        Args:
            report_id: The report UUID

        Returns:
            The report entity if found, None otherwise
        """
        logger.debug(f"Finding report {report_id}")

        stmt = select(ReportModel).where(ReportModel.id == report_id)
        result = await self.session.execute(stmt)
        report_model = result.scalar_one_or_none()

        if not report_model:
            logger.debug(f"Report {report_id} not found")
            return None

        return self._model_to_entity(report_model)

    async def find_by_user(
        self,
        user_id: UUID,
        limit: int = 10,
        offset: int = 0,
        status: Optional[ReportStatus] = None,
        report_type: Optional[ReportType] = None,
    ) -> Tuple[List[ReportEntity], int]:
        """
        Find reports for a specific user with pagination and filters.

        Args:
            user_id: The user UUID
            limit: Maximum number of reports to return
            offset: Number of reports to skip
            status: Optional status filter
            report_type: Optional report type filter

        Returns:
            Tuple of (list of reports, total count)
        """
        logger.debug(
            f"Finding reports for user {user_id} (limit={limit}, offset={offset}, "
            f"status={status}, type={report_type})"
        )

        # Build filters
        filters = [ReportModel.user_id == user_id]

        if status:
            filters.append(ReportModel.status == status.value)

        if report_type:
            filters.append(ReportModel.report_type == report_type.value)

        # Count query
        count_stmt = select(func.count()).select_from(ReportModel).where(and_(*filters))
        count_result = await self.session.execute(count_stmt)
        total = count_result.scalar()

        # Data query (ordered by created_at DESC)
        data_stmt = (
            select(ReportModel)
            .where(and_(*filters))
            .order_by(ReportModel.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        data_result = await self.session.execute(data_stmt)
        report_models = data_result.scalars().all()

        reports = [self._model_to_entity(model) for model in report_models]

        logger.info(f"Found {len(reports)} reports for user {user_id} (total: {total})")
        return reports, total

    async def update_status(
        self,
        report_id: UUID,
        status: ReportStatus,
        s3_bucket: Optional[str] = None,
        s3_key: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> None:
        """
        Update report status and related fields.

        Args:
            report_id: The report UUID
            status: New status
            s3_bucket: S3 bucket (for completed reports)
            s3_key: S3 key (for completed reports)
            error_message: Error message (for failed reports)
        """
        logger.debug(f"Updating report {report_id} status to {status}")

        stmt = select(ReportModel).where(ReportModel.id == report_id)
        result = await self.session.execute(stmt)
        report_model = result.scalar_one_or_none()

        if not report_model:
            raise ValueError(f"Report {report_id} not found")

        report_model.status = status.value

        if status == ReportStatus.COMPLETED:
            report_model.s3_bucket = s3_bucket
            report_model.s3_key = s3_key
            report_model.completed_at = datetime.utcnow()
        elif status == ReportStatus.FAILED:
            report_model.error_message = error_message
            report_model.completed_at = datetime.utcnow()

        await self.session.flush()

        logger.info(f"Report {report_id} status updated to {status}")

    def _model_to_entity(self, model: ReportModel) -> ReportEntity:
        """
        Convert ORM model to domain entity.

        Args:
            model: Report ORM model

        Returns:
            Report domain entity
        """
        return ReportEntity(
            id=model.id,
            report_type=ReportType(model.report_type),
            status=ReportStatus(model.status),
            user_id=model.user_id,
            start_date=model.start_date,
            end_date=model.end_date,
            filters=model.filters,
            s3_bucket=model.s3_bucket,
            s3_key=model.s3_key,
            error_message=model.error_message,
            created_at=model.created_at,
            completed_at=model.completed_at,
        )
