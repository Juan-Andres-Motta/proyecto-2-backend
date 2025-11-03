"""HTTP adapter for visit operations (BFF → Seller Service)."""
import logging
from datetime import datetime
from uuid import UUID

from common.http_client import HttpClient
from sellers_app.ports.visit_port import VisitPort
from sellers_app.schemas.visit_schemas import (
    CreateVisitRequestBFF,
    UpdateVisitStatusRequestBFF,
    GenerateEvidenceUploadURLRequestBFF,
    ConfirmEvidenceUploadRequestBFF,
    VisitResponseBFF,
    PreSignedUploadURLResponseBFF,
    ListVisitsResponseBFF,
)

logger = logging.getLogger(__name__)


class VisitAdapter(VisitPort):
    """HTTP client adapter for visit operations via Seller Service."""

    def __init__(self, http_client: HttpClient):
        """Initialize adapter with HTTP client.

        Args:
            http_client: Configured HTTP client for the seller service
        """
        self.client = http_client

    async def create_visit(
        self,
        seller_id: UUID,
        request: CreateVisitRequestBFF,
        client_nombre_institucion: str,
        client_direccion: str,
        client_ciudad: str,
        client_pais: str,
    ) -> VisitResponseBFF:
        """Create a new visit via Seller Service.

        Args:
            seller_id: ID of authenticated seller
            request: Visit creation request
            client_nombre_institucion: Client institution name (denormalized)
            client_direccion: Client address (denormalized)
            client_ciudad: Client city (denormalized)
            client_pais: Client country (denormalized)

        Returns:
            Created visit response
        """
        payload = {
            "seller_id": str(seller_id),
            "client_id": str(request.client_id),
            "fecha_visita": request.fecha_visita.isoformat(),
            "notas_visita": request.notas_visita,
            "client_nombre_institucion": client_nombre_institucion,
            "client_direccion": client_direccion,
            "client_ciudad": client_ciudad,
            "client_pais": client_pais,
        }

        logger.info(f"Creating visit for seller {seller_id} to client {client_nombre_institucion}")
        response_data = await self.client.post("/seller/visits", json=payload)
        return VisitResponseBFF(**response_data)

    async def update_visit_status(
        self, visit_id: UUID, seller_id: UUID, request: UpdateVisitStatusRequestBFF
    ) -> VisitResponseBFF:
        """Update visit status via Seller Service.

        Args:
            visit_id: ID of visit to update
            seller_id: ID of authenticated seller
            request: Status update request

        Returns:
            Updated visit response
        """
        payload = {
            "status": request.status,
            "recomendaciones": request.recomendaciones,
        }

        logger.info(f"Updating visit {visit_id} status for seller {seller_id}")
        response_data = await self.client.patch(
            f"/seller/visits/{visit_id}/status", json=payload
        )
        return VisitResponseBFF(**response_data)

    async def list_visits(
        self, seller_id: UUID, date: datetime
    ) -> ListVisitsResponseBFF:
        """List visits for a specific date via Seller Service.

        Args:
            seller_id: ID of authenticated seller
            date: Date to query

        Returns:
            List of visits response
        """
        params = {
            "seller_id": str(seller_id),
            "date": date.isoformat(),
        }

        logger.info(f"Listing visits for seller {seller_id} on {date.date()}")
        response_data = await self.client.get("/seller/visits", params=params)
        return ListVisitsResponseBFF(**response_data)

    async def generate_evidence_upload_url(
        self, visit_id: UUID, seller_id: UUID, request: GenerateEvidenceUploadURLRequestBFF
    ) -> PreSignedUploadURLResponseBFF:
        """Generate S3 pre-signed upload URL via Seller Service.

        Args:
            visit_id: ID of visit
            seller_id: ID of authenticated seller
            request: Upload URL generation request

        Returns:
            Pre-signed upload URL response
        """
        payload = {
            "filename": request.filename,
            "content_type": request.content_type,
        }

        logger.info(f"Generating evidence upload URL for visit {visit_id}")
        response_data = await self.client.post(
            f"/seller/visits/{visit_id}/evidence/upload-url", json=payload
        )
        return PreSignedUploadURLResponseBFF(**response_data)

    async def confirm_evidence_upload(
        self, visit_id: UUID, seller_id: UUID, request: ConfirmEvidenceUploadRequestBFF
    ) -> VisitResponseBFF:
        """Confirm evidence upload via Seller Service.

        Args:
            visit_id: ID of visit
            seller_id: ID of authenticated seller
            request: Upload confirmation request

        Returns:
            Updated visit response
        """
        payload = {"s3_url": request.s3_url}

        logger.info(f"Confirming evidence upload for visit {visit_id}")
        response_data = await self.client.post(
            f"/seller/visits/{visit_id}/evidence/confirm", json=payload
        )
        return VisitResponseBFF(**response_data)
