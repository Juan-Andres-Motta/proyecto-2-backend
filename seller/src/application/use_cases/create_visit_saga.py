"""Create Visit Saga - Orchestrates client assignment and visit creation."""
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.application.ports.client_service_port import ClientServicePort
from src.application.ports.visit_repository_port import VisitRepositoryPort
from src.domain.entities.visit import Visit, VisitStatus
from src.domain.exceptions import (
    ClientAssignedToOtherSellerError,
    VisitNotFoundError,
    VisitTimeConflictError,
)
from src.domain.validation import VisitValidationRules

logger = logging.getLogger(__name__)


class CreateVisitSaga:
    """Saga for creating visit with client assignment orchestration.

    Business flow:
    1. Fetch client details
    2. Check client assignment:
       - If unassigned: Assign current seller
       - If assigned to current seller: Continue
       - If assigned to different seller: Abort (403)
    3. Validate time constraints (future date, 180-minute gap)
    4. Create visit with denormalized client data

    This is a Saga pattern implementation that ensures atomicity across
    client assignment and visit creation operations.
    """

    def __init__(
        self,
        visit_repository: VisitRepositoryPort,
        client_service: ClientServicePort,
    ):
        """Initialize the saga with required dependencies.

        Args:
            visit_repository: Repository for visit persistence operations
            client_service: Service for client-related operations
        """
        self.visit_repository = visit_repository
        self.client_service = client_service

    async def execute(
        self,
        seller_id: UUID,
        client_id: UUID,
        fecha_visita: datetime,
        notas_visita: Optional[str],
        session: AsyncSession,
    ) -> Visit:
        """Execute the create visit saga.

        Args:
            seller_id: UUID of the seller creating the visit
            client_id: UUID of the client to visit
            fecha_visita: Scheduled visit datetime (timezone-aware)
            notas_visita: Optional notes for the visit
            session: Database session

        Returns:
            Created Visit domain entity

        Raises:
            VisitNotFoundError: If client not found
            ClientAssignedToOtherSellerError: If client assigned to different seller
            InvalidVisitDateError: If date not in future
            VisitTimeConflictError: If conflicts with another visit
        """
        logger.info(
            f"Starting CreateVisitSaga: seller_id={seller_id}, "
            f"client_id={client_id}, fecha_visita={fecha_visita}"
        )

        # Step 1: Fetch client details
        logger.debug(f"Fetching client: client_id={client_id}")
        client = await self.client_service.get_client(client_id)

        if not client:
            logger.error(f"Client not found: client_id={client_id}")
            raise VisitNotFoundError(client_id)

        # Step 2: Handle client assignment
        if client.vendedor_asignado_id is None:
            # Client unassigned - auto-assign to current seller
            logger.info(
                f"Client {client_id} unassigned. Auto-assigning to seller {seller_id}"
            )
            try:
                await self.client_service.assign_seller(client_id, seller_id)
                logger.info(f"Successfully assigned seller {seller_id} to client {client_id}")
            except Exception as e:
                logger.error(
                    f"Client assignment failed: client_id={client_id}, "
                    f"seller_id={seller_id}, error={e}"
                )
                raise  # Re-raise to abort saga

        elif client.vendedor_asignado_id != seller_id:
            # Client assigned to different seller - abort
            logger.warning(
                f"Client {client_id} assigned to different seller: "
                f"assigned={client.vendedor_asignado_id}, requesting={seller_id}"
            )
            raise ClientAssignedToOtherSellerError(
                client_id=client_id,
                client_nombre=client.nombre_institucion,
                assigned_seller_id=client.vendedor_asignado_id,
            )

        # Step 3: Validate business rules
        logger.debug("Validating business rules")

        # 3a. Validate future date (at least 1 day ahead)
        VisitValidationRules.validate_future_date(fecha_visita)

        # 3b. Check for time conflicts (180-minute gap)
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

        # Step 4: Create visit entity with denormalized client data
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
            # Denormalized client data (snapshot at creation time)
            client_nombre_institucion=client.nombre_institucion,
            client_direccion=client.direccion,
            client_ciudad=client.ciudad,
            client_pais=client.pais,
            created_at=now,
            updated_at=now,
        )

        # Step 5: Persist to database
        logger.debug(f"Saving visit to database: visit_id={visit.id}")
        created_visit = await self.visit_repository.create(visit, session)

        logger.info(
            f"Visit created successfully: visit_id={created_visit.id}, "
            f"seller_id={seller_id}, client={client.nombre_institucion}"
        )

        return created_visit
