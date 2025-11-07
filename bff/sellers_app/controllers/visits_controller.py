"""FastAPI controller for visit endpoints in BFF (sellers app)."""
import logging
from datetime import datetime
from typing import Dict
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from common.auth.dependencies import require_seller_user
from sellers_app.ports.visit_port import VisitPort
from sellers_app.ports.seller_port import SellerPort
from sellers_app.ports.client_port import ClientPort
from sellers_app.schemas.visit_schemas import (
    CreateVisitRequestBFF,
    UpdateVisitStatusRequestBFF,
    GenerateEvidenceUploadURLRequestBFF,
    ConfirmEvidenceUploadRequestBFF,
    VisitResponseBFF,
    PreSignedUploadURLResponseBFF,
    ListVisitsResponseBFF,
)
from sellers_app.sagas.create_visit_saga import CreateVisitSaga, ClientAssignedToOtherSellerError, ClientNotFoundError
from dependencies import get_visit_port, get_seller_app_seller_port, get_seller_client_port

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/visits")


# ========== Endpoints ==========


@router.post(
    "",
    response_model=VisitResponseBFF,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new visit",
    description="Creates a new visit for the authenticated seller. "
    "Automatically assigns unassigned clients to the seller. "
    "Validates future date (≥1 day ahead) and 180-minute gap between visits.",
)
async def create_visit(
    request: CreateVisitRequestBFF,
    visit_port: VisitPort = Depends(get_visit_port),
    seller_port: SellerPort = Depends(get_seller_app_seller_port),
    client_port: ClientPort = Depends(get_seller_client_port),
    user: Dict = Depends(require_seller_user),
):
    """Create a new visit using saga orchestration."""
    try:
        # Get cognito_user_id from JWT sub claim
        cognito_user_id = user.get("sub")
        if not cognito_user_id:
            raise HTTPException(status_code=401, detail="Invalid token: missing sub claim")

        # Look up seller by cognito_user_id to get seller_id
        seller = await seller_port.get_seller_by_cognito_user_id(cognito_user_id)
        seller_id = UUID(seller["id"])  # Convert to UUID for proper comparison in saga

        logger.info(f"BFF: Creating visit for seller {seller_id} via saga")

        # Initialize saga with adapters
        from sellers_app.adapters.client_adapter import ClientAdapter
        from sellers_app.adapters.visit_adapter import VisitAdapter

        saga = CreateVisitSaga(
            client_adapter=client_port,
            visit_adapter=visit_port,
        )

        # Execute saga
        return await saga.execute(seller_id=seller_id, request=request)

    except ClientNotFoundError as e:
        logger.error(f"BFF: Client not found: {e}")
        raise HTTPException(status_code=404, detail=str(e))

    except ClientAssignedToOtherSellerError as e:
        logger.error(f"BFF: Client already assigned: {e}")
        raise HTTPException(
            status_code=403,
            detail={
                "error": "ClientAlreadyAssigned",
                "message": str(e),
                "client_id": str(e.client_id),
                "assigned_seller_id": str(e.assigned_seller_id),
            }
        )

    except Exception as e:
        logger.error(f"BFF: Error creating visit: {e}")
        raise


@router.patch(
    "/{visit_id}/status",
    response_model=VisitResponseBFF,
    summary="Update visit status",
    description="Updates visit status and optional product recommendations. "
    "Only allows programada → completada/cancelada transitions.",
)
async def update_visit_status(
    visit_id: UUID,
    request: UpdateVisitStatusRequestBFF,
    visit_port: VisitPort = Depends(get_visit_port),
    seller_port: SellerPort = Depends(get_seller_app_seller_port),
    user: Dict = Depends(require_seller_user),
):
    """Update visit status."""
    try:
        cognito_user_id = user.get("sub")
        if not cognito_user_id:
            raise HTTPException(status_code=401, detail="Invalid token: missing sub claim")

        seller = await seller_port.get_seller_by_cognito_user_id(cognito_user_id)
        seller_id = UUID(seller["id"])  # Convert to UUID for consistency

        logger.info(f"BFF: Updating status for visit {visit_id}")
        return await visit_port.update_visit_status(
            visit_id=visit_id, seller_id=seller_id, request=request
        )

    except Exception as e:
        logger.error(f"BFF: Error updating visit status: {e}")
        raise


@router.get(
    "",
    response_model=ListVisitsResponseBFF,
    summary="List visits for a date",
    description="Retrieves all visits for the authenticated seller on a specific date, "
    "ordered chronologically by fecha_visita.",
)
async def list_visits(
    date: datetime,
    visit_port: VisitPort = Depends(get_visit_port),
    seller_port: SellerPort = Depends(get_seller_app_seller_port),
    user: Dict = Depends(require_seller_user),
):
    """List visits for a specific date."""
    try:
        cognito_user_id = user.get("sub")
        if not cognito_user_id:
            raise HTTPException(status_code=401, detail="Invalid token: missing sub claim")

        seller = await seller_port.get_seller_by_cognito_user_id(cognito_user_id)
        seller_id = UUID(seller["id"])  # Convert to UUID for consistency

        logger.info(f"BFF: Listing visits for seller {seller_id} on {date.date()}")
        return await visit_port.list_visits(seller_id=seller_id, date=date)

    except Exception as e:
        logger.error(f"BFF: Error listing visits: {e}")
        raise


@router.post(
    "/{visit_id}/evidence/upload-url",
    response_model=PreSignedUploadURLResponseBFF,
    summary="Generate S3 pre-signed upload URL",
    description="Generates a pre-signed POST URL for direct browser-to-S3 evidence upload. "
    "URL expires in 1 hour. Max file size: 50MB. "
    "Allowed types: image/jpeg, image/png, image/heic, video/mp4, video/quicktime.",
)
async def generate_evidence_upload_url(
    visit_id: UUID,
    request: GenerateEvidenceUploadURLRequestBFF,
    visit_port: VisitPort = Depends(get_visit_port),
    seller_port: SellerPort = Depends(get_seller_app_seller_port),
    user: Dict = Depends(require_seller_user),
):
    """Generate S3 pre-signed upload URL for evidence."""
    try:
        cognito_user_id = user.get("sub")
        if not cognito_user_id:
            raise HTTPException(status_code=401, detail="Invalid token: missing sub claim")

        seller = await seller_port.get_seller_by_cognito_user_id(cognito_user_id)
        seller_id = UUID(seller["id"])  # Convert to UUID for consistency

        logger.info(f"BFF: Generating upload URL for visit {visit_id}")
        return await visit_port.generate_evidence_upload_url(
            visit_id=visit_id, seller_id=seller_id, request=request
        )

    except Exception as e:
        logger.error(f"BFF: Error generating upload URL: {e}")
        raise


@router.post(
    "/{visit_id}/evidence/confirm",
    response_model=VisitResponseBFF,
    summary="Confirm evidence upload",
    description="Saves the S3 URL to the visit record after successful upload.",
)
async def confirm_evidence_upload(
    visit_id: UUID,
    request: ConfirmEvidenceUploadRequestBFF,
    visit_port: VisitPort = Depends(get_visit_port),
    seller_port: SellerPort = Depends(get_seller_app_seller_port),
    user: Dict = Depends(require_seller_user),
):
    """Confirm evidence upload and save S3 URL."""
    try:
        cognito_user_id = user.get("sub")
        if not cognito_user_id:
            raise HTTPException(status_code=401, detail="Invalid token: missing sub claim")

        seller = await seller_port.get_seller_by_cognito_user_id(cognito_user_id)
        seller_id = UUID(seller["id"])  # Convert to UUID for consistency

        logger.info(f"BFF: Confirming evidence upload for visit {visit_id}")
        return await visit_port.confirm_evidence_upload(
            visit_id=visit_id, seller_id=seller_id, request=request
        )

    except Exception as e:
        logger.error(f"BFF: Error confirming evidence upload: {e}")
        raise
