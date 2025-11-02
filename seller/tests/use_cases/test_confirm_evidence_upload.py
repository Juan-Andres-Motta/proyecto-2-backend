"""Unit tests for ConfirmEvidenceUploadUseCase."""
import pytest
from datetime import datetime, timezone, timedelta
from uuid import uuid4
from unittest.mock import AsyncMock

from src.application.use_cases.confirm_evidence_upload import ConfirmEvidenceUploadUseCase
from src.domain.entities.visit import Visit, VisitStatus
from src.domain.exceptions import (
    VisitNotFoundError,
    UnauthorizedVisitAccessError,
)

@pytest.fixture
def mock_visit_repository():
    """Mock visit repository."""
    return AsyncMock()

@pytest.fixture
def mock_session():
    """Mock database session."""
    return AsyncMock()

@pytest.fixture
def use_case(mock_visit_repository):
    """ConfirmEvidenceUploadUseCase instance."""
    return ConfirmEvidenceUploadUseCase(visit_repository=mock_visit_repository)

@pytest.fixture
def visit():
    """Mock visit without evidence."""
    return Visit(
        id=uuid4(),
        seller_id=uuid4(),
        client_id=uuid4(),
        fecha_visita=datetime.now(timezone.utc) + timedelta(days=2),
        status=VisitStatus.PROGRAMADA,
        notas_visita="Test",
        recomendaciones=None,
        archivos_evidencia=None,  # No evidence yet
        client_nombre_institucion="Hospital",
        client_direccion="Address",
        client_ciudad="City",
        client_pais="Country",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

class TestConfirmEvidenceUploadSuccess:
    """Test successful evidence confirmation scenarios."""

    @pytest.mark.asyncio
    async def test_confirm_upload_success(
        self, use_case, mock_visit_repository, mock_session, visit
    ):
        """Test successful evidence upload confirmation."""
        s3_url = "https://s3.amazonaws.com/bucket/visits/123/photo.jpg"
        mock_visit_repository.find_by_id.return_value = visit

        result = await use_case.execute(
            visit_id=visit.id,            s3_url=s3_url,
            session=mock_session,
        )

        assert result.archivos_evidencia == s3_url
        mock_session.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_confirm_upload_updates_timestamp(
        self, use_case, mock_visit_repository, mock_session, visit
    ):
        """Test that updated_at timestamp is modified."""
        original_updated_at = visit.updated_at
        s3_url = "https://s3.amazonaws.com/bucket/test.jpg"
        mock_visit_repository.find_by_id.return_value = visit

        result = await use_case.execute(
            visit_id=visit.id,            s3_url=s3_url,
            session=mock_session,
        )

        # updated_at should be changed
        assert result.updated_at >= original_updated_at

    @pytest.mark.asyncio
    async def test_confirm_upload_replaces_existing_evidence(
        self, use_case, mock_visit_repository, mock_session, visit
    ):
        """Test confirming upload replaces existing evidence URL."""
        # Visit already has evidence
        visit.archivos_evidencia = "https://s3.amazonaws.com/old.jpg"

        new_s3_url = "https://s3.amazonaws.com/new.jpg"
        mock_visit_repository.find_by_id.return_value = visit

        result = await use_case.execute(
            visit_id=visit.id,            s3_url=new_s3_url,
            session=mock_session,
        )

        # Should replace old URL
        assert result.archivos_evidencia == new_s3_url

    @pytest.mark.asyncio
    async def test_confirm_upload_preserves_other_fields(
        self, use_case, mock_visit_repository, mock_session, visit
    ):
        """Test that confirming upload doesn't modify other fields."""
        original_status = visit.status
        original_notas = visit.notas_visita
        original_recomendaciones = visit.recomendaciones

        s3_url = "https://s3.amazonaws.com/test.jpg"
        mock_visit_repository.find_by_id.return_value = visit

        result = await use_case.execute(
            visit_id=visit.id,            s3_url=s3_url,
            session=mock_session,
        )

        # Other fields should remain unchanged
        assert result.status == original_status
        assert result.notas_visita == original_notas
        assert result.recomendaciones == original_recomendaciones

class TestConfirmEvidenceUploadFailures:
    """Test failure scenarios."""

    @pytest.mark.asyncio
    async def test_confirm_upload_visit_not_found(
        self, use_case, mock_visit_repository, mock_session
    ):
        """Test confirming upload when visit doesn't exist."""
        visit_id = uuid4()
        mock_visit_repository.find_by_id.return_value = None

        with pytest.raises(VisitNotFoundError) as exc_info:
            await use_case.execute(
                visit_id=visit_id,                s3_url="https://s3.amazonaws.com/test.jpg",
                session=mock_session,
            )

        assert exc_info.value.visit_id == visit_id

    
class TestConfirmEvidenceUploadOwnership:
    """Test ownership verification."""

    