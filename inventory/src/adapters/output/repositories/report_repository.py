import logging
from datetime import datetime, timezone
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.ports.report_repository_port import ReportRepositoryPort
from src.domain.entities.report import Report as DomainReport
from src.infrastructure.database.models.report import Report as ORMReport

logger = logging.getLogger(__name__)


class ReportRepository(ReportRepositoryPort):
    """Implementation of ReportRepositoryPort for PostgreSQL."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, report_data: dict) -> DomainReport:
        """Create a report and return domain entity."""
        logger.debug(
            f"DB: Creating report with data: report_type={report_data.get('report_type')}, "
            f"user_id={report_data.get('user_id')}"
        )
        try:
            orm_report = ORMReport(**report_data)
            self.session.add(orm_report)
            await self.session.commit()
            await self.session.refresh(orm_report)
            logger.debug(f"DB: Successfully created report: id={orm_report.id}")
            return self._to_domain(orm_report)
        except Exception as e:
            logger.error(f"DB: Create report failed: {e}")
            raise

    async def find_by_id(self, report_id: UUID, user_id: UUID) -> Optional[DomainReport]:
        """Find a report by ID and user_id (authorization) and return domain entity."""
        logger.debug(f"DB: Finding report by id: report_id={report_id}, user_id={user_id}")
        try:
            stmt = select(ORMReport).where(
                ORMReport.id == report_id, ORMReport.user_id == user_id
            )
            result = await self.session.execute(stmt)
            orm_report = result.scalars().first()
            if orm_report is None:
                logger.debug(f"DB: Report not found: report_id={report_id}")
                return None
            logger.debug(f"DB: Successfully found report: id={orm_report.id}")
            return self._to_domain(orm_report)
        except Exception as e:
            logger.error(f"DB: Find report by id failed: {e}")
            raise

    async def list_reports(
        self,
        user_id: UUID,
        limit: int = 10,
        offset: int = 0,
        status: Optional[str] = None,
        report_type: Optional[str] = None,
    ) -> Tuple[List[DomainReport], int]:
        """List reports with pagination and filters, return domain entities."""
        logger.debug(
            f"DB: Listing reports with user_id={user_id}, limit={limit}, offset={offset}, "
            f"status={status}, report_type={report_type}"
        )
        try:
            # Build base query with user_id filter (authorization)
            query = select(ORMReport).where(ORMReport.user_id == user_id)
            count_query = select(func.count()).select_from(ORMReport).where(
                ORMReport.user_id == user_id
            )

            # Apply filters
            if status:
                logger.debug(f"DB: Applying status filter: {status}")
                query = query.where(ORMReport.status == status)
                count_query = count_query.where(ORMReport.status == status)

            if report_type:
                logger.debug(f"DB: Applying report_type filter: {report_type}")
                query = query.where(ORMReport.report_type == report_type)
                count_query = count_query.where(ORMReport.report_type == report_type)

            # Get total count with filters
            count_result = await self.session.execute(count_query)
            total = count_result.scalar()

            # Get paginated data with filters, ordered by created_at DESC
            query = query.order_by(ORMReport.created_at.desc()).limit(limit).offset(offset)
            result = await self.session.execute(query)
            orm_reports = result.scalars().all()

            logger.debug(
                f"DB: Successfully listed reports: count={len(orm_reports)}, total={total}"
            )
            return [self._to_domain(r) for r in orm_reports], total
        except Exception as e:
            logger.error(f"DB: List reports failed: {e}")
            raise

    async def update_status(
        self,
        report_id: UUID,
        status: str,
        s3_bucket: Optional[str] = None,
        s3_key: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> Optional[DomainReport]:
        """Update report status and optional fields."""
        logger.debug(
            f"DB: Updating report status: report_id={report_id}, status={status}, "
            f"s3_bucket={s3_bucket}, s3_key={s3_key}"
        )
        try:
            stmt = select(ORMReport).where(ORMReport.id == report_id)
            result = await self.session.execute(stmt)
            orm_report = result.scalars().first()

            if orm_report is None:
                logger.debug(f"DB: Report not found for update: report_id={report_id}")
                return None

            # Update fields
            orm_report.status = status
            if s3_bucket:
                orm_report.s3_bucket = s3_bucket
            if s3_key:
                orm_report.s3_key = s3_key
            if error_message:
                orm_report.error_message = error_message

            # Set completed_at if status is completed or failed
            if status in ("completed", "failed"):
                orm_report.completed_at = datetime.now(timezone.utc)

            await self.session.commit()
            await self.session.refresh(orm_report)
            logger.debug(f"DB: Successfully updated report: id={orm_report.id}")
            return self._to_domain(orm_report)
        except Exception as e:
            logger.error(f"DB: Update report status failed: {e}")
            raise

    @staticmethod
    def _to_domain(orm_report: ORMReport) -> DomainReport:
        """Map ORM model to domain entity."""
        return DomainReport(
            id=orm_report.id,
            report_type=orm_report.report_type,
            status=orm_report.status,
            user_id=orm_report.user_id,
            start_date=orm_report.start_date,
            end_date=orm_report.end_date,
            filters=orm_report.filters,
            s3_bucket=orm_report.s3_bucket,
            s3_key=orm_report.s3_key,
            error_message=orm_report.error_message,
            created_at=orm_report.created_at,
            completed_at=orm_report.completed_at,
        )
