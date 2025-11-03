"""Create Visit Use Case - Simple validation and persistence (no orchestration)."""
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.application.ports.visit_repository_port import VisitRepositoryPort
from src.domain.entities.visit import Visit, VisitStatus
from src.domain.exceptions import VisitTimeConflictError
from src.domain.validation import VisitValidationRules

logger = logging.getLogger(__name__)


class CreateVisitUseCase:
    """Use case for creating a visit (simple validation and persistence).

    Business flow:
    1. Validate time constraints (future date, 180-minute gap)
    2. Create visit with denormalized client data (provided by BFF)
    3. Persist to database

    Note: This use case does NOT orchestrate with other services.
    Client assignment and validation is handled by the BFF saga.
    """

    def __init__(self, visit_repository: VisitRepositoryPort):
        """Initialize the use case.

        Args:
            visit_repository: Repository for visit persistence operations
        """
        self.visit_repository = visit_repository

    async def execute(
        self,
        seller_id: UUID,
        client_id: UUID,
        fecha_visita: datetime,
        notas_visita: Optional[str],
        client_nombre_institucion: str,
        client_direccion: str,
        client_ciudad: str,
        client_pais: str,
        session: AsyncSession,
    ) -> Visit:
        """Execute the create visit use case.

        Args:
            seller_id: UUID of the seller creating the visit
            client_id: UUID of the client to visit
            fecha_visita: Scheduled visit datetime (timezone-aware)
            notas_visita: Optional notes for the visit
            client_nombre_institucion: Client institution name (denormalized)
            client_direccion: Client address (denormalized)
            client_ciudad: Client city (denormalized)
            client_pais: Client country (denormalized)
            session: Database session

        Returns:
            Created Visit domain entity

        Raises:
            InvalidVisitDateError: If date not in future
            VisitTimeConflictError: If conflicts with another visit
        """
        logger.info(
            f"Creating visit: seller_id={seller_id}, "
            f"client_id={client_id}, fecha_visita={fecha_visita}"
        )

        # Step 1: Validate business rules
        logger.debug("Validating business rules")

        # 1a. Validate future date (at least 1 day ahead)
        VisitValidationRules.validate_future_date(fecha_visita)

        # 1b. Check for time conflicts (180-minute gap)
        conflicting_visit = await self.visit_repository.has_conflicting_visit(
            seller_id=seller_id,
            fecha_visita=fecha_visita,
            session=session,
        )

        if conflicting_visit:
            logger.warning(
                f"Visit time conflict: requested={fecha_visita}, "
                f"conflict_id={conflicting_visit.id}, "
                f"conflict_time={conflicting_visit.fecha_visita}"
            )
            raise VisitTimeConflictError(
                requested_time=fecha_visita,
                conflicting_visit=conflicting_visit,
            )

        # Step 2: Create visit entity with denormalized client data
        logger.debug("Creating visit entity")
        now = datetime.now(timezone.utc)

        visit = Visit(
            id=uuid.uuid4(),
            seller_id=seller_id,
            client_id=client_id,
            fecha_visita=fecha_visita,
            status=VisitStatus.PROGRAMADA,
            notas_visita=notas_visita,
            recomendaciones=None,
            archivos_evidencia=None,
            # Denormalized client data (provided by BFF)
            client_nombre_institucion=client_nombre_institucion,
            client_direccion=client_direccion,
            client_ciudad=client_ciudad,
            client_pais=client_pais,
            created_at=now,
            updated_at=now,
        )

        # Step 3: Persist to database
        logger.debug(f"Saving visit to database: visit_id={visit.id}")
        created_visit = await self.visit_repository.create(visit, session)

        logger.info(
            f"Visit created successfully: visit_id={created_visit.id}, "
            f"seller_id={seller_id}, client={client_nombre_institucion}"
        )

        return created_visit
