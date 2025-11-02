"""FastAPI controller for visit endpoints."""
import logging
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.adapters.input.schemas import (
    CreateVisitRequest,
    UpdateVisitStatusRequest,
    GenerateEvidenceUploadURLRequest,
    ConfirmEvidenceUploadRequest,
    VisitResponse,
    PreSignedUploadURLResponse,
    ListVisitsResponse,
)
from src.application.use_cases.create_visit import CreateVisitUseCase
from src.application.use_cases.update_visit_status import UpdateVisitStatusUseCase
from src.application.use_cases.list_visits import ListVisitsUseCase
from src.application.use_cases.generate_evidence_upload_url import (
    GenerateEvidenceUploadURLUseCase,
)
from src.application.use_cases.confirm_evidence_upload import (
    ConfirmEvidenceUploadUseCase,
)
from src.domain.exceptions import (
    VisitNotFoundError,
    InvalidVisitDateError,
    VisitTimeConflictError,
    InvalidStatusTransitionError,
    ClientAssignedToOtherSellerError,
    UnauthorizedVisitAccessError,
)
from src.adapters.output.services.s3_service_adapter import InvalidContentTypeError
from src.adapters.output.services.client_service_adapter import (
    ClientServiceConnectionError,
    ClientAssignmentFailedError,
)
from src.infrastructure.dependencies import (
    get_create_visit_use_case,
    get_update_visit_status_use_case,
    get_list_visits_use_case,
    get_generate_evidence_upload_url_use_case,
    get_confirm_evidence_upload_use_case,
)
from src.infrastructure.database.config import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/visits", tags=["Visits"])


# ========== Endpoints ==========


@router.post(
    "",
    response_model=VisitResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new visit",
    description="Creates a new visit. BFF handles client assignment orchestration. "
    "Validates future date (≥1 day ahead) and 180-minute gap between visits.",
)
async def create_visit(
    request: CreateVisitRequest,
    use_case: CreateVisitUseCase = Depends(get_create_visit_use_case),
    session: AsyncSession = Depends(get_db),
):
    """Create a new visit.

    The seller_id and denormalized client data are provided by the BFF after
    JWT authentication and client assignment orchestration.
    """
    try:
        visit = await use_case.execute(
            seller_id=request.seller_id,
            client_id=request.client_id,
            fecha_visita=request.fecha_visita,
            notas_visita=request.notas_visita,
            client_nombre_institucion=request.client_nombre_institucion,
            client_direccion=request.client_direccion,
            client_ciudad=request.client_ciudad,
            client_pais=request.client_pais,
            session=session,
        )
        await session.commit()
        return VisitResponse.model_validate(visit)

    except InvalidVisitDateError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "InvalidDate",
                "message": str(e),
                "details": {
                    "fecha_visita": e.fecha_visita.isoformat(),
                    "earliest_allowed_date": e.earliest_allowed_date.isoformat(),
                },
            },
        )
    except VisitTimeConflictError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "VisitTimeConflict",
                "message": str(e),
                "details": {
                    "requested_time": e.requested_time.isoformat(),
                    "conflicting_visit_id": str(e.conflicting_visit.id),
                    "conflicting_visit_time": e.conflicting_visit.fecha_visita.isoformat(),
                },
            },
        )
    except ClientAssignedToOtherSellerError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "ClientAssignedToOtherSeller",
                "message": str(e),
                "details": {
                    "client_id": str(e.client_id),
                    "client_nombre": e.client_nombre,
                    "assigned_seller_id": str(e.assigned_seller_id),
                },
            },
        )
    except VisitNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "VisitNotFound",
                "message": str(e),
                "details": {"visit_id": str(e.visit_id)},
            },
        )
    except ClientServiceConnectionError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": "ClientServiceUnavailable",
                "message": str(e),
            },
        )
    except ClientAssignmentFailedError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": "ClientAssignmentFailed",
                "message": str(e),
            },
        )


@router.patch(
    "/{visit_id}/status",
    response_model=VisitResponse,
    summary="Update visit status",
    description="Updates visit status and optional recommendations. "
    "Only allows programada → completada/cancelada transitions.",
)
async def update_visit_status(
    visit_id: UUID,
    request: UpdateVisitStatusRequest,
    use_case: UpdateVisitStatusUseCase = Depends(get_update_visit_status_use_case),
    session: AsyncSession = Depends(get_db),
):
    """Update visit status.

    Authorization is enforced by BFF - microservice trusts that the seller
    can only update their own visits.
    """
    try:
        visit = await use_case.execute(
            visit_id=visit_id,
            new_status=request.status,
            recomendaciones=request.recomendaciones,
            session=session,
        )
        await session.commit()
        return VisitResponse.model_validate(visit)

    except VisitNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "VisitNotFound",
                "message": str(e),
                "details": {"visit_id": str(e.visit_id)},
            },
        )
    except InvalidStatusTransitionError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "InvalidStatusTransition",
                "message": str(e),
                "details": {
                    "current_status": e.current_status,
                    "requested_status": e.requested_status,
                },
            },
        )
    except UnauthorizedVisitAccessError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "UnauthorizedVisitAccess",
                "message": str(e),
                "details": {
                    "visit_id": str(e.visit_id),
                    "seller_id": str(e.seller_id),
                },
            },
        )


@router.get(
    "",
    response_model=ListVisitsResponse,
    summary="List visits for a date",
    description="Retrieves all visits for authenticated seller on specified date, "
    "ordered chronologically.",
)
async def list_visits(
    date: datetime,
    seller_id: UUID = Query(..., description="Seller ID from BFF authentication"),
    use_case: ListVisitsUseCase = Depends(get_list_visits_use_case),
    session: AsyncSession = Depends(get_db),
):
    """List visits for a specific date.

    The seller_id is provided as a query parameter by the BFF after JWT authentication.
    """
    visits = await use_case.execute(seller_id=seller_id, date=date, session=session)

    return ListVisitsResponse(
        visits=[VisitResponse.model_validate(v) for v in visits],
        count=len(visits),
    )


@router.post(
    "/{visit_id}/evidence/upload-url",
    response_model=PreSignedUploadURLResponse,
    summary="Generate S3 pre-signed upload URL",
    description="Generates a pre-signed POST URL for direct browser-to-S3 evidence upload. "
    "URL expires in 1 hour. Max file size: 50MB. Allowed types: JPEG, PNG, HEIC, MP4, MOV.",
)
async def generate_evidence_upload_url(
    visit_id: UUID,
    request: GenerateEvidenceUploadURLRequest,
    use_case: GenerateEvidenceUploadURLUseCase = Depends(
        get_generate_evidence_upload_url_use_case
    ),
    session: AsyncSession = Depends(get_db),
):
    """Generate S3 pre-signed upload URL for evidence.

    Authorization is enforced by BFF - microservice trusts that the seller
    can only upload evidence for their own visits.
    """
    try:
        upload_url = await use_case.execute(
            visit_id=visit_id,
            filename=request.filename,
            content_type=request.content_type,
            session=session,
        )
        return PreSignedUploadURLResponse(
            upload_url=upload_url.upload_url,
            fields=upload_url.fields,
            s3_url=upload_url.s3_url,
            expires_at=upload_url.expires_at,
        )

    except VisitNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "VisitNotFound",
                "message": str(e),
                "details": {"visit_id": str(e.visit_id)},
            },
        )
    except InvalidContentTypeError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error": "InvalidContentType",
                "message": str(e),
                "details": {"content_type": request.content_type},
            },
        )
    except UnauthorizedVisitAccessError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "UnauthorizedVisitAccess",
                "message": str(e),
                "details": {
                    "visit_id": str(e.visit_id),
                    "seller_id": str(e.seller_id),
                },
            },
        )


@router.post(
    "/{visit_id}/evidence/confirm",
    response_model=VisitResponse,
    summary="Confirm evidence upload",
    description="Saves the S3 URL to the visit record after successful upload.",
)
async def confirm_evidence_upload(
    visit_id: UUID,
    request: ConfirmEvidenceUploadRequest,
    use_case: ConfirmEvidenceUploadUseCase = Depends(
        get_confirm_evidence_upload_use_case
    ),
    session: AsyncSession = Depends(get_db),
):
    """Confirm evidence upload and save S3 URL.

    Authorization is enforced by BFF - microservice trusts that the seller
    can only confirm evidence for their own visits.
    """
    try:
        visit = await use_case.execute(
            visit_id=visit_id,
            s3_url=request.s3_url,
            session=session,
        )
        await session.commit()
        return VisitResponse.model_validate(visit)

    except VisitNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "VisitNotFound",
                "message": str(e),
                "details": {"visit_id": str(e.visit_id)},
            },
        )
    except UnauthorizedVisitAccessError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "UnauthorizedVisitAccess",
                "message": str(e),
                "details": {
                    "visit_id": str(e.visit_id),
                    "seller_id": str(e.seller_id),
                },
            },
        )
