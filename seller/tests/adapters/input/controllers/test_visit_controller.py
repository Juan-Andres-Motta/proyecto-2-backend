"""Unit tests for visit controller."""
import pytest
from datetime import datetime, timezone, timedelta
from uuid import uuid4
from unittest.mock import AsyncMock, patch
from fastapi import HTTPException

from src.adapters.input.controllers.visit_controller import (
    create_visit,
    update_visit_status,
    list_visits,
    generate_evidence_upload_url,
    confirm_evidence_upload,
)
from src.adapters.input.schemas import (
    CreateVisitRequest,
    UpdateVisitStatusRequest,
    GenerateEvidenceUploadURLRequest,
    ConfirmEvidenceUploadRequest,
)
from src.domain.entities.visit import Visit, VisitStatus
from src.domain.exceptions import (
    VisitNotFoundError,
    UnauthorizedVisitAccessError,
    InvalidVisitDateError,
    VisitTimeConflictError,
    ClientAssignedToOtherSellerError,
    InvalidStatusTransitionError,
)
from src.adapters.output.services.client_service_adapter import (
    ClientServiceConnectionError,
)
from src.adapters.output.services.s3_service_adapter import InvalidContentTypeError
from src.application.ports.s3_service_port import PreSignedUploadURL


@pytest.fixture
def mock_session():
    """Mock database session."""
    session = AsyncMock()
    session.commit = AsyncMock()
    return session


@pytest.fixture
def seller_id():
    """Fixed seller ID."""
    return uuid4()


@pytest.fixture
def visit_entity():
    """Mock visit entity."""
    return Visit(
        id=uuid4(),
        seller_id=uuid4(),
        client_id=uuid4(),
        fecha_visita=datetime.now(timezone.utc) + timedelta(days=2),
        status=VisitStatus.PROGRAMADA,
        notas_visita="Test",
        recomendaciones=None,
        archivos_evidencia=None,
        client_nombre_institucion="Hospital",
        client_direccion="Address",
        client_ciudad="City",
        client_pais="Country",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


class TestCreateVisitController:
    """Test create_visit endpoint."""

    @pytest.mark.asyncio
    async def test_create_visit_success(self, mock_session, seller_id, visit_entity):
        """Test successful visit creation."""
        request = CreateVisitRequest(
            client_id=uuid4(),
            fecha_visita=datetime.now(timezone.utc) + timedelta(days=2),
            notas_visita="Test",
        )

        mock_saga = AsyncMock()
        mock_saga.execute.return_value = visit_entity

        response = await create_visit(
            request=request,
            seller_id=seller_id,
            saga=mock_saga,
            session=mock_session,
        )

        assert response.id == visit_entity.id
        assert response.status == VisitStatus.PROGRAMADA.value
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_visit_invalid_date(self, mock_session, seller_id):
        """Test creating visit with invalid date raises 400."""
        request = CreateVisitRequest(
            client_id=uuid4(),
            fecha_visita=datetime.now(timezone.utc) + timedelta(hours=12),
            notas_visita=None,
        )

        mock_saga = AsyncMock()
        mock_saga.execute.side_effect = InvalidVisitDateError(
            fecha_visita=request.fecha_visita,
            earliest_allowed_date=datetime.now(timezone.utc) + timedelta(days=1),
        )

        with pytest.raises(HTTPException) as exc_info:
            await create_visit(
                request=request,
                seller_id=seller_id,
                saga=mock_saga,
                session=mock_session,
            )

        assert exc_info.value.status_code == 400
        assert "InvalidDate" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_create_visit_time_conflict(self, mock_session, seller_id, visit_entity):
        """Test creating visit with time conflict raises 409."""
        request = CreateVisitRequest(
            client_id=uuid4(),
            fecha_visita=datetime.now(timezone.utc) + timedelta(days=2),
            notas_visita=None,
        )

        mock_saga = AsyncMock()
        mock_saga.execute.side_effect = VisitTimeConflictError(
            requested_time=request.fecha_visita,
            conflicting_visit=visit_entity,
        )

        with pytest.raises(HTTPException) as exc_info:
            await create_visit(
                request=request,
                seller_id=seller_id,
                saga=mock_saga,
                session=mock_session,
            )

        assert exc_info.value.status_code == 409

    @pytest.mark.asyncio
    async def test_create_visit_client_assigned_to_other_seller(self, mock_session, seller_id):
        """Test creating visit for client assigned to other seller raises 403."""
        request = CreateVisitRequest(
            client_id=uuid4(),
            fecha_visita=datetime.now(timezone.utc) + timedelta(days=2),
            notas_visita=None,
        )

        mock_saga = AsyncMock()
        mock_saga.execute.side_effect = ClientAssignedToOtherSellerError(
            client_id=request.client_id,
            client_nombre="Hospital",
            assigned_seller_id=uuid4(),
        )

        with pytest.raises(HTTPException) as exc_info:
            await create_visit(
                request=request,
                seller_id=seller_id,
                saga=mock_saga,
                session=mock_session,
            )

        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_create_visit_client_not_found(self, mock_session, seller_id):
        """Test creating visit for non-existent client raises 404."""
        request = CreateVisitRequest(
            client_id=uuid4(),
            fecha_visita=datetime.now(timezone.utc) + timedelta(days=2),
            notas_visita=None,
        )

        mock_saga = AsyncMock()
        mock_saga.execute.side_effect = VisitNotFoundError(request.client_id)

        with pytest.raises(HTTPException) as exc_info:
            await create_visit(
                request=request,
                seller_id=seller_id,
                saga=mock_saga,
                session=mock_session,
            )

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_create_visit_client_service_unavailable(self, mock_session, seller_id):
        """Test creating visit when Client Service is unavailable raises 503."""
        request = CreateVisitRequest(
            client_id=uuid4(),
            fecha_visita=datetime.now(timezone.utc) + timedelta(days=2),
            notas_visita=None,
        )

        mock_saga = AsyncMock()
        mock_saga.execute.side_effect = ClientServiceConnectionError("Timeout")

        with pytest.raises(HTTPException) as exc_info:
            await create_visit(
                request=request,
                seller_id=seller_id,
                saga=mock_saga,
                session=mock_session,
            )

        assert exc_info.value.status_code == 503


class TestUpdateVisitStatusController:
    """Test update_visit_status endpoint."""

    @pytest.mark.asyncio
    async def test_update_status_success(self, mock_session, seller_id, visit_entity):
        """Test successful status update."""
        visit_id = uuid4()
        request = UpdateVisitStatusRequest(
            status=VisitStatus.COMPLETADA,
            recomendaciones="Recommend Product X",
        )

        visit_entity.status = VisitStatus.COMPLETADA
        visit_entity.recomendaciones = "Recommend Product X"

        mock_use_case = AsyncMock()
        mock_use_case.execute.return_value = visit_entity

        response = await update_visit_status(
            visit_id=visit_id,
            request=request,
            seller_id=seller_id,
            use_case=mock_use_case,
            session=mock_session,
        )

        assert response.status == VisitStatus.COMPLETADA.value
        assert response.recomendaciones == "Recommend Product X"
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_status_visit_not_found(self, mock_session, seller_id):
        """Test updating status when visit not found raises 404."""
        visit_id = uuid4()
        request = UpdateVisitStatusRequest(status=VisitStatus.COMPLETADA, recomendaciones=None)

        mock_use_case = AsyncMock()
        mock_use_case.execute.side_effect = VisitNotFoundError(visit_id)

        with pytest.raises(HTTPException) as exc_info:
            await update_visit_status(
                visit_id=visit_id,
                request=request,
                seller_id=seller_id,
                use_case=mock_use_case,
                session=mock_session,
            )

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_update_status_unauthorized(self, mock_session, seller_id):
        """Test updating status when unauthorized raises 403."""
        visit_id = uuid4()
        request = UpdateVisitStatusRequest(status=VisitStatus.COMPLETADA, recomendaciones=None)

        mock_use_case = AsyncMock()
        mock_use_case.execute.side_effect = UnauthorizedVisitAccessError(visit_id, seller_id)

        with pytest.raises(HTTPException) as exc_info:
            await update_visit_status(
                visit_id=visit_id,
                request=request,
                seller_id=seller_id,
                use_case=mock_use_case,
                session=mock_session,
            )

        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_update_status_invalid_transition(self, mock_session, seller_id):
        """Test invalid status transition raises 400."""
        visit_id = uuid4()
        request = UpdateVisitStatusRequest(status=VisitStatus.PROGRAMADA, recomendaciones=None)

        mock_use_case = AsyncMock()
        mock_use_case.execute.side_effect = InvalidStatusTransitionError("completada", "programada")

        with pytest.raises(HTTPException) as exc_info:
            await update_visit_status(
                visit_id=visit_id,
                request=request,
                seller_id=seller_id,
                use_case=mock_use_case,
                session=mock_session,
            )

        assert exc_info.value.status_code == 400


class TestListVisitsController:
    """Test list_visits endpoint."""

    @pytest.mark.asyncio
    async def test_list_visits_success(self, mock_session, seller_id, visit_entity):
        """Test successful visit listing."""
        date = datetime.now(timezone.utc)
        mock_use_case = AsyncMock()
        mock_use_case.execute.return_value = [visit_entity]

        response = await list_visits(
            date=date,
            seller_id=seller_id,
            use_case=mock_use_case,
            session=mock_session,
        )

        assert response.count == 1
        assert len(response.visits) == 1

    @pytest.mark.asyncio
    async def test_list_visits_empty(self, mock_session, seller_id):
        """Test listing visits returns empty list."""
        date = datetime.now(timezone.utc)
        mock_use_case = AsyncMock()
        mock_use_case.execute.return_value = []

        response = await list_visits(
            date=date,
            seller_id=seller_id,
            use_case=mock_use_case,
            session=mock_session,
        )

        assert response.count == 0
        assert response.visits == []


class TestGenerateEvidenceUploadURLController:
    """Test generate_evidence_upload_url endpoint."""

    @pytest.mark.asyncio
    async def test_generate_url_success(self, mock_session, seller_id):
        """Test successful URL generation."""
        visit_id = uuid4()
        request = GenerateEvidenceUploadURLRequest(
            filename="photo.jpg",
            content_type="image/jpeg",
        )

        upload_url = PreSignedUploadURL(
            upload_url="https://s3.amazonaws.com/bucket",
            fields={"key": "test"},
            s3_url="https://s3.amazonaws.com/bucket/test",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        )

        mock_use_case = AsyncMock()
        mock_use_case.execute.return_value = upload_url

        response = await generate_evidence_upload_url(
            visit_id=visit_id,
            request=request,
            seller_id=seller_id,
            use_case=mock_use_case,
            session=mock_session,
        )

        assert response.upload_url == upload_url.upload_url
        assert response.s3_url == upload_url.s3_url

    @pytest.mark.asyncio
    async def test_generate_url_invalid_content_type(self, mock_session, seller_id):
        """Test generating URL with invalid content type raises 422."""
        visit_id = uuid4()
        request = GenerateEvidenceUploadURLRequest(
            filename="doc.pdf",
            content_type="application/pdf",
        )

        mock_use_case = AsyncMock()
        mock_use_case.execute.side_effect = InvalidContentTypeError("PDF not allowed")

        with pytest.raises(HTTPException) as exc_info:
            await generate_evidence_upload_url(
                visit_id=visit_id,
                request=request,
                seller_id=seller_id,
                use_case=mock_use_case,
                session=mock_session,
            )

        assert exc_info.value.status_code == 422


class TestConfirmEvidenceUploadController:
    """Test confirm_evidence_upload endpoint."""

    @pytest.mark.asyncio
    async def test_confirm_upload_success(self, mock_session, seller_id, visit_entity):
        """Test successful upload confirmation."""
        visit_id = uuid4()
        request = ConfirmEvidenceUploadRequest(
            s3_url="https://s3.amazonaws.com/bucket/photo.jpg"
        )

        visit_entity.archivos_evidencia = request.s3_url

        mock_use_case = AsyncMock()
        mock_use_case.execute.return_value = visit_entity

        response = await confirm_evidence_upload(
            visit_id=visit_id,
            request=request,
            seller_id=seller_id,
            use_case=mock_use_case,
            session=mock_session,
        )

        assert response.archivos_evidencia == request.s3_url
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_confirm_upload_visit_not_found(self, mock_session, seller_id):
        """Test confirming upload for non-existent visit raises 404."""
        visit_id = uuid4()
        request = ConfirmEvidenceUploadRequest(
            s3_url="https://s3.amazonaws.com/bucket/photo.jpg"
        )

        mock_use_case = AsyncMock()
        mock_use_case.execute.side_effect = VisitNotFoundError(visit_id)

        with pytest.raises(HTTPException) as exc_info:
            await confirm_evidence_upload(
                visit_id=visit_id,
                request=request,
                seller_id=seller_id,
                use_case=mock_use_case,
                session=mock_session,
            )

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_confirm_upload_unauthorized(self, mock_session, seller_id):
        """Test confirming upload when unauthorized raises 403."""
        visit_id = uuid4()
        request = ConfirmEvidenceUploadRequest(
            s3_url="https://s3.amazonaws.com/bucket/photo.jpg"
        )

        mock_use_case = AsyncMock()
        mock_use_case.execute.side_effect = UnauthorizedVisitAccessError(visit_id, seller_id)

        with pytest.raises(HTTPException) as exc_info:
            await confirm_evidence_upload(
                visit_id=visit_id,
                request=request,
                seller_id=seller_id,
                use_case=mock_use_case,
                session=mock_session,
            )

        assert exc_info.value.status_code == 403


class TestGenerateEvidenceUploadURLControllerAdditional:
    """Additional tests for generate_evidence_upload_url endpoint."""

    @pytest.mark.asyncio
    async def test_generate_url_visit_not_found(self, mock_session, seller_id):
        """Test generating URL for non-existent visit raises 404."""
        visit_id = uuid4()
        request = GenerateEvidenceUploadURLRequest(
            filename="photo.jpg",
            content_type="image/jpeg",
        )

        mock_use_case = AsyncMock()
        mock_use_case.execute.side_effect = VisitNotFoundError(visit_id)

        with pytest.raises(HTTPException) as exc_info:
            await generate_evidence_upload_url(
                visit_id=visit_id,
                request=request,
                seller_id=seller_id,
                use_case=mock_use_case,
                session=mock_session,
            )

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_generate_url_unauthorized(self, mock_session, seller_id):
        """Test generating URL when unauthorized raises 403."""
        visit_id = uuid4()
        request = GenerateEvidenceUploadURLRequest(
            filename="photo.jpg",
            content_type="image/jpeg",
        )

        mock_use_case = AsyncMock()
        mock_use_case.execute.side_effect = UnauthorizedVisitAccessError(visit_id, seller_id)

        with pytest.raises(HTTPException) as exc_info:
            await generate_evidence_upload_url(
                visit_id=visit_id,
                request=request,
                seller_id=seller_id,
                use_case=mock_use_case,
                session=mock_session,
            )

        assert exc_info.value.status_code == 403


class TestCreateVisitControllerAdditional:
    """Additional tests for create_visit endpoint."""

    @pytest.mark.asyncio
    async def test_create_visit_assignment_failed(self, mock_session, seller_id):
        """Test creating visit when client assignment fails raises 503."""
        from src.adapters.output.services.client_service_adapter import (
            ClientAssignmentFailedError,
        )

        request = CreateVisitRequest(
            client_id=uuid4(),
            fecha_visita=datetime.now(timezone.utc) + timedelta(days=2),
            notas_visita=None,
        )

        mock_saga = AsyncMock()
        mock_saga.execute.side_effect = ClientAssignmentFailedError("Assignment failed")

        with pytest.raises(HTTPException) as exc_info:
            await create_visit(
                request=request,
                seller_id=seller_id,
                saga=mock_saga,
                session=mock_session,
            )

        assert exc_info.value.status_code == 503


class TestUpdateVisitStatusControllerEdgeCases:
    """Edge case tests for update_visit_status endpoint."""

    @pytest.mark.asyncio
    async def test_update_status_with_recommendations(self, mock_session, seller_id, visit_entity):
        """Test updating status with recommendations."""
        visit_id = uuid4()
        recommendations = "Recommend product A and B"
        request = UpdateVisitStatusRequest(
            status=VisitStatus.COMPLETADA,
            recomendaciones=recommendations,
        )

        visit_entity.status = VisitStatus.COMPLETADA
        visit_entity.recomendaciones = recommendations

        mock_use_case = AsyncMock()
        mock_use_case.execute.return_value = visit_entity

        response = await update_visit_status(
            visit_id=visit_id,
            request=request,
            seller_id=seller_id,
            use_case=mock_use_case,
            session=mock_session,
        )

        assert response.recomendaciones == recommendations

    @pytest.mark.asyncio
    async def test_update_status_without_recommendations(self, mock_session, seller_id, visit_entity):
        """Test updating status without recommendations."""
        visit_id = uuid4()
        request = UpdateVisitStatusRequest(
            status=VisitStatus.COMPLETADA,
            recomendaciones=None,
        )

        visit_entity.status = VisitStatus.COMPLETADA
        visit_entity.recomendaciones = None

        mock_use_case = AsyncMock()
        mock_use_case.execute.return_value = visit_entity

        response = await update_visit_status(
            visit_id=visit_id,
            request=request,
            seller_id=seller_id,
            use_case=mock_use_case,
            session=mock_session,
        )

        assert response.recomendaciones is None


class TestListVisitsControllerEdgeCases:
    """Edge case tests for list_visits endpoint."""

    @pytest.mark.asyncio
    async def test_list_visits_with_multiple_visits(self, mock_session, seller_id):
        """Test listing multiple visits on same date."""
        date = datetime.now(timezone.utc)

        visits = [
            Visit(
                id=uuid4(),
                seller_id=seller_id,
                client_id=uuid4(),
                fecha_visita=date + timedelta(hours=i),
                status=VisitStatus.PROGRAMADA,
                notas_visita=f"Visit {i}",
                recomendaciones=None,
                archivos_evidencia=None,
                client_nombre_institucion="Hospital",
                client_direccion="Address",
                client_ciudad="City",
                client_pais="Country",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            for i in range(3)
        ]

        mock_use_case = AsyncMock()
        mock_use_case.execute.return_value = visits

        response = await list_visits(
            date=date,
            seller_id=seller_id,
            use_case=mock_use_case,
            session=mock_session,
        )

        assert response.count == 3
        assert len(response.visits) == 3
