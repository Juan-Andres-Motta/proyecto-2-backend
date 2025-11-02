"""Port for visit operations (BFF → Seller Service)."""
from abc import ABC, abstractmethod
from datetime import datetime
from uuid import UUID

from sellers_app.schemas.visit_schemas import (
    CreateVisitRequestBFF,
    UpdateVisitStatusRequestBFF,
    GenerateEvidenceUploadURLRequestBFF,
    ConfirmEvidenceUploadRequestBFF,
    VisitResponseBFF,
    PreSignedUploadURLResponseBFF,
    ListVisitsResponseBFF,
)


class VisitPort(ABC):
    """Abstract port for visit operations."""

    @abstractmethod
    async def create_visit(
        self,
        seller_id: UUID,
        request: CreateVisitRequestBFF,
        client_nombre_institucion: str,
        client_direccion: str,
        client_ciudad: str,
        client_pais: str,
    ) -> VisitResponseBFF:
        """Create a new visit with denormalized client data."""
        pass  # pragma: no cover

    @abstractmethod
    async def update_visit_status(
        self, visit_id: UUID, seller_id: UUID, request: UpdateVisitStatusRequestBFF
    ) -> VisitResponseBFF:
        """Update visit status."""
        pass  # pragma: no cover

    @abstractmethod
    async def list_visits(
        self, seller_id: UUID, date: datetime
    ) -> ListVisitsResponseBFF:
        """List visits for a specific date."""
        pass  # pragma: no cover

    @abstractmethod
    async def generate_evidence_upload_url(
        self, visit_id: UUID, seller_id: UUID, request: GenerateEvidenceUploadURLRequestBFF
    ) -> PreSignedUploadURLResponseBFF:
        """Generate S3 pre-signed upload URL."""
        pass  # pragma: no cover

    @abstractmethod
    async def confirm_evidence_upload(
        self, visit_id: UUID, seller_id: UUID, request: ConfirmEvidenceUploadRequestBFF
    ) -> VisitResponseBFF:
        """Confirm evidence upload."""
        pass  # pragma: no cover
