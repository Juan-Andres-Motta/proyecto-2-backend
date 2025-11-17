"""Visit repository implementation for PostgreSQL."""
import logging
from datetime import date, datetime, timedelta
from typing import List, Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.ports.visit_repository_port import VisitRepositoryPort
from src.domain.entities.visit import Visit as DomainVisit
from src.domain.entities.visit import VisitStatus
from src.infrastructure.database.models import Visit as ORMVisit

logger = logging.getLogger(__name__)


class VisitRepository(VisitRepositoryPort):
    """Implementation of VisitRepositoryPort for PostgreSQL."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, visit: DomainVisit, session: AsyncSession) -> DomainVisit:
        """Create a new visit and return domain entity."""
        logger.debug(
            f"DB: Creating visit: seller_id={visit.seller_id}, "
            f"client_id={visit.client_id}, fecha_visita={visit.fecha_visita}"
        )

        try:
            orm_visit = self._to_orm(visit)
            session.add(orm_visit)
            await session.flush()
            await session.refresh(orm_visit)

            logger.debug(
                f"DB: Successfully created visit: id={orm_visit.id}, "
                f"seller_id={orm_visit.seller_id}, status={orm_visit.status}"
            )
            return self._to_domain(orm_visit)
        except Exception as e:
            logger.error(
                f"DB: Create visit failed: seller_id={visit.seller_id}, "
                f"client_id={visit.client_id}, error={e}"
            )
            raise

    async def find_by_id(
        self, visit_id: UUID, session: AsyncSession
    ) -> Optional[DomainVisit]:
        """Find a visit by ID and return domain entity."""
        logger.debug(f"DB: Finding visit by ID: visit_id={visit_id}")

        try:
            stmt = select(ORMVisit).where(ORMVisit.id == visit_id)
            result = await session.execute(stmt)
            orm_visit = result.scalars().first()

            if orm_visit is None:
                logger.debug(f"DB: Visit not found: visit_id={visit_id}")
                return None

            logger.debug(
                f"DB: Successfully found visit: visit_id={visit_id}, "
                f"status={orm_visit.status}, client={orm_visit.client_nombre_institucion}"
            )
            return self._to_domain(orm_visit)
        except Exception as e:
            logger.error(f"DB: Find visit by ID failed: visit_id={visit_id}, error={e}")
            raise

    async def get_visits_by_date(
        self, seller_id: UUID, date: datetime, session: AsyncSession
    ) -> List[DomainVisit]:
        """Get all visits for a seller on a specific date, ordered chronologically."""
        logger.debug(
            f"DB: Getting visits by date: seller_id={seller_id}, date={date.date()}"
        )

        try:
            stmt = (
                select(ORMVisit)
                .where(
                    ORMVisit.seller_id == seller_id,
                    func.date(ORMVisit.fecha_visita) == date.date(),
                )
                .order_by(ORMVisit.fecha_visita.asc())  # Chronological order
            )
            result = await session.execute(stmt)
            orm_visits = result.scalars().all()

            logger.debug(
                f"DB: Successfully retrieved visits: seller_id={seller_id}, "
                f"date={date.date()}, count={len(orm_visits)}"
            )
            return [self._to_domain(orm_visit) for orm_visit in orm_visits]
        except Exception as e:
            logger.error(
                f"DB: Get visits by date failed: seller_id={seller_id}, "
                f"date={date.date()}, error={e}"
            )
            raise

    async def has_conflicting_visit(
        self, seller_id: UUID, fecha_visita: datetime, session: AsyncSession
    ) -> Optional[DomainVisit]:
        """Check if there's a conflicting visit within 180 minutes.

        Business rule: No two visits can be scheduled within 180 minutes.
        Cancelled visits are excluded from conflict check.
        """
        logger.debug(
            f"DB: Checking for conflicting visits: seller_id={seller_id}, "
            f"fecha_visita={fecha_visita}"
        )

        try:
            # Calculate time window: ±180 minutes
            min_time = fecha_visita - timedelta(minutes=180)
            max_time = fecha_visita + timedelta(minutes=180)

            stmt = select(ORMVisit).where(
                ORMVisit.seller_id == seller_id,
                ORMVisit.fecha_visita >= min_time,
                ORMVisit.fecha_visita <= max_time,
                ORMVisit.status != VisitStatus.CANCELADA.value,  # Exclude cancelled
            )
            result = await session.execute(stmt)
            orm_visit = result.scalars().first()

            if orm_visit is None:
                logger.debug(
                    f"DB: No conflicting visits found: seller_id={seller_id}, "
                    f"fecha_visita={fecha_visita}"
                )
                return None

            logger.debug(
                f"DB: Conflicting visit found: seller_id={seller_id}, "
                f"conflict_id={orm_visit.id}, conflict_time={orm_visit.fecha_visita}"
            )
            return self._to_domain(orm_visit)
        except Exception as e:
            logger.error(
                f"DB: Check conflicting visit failed: seller_id={seller_id}, "
                f"fecha_visita={fecha_visita}, error={e}"
            )
            raise

    async def find_by_seller_and_date_range(
        self,
        seller_id: UUID,
        date_from: date | None,
        date_to: date | None,
        page: int,
        page_size: int,
        session: AsyncSession,
        client_name: Optional[str] = None,
    ) -> List[DomainVisit]:
        """Find visits by seller within optional date range with pagination.

        Ordering:
        - If date_to only (PAST): descending by fecha_visita (most recent first)
        - Otherwise (TODAY/FUTURE): ascending by fecha_visita (nearest first)

        Args:
            seller_id: UUID of the seller
            date_from: Start date (inclusive), None for no lower bound
            date_to: End date (inclusive), None for no upper bound
            page: Page number (1-indexed)
            page_size: Number of results per page
            session: Database session

        Returns:
            List of Visit domain entities with applied ordering and pagination
        """
        logger.debug(
            f"DB: Finding visits by date range: seller_id={seller_id}, "
            f"date_from={date_from}, date_to={date_to}, page={page}, page_size={page_size}"
        )

        try:
            # Build query with seller filter
            stmt = select(ORMVisit).where(ORMVisit.seller_id == seller_id)

            # Apply date filters
            if date_from is not None:
                stmt = stmt.where(func.date(ORMVisit.fecha_visita) >= date_from)
            if date_to is not None:
                stmt = stmt.where(func.date(ORMVisit.fecha_visita) <= date_to)

            # Apply client name filter
            if client_name:
                stmt = stmt.where(ORMVisit.client_nombre_institucion.ilike(f"%{client_name}%"))

            # Apply multi-column ordering based on temporal group
            # PAST (date_to only, no date_from): DESC (most recent first)
            # TODAY/FUTURE: ASC (nearest first)
            # Secondary sort by client name (alphabetical), tertiary by ID for stability
            if date_to is not None and date_from is None:
                stmt = stmt.order_by(
                    ORMVisit.fecha_visita.desc(),
                    ORMVisit.client_nombre_institucion.asc(),
                    ORMVisit.id.asc()
                )
            else:
                stmt = stmt.order_by(
                    ORMVisit.fecha_visita.asc(),
                    ORMVisit.client_nombre_institucion.asc(),
                    ORMVisit.id.asc()
                )

            # Apply pagination
            offset = (page - 1) * page_size
            stmt = stmt.limit(page_size).offset(offset)

            # Execute query
            result = await session.execute(stmt)
            orm_visits = result.scalars().all()

            logger.debug(
                f"DB: Successfully retrieved visits: seller_id={seller_id}, "
                f"date_from={date_from}, date_to={date_to}, "
                f"count={len(orm_visits)}, page={page}"
            )
            return [self._to_domain(orm_visit) for orm_visit in orm_visits]
        except Exception as e:
            logger.error(
                f"DB: Find visits by date range failed: seller_id={seller_id}, "
                f"date_from={date_from}, date_to={date_to}, error={e}"
            )
            raise

    async def count_by_seller_and_date_range(
        self,
        seller_id: UUID,
        date_from: date | None,
        date_to: date | None,
        session: AsyncSession,
        client_name: Optional[str] = None,
    ) -> int:
        """Count visits matching seller and date range.

        Args:
            seller_id: UUID of the seller
            date_from: Start date (inclusive), None for no lower bound
            date_to: End date (inclusive), None for no upper bound
            session: Database session

        Returns:
            Total count of matching visits
        """
        logger.debug(
            f"DB: Counting visits by date range: seller_id={seller_id}, "
            f"date_from={date_from}, date_to={date_to}"
        )

        try:
            # Build count query with seller filter
            stmt = select(func.count()).select_from(ORMVisit).where(
                ORMVisit.seller_id == seller_id
            )

            # Apply date filters
            if date_from is not None:
                stmt = stmt.where(func.date(ORMVisit.fecha_visita) >= date_from)
            if date_to is not None:
                stmt = stmt.where(func.date(ORMVisit.fecha_visita) <= date_to)

            # Apply client name filter
            if client_name:
                stmt = stmt.where(ORMVisit.client_nombre_institucion.ilike(f"%{client_name}%"))

            # Execute query
            result = await session.execute(stmt)
            count = result.scalar() or 0

            logger.debug(
                f"DB: Successfully counted visits: seller_id={seller_id}, "
                f"date_from={date_from}, date_to={date_to}, count={count}"
            )
            return count
        except Exception as e:
            logger.error(
                f"DB: Count visits by date range failed: seller_id={seller_id}, "
                f"date_from={date_from}, date_to={date_to}, error={e}"
            )
            raise

    async def update(
        self, visit: DomainVisit, session: AsyncSession
    ) -> DomainVisit:
        """Update an existing visit.

        Args:
            visit: Domain visit entity with updated fields
            session: Database session

        Returns:
            Updated domain visit entity
        """
        logger.debug(f"DB: Updating visit: visit_id={visit.id}")

        try:
            # Fetch the ORM object (tracked by session)
            stmt = select(ORMVisit).where(ORMVisit.id == visit.id)
            result = await session.execute(stmt)
            orm_visit = result.scalars().first()

            if orm_visit is None:
                logger.error(f"DB: Cannot update - visit not found: visit_id={visit.id}")
                raise ValueError(f"Visit {visit.id} not found")

            # Update ORM object fields
            orm_visit.status = visit.status.value
            orm_visit.recomendaciones = visit.recomendaciones
            orm_visit.archivos_evidencia = visit.archivos_evidencia
            orm_visit.notas_visita = visit.notas_visita
            orm_visit.updated_at = visit.updated_at

            # Flush changes to DB
            await session.flush()
            await session.refresh(orm_visit)

            logger.debug(f"DB: Successfully updated visit: visit_id={visit.id}, status={orm_visit.status}")
            return self._to_domain(orm_visit)

        except Exception as e:
            logger.error(f"DB: Update visit failed: visit_id={visit.id}, error={e}")
            raise

    @staticmethod
    def _to_domain(orm_visit: ORMVisit) -> DomainVisit:
        """Map ORM model to domain entity."""
        return DomainVisit(
            id=orm_visit.id,
            seller_id=orm_visit.seller_id,
            client_id=orm_visit.client_id,
            fecha_visita=orm_visit.fecha_visita,
            status=VisitStatus(orm_visit.status),
            notas_visita=orm_visit.notas_visita,
            recomendaciones=orm_visit.recomendaciones,
            archivos_evidencia=orm_visit.archivos_evidencia,
            client_nombre_institucion=orm_visit.client_nombre_institucion,
            client_direccion=orm_visit.client_direccion,
            client_ciudad=orm_visit.client_ciudad,
            client_pais=orm_visit.client_pais,
            created_at=orm_visit.created_at,
            updated_at=orm_visit.updated_at,
        )

    @staticmethod
    def _to_orm(domain_visit: DomainVisit) -> ORMVisit:
        """Map domain entity to ORM model."""
        return ORMVisit(
            id=domain_visit.id,
            seller_id=domain_visit.seller_id,
            client_id=domain_visit.client_id,
            fecha_visita=domain_visit.fecha_visita,
            status=domain_visit.status.value,
            notas_visita=domain_visit.notas_visita,
            recomendaciones=domain_visit.recomendaciones,
            archivos_evidencia=domain_visit.archivos_evidencia,
            client_nombre_institucion=domain_visit.client_nombre_institucion,
            client_direccion=domain_visit.client_direccion,
            client_ciudad=domain_visit.client_ciudad,
            client_pais=domain_visit.client_pais,
            created_at=domain_visit.created_at,
            updated_at=domain_visit.updated_at,
        )
