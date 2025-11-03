"""Create Visit Saga - Orchestrates client assignment and visit creation."""
import logging
from datetime import datetime
from typing import Optional
from uuid import UUID

from sellers_app.adapters.client_adapter import ClientAdapter
from sellers_app.adapters.visit_adapter import VisitAdapter
from sellers_app.schemas.visit_schemas import CreateVisitRequestBFF, VisitResponseBFF

logger = logging.getLogger(__name__)


class ClientAssignedToOtherSellerError(Exception):
    """Raised when client is assigned to a different seller."""
    def __init__(self, client_id: UUID, client_name: str, assigned_seller_id: UUID):
        self.client_id = client_id
        self.client_name = client_name
        self.assigned_seller_id = assigned_seller_id
        super().__init__(
            f"Client {client_name} ({client_id}) is already assigned to seller {assigned_seller_id}"
        )


class ClientNotFoundError(Exception):
    """Raised when client is not found."""
    def __init__(self, client_id: UUID):
        self.client_id = client_id
        super().__init__(f"Client {client_id} not found")


class CreateVisitSaga:
    """Saga for creating visit with client assignment orchestration.

    Business flow (BFF orchestrates):
    1. Fetch client details from Client Service
    2. Check client assignment:
       - If unassigned: Assign current seller via Client Service
       - If assigned to current seller: Continue
       - If assigned to different seller: Abort (403)
    3. Create visit via Seller Service (which validates time constraints)

    This is a Saga pattern implementation that ensures atomicity across
    client assignment and visit creation operations.
    """

    def __init__(
        self,
        client_adapter: ClientAdapter,
        visit_adapter: VisitAdapter,
    ):
        """Initialize the saga with required adapters.

        Args:
            client_adapter: Adapter for client service operations
            visit_adapter: Adapter for visit service operations
        """
        self.client_adapter = client_adapter
        self.visit_adapter = visit_adapter

    async def execute(
        self,
        seller_id: UUID,
        request: CreateVisitRequestBFF,
    ) -> VisitResponseBFF:
        """Execute the create visit saga.

        Args:
            seller_id: UUID of the seller creating the visit
            request: Visit creation request with client_id, fecha_visita, notas_visita

        Returns:
            Created Visit response from Seller Service

        Raises:
            ClientNotFoundError: If client not found
            ClientAssignedToOtherSellerError: If client assigned to different seller
            Other exceptions from downstream services
        """
        logger.info(
            f"BFF Saga: Starting CreateVisitSaga: seller_id={seller_id}, "
            f"client_id={request.client_id}, fecha_visita={request.fecha_visita}"
        )

        # Step 1: Fetch client details from Client Service
        logger.debug(f"BFF Saga Step 1: Fetching client: client_id={request.client_id}")

        try:
            client = await self.client_adapter.get_client_by_id(request.client_id)
        except Exception as e:
            logger.error(f"BFF Saga: Client not found or error fetching: client_id={request.client_id}, error={e}")
            raise ClientNotFoundError(request.client_id)

        # Step 2: Handle client assignment
        assigned_seller_id = client.vendedor_asignado_id

        if assigned_seller_id is None:
            # Client unassigned - auto-assign to current seller
            logger.info(
                f"BFF Saga Step 2a: Client {request.client_id} unassigned. "
                f"Auto-assigning to seller {seller_id}"
            )
            try:
                await self.client_adapter.assign_seller(request.client_id, seller_id)
                logger.info(
                    f"BFF Saga: Successfully assigned seller {seller_id} to client {request.client_id}"
                )
            except Exception as e:
                logger.error(
                    f"BFF Saga: Client assignment failed: client_id={request.client_id}, "
                    f"seller_id={seller_id}, error={e}"
                )
                raise  # Re-raise to abort saga

        elif assigned_seller_id != seller_id:
            # Client assigned to different seller - abort
            logger.warning(
                f"BFF Saga: Client {request.client_id} assigned to different seller: "
                f"assigned={assigned_seller_id}, requesting={seller_id}"
            )
            raise ClientAssignedToOtherSellerError(
                client_id=request.client_id,
                client_name=client.nombre_institucion,
                assigned_seller_id=assigned_seller_id,
            )
        else:
            logger.debug(
                f"BFF Saga Step 2b: Client {request.client_id} already assigned to seller {seller_id}"
            )

        # Step 3: Create visit via Seller Service
        # The Seller Service will handle:
        # - Business rule validation (future date, time conflicts)
        # - Persistence with denormalized client data
        logger.debug("BFF Saga Step 3: Creating visit via Seller Service")

        created_visit = await self.visit_adapter.create_visit(
            seller_id=seller_id,
            request=request,
            client_nombre_institucion=client.nombre_institucion,
            client_direccion=client.direccion,
            client_ciudad=client.ciudad,
            client_pais=client.pais,
        )

        logger.info(
            f"BFF Saga: Visit created successfully: visit_id={created_visit.id}, "
            f"seller_id={seller_id}, client={client.nombre_institucion}"
        )

        return created_visit
