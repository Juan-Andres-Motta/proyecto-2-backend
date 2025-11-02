"""Unit tests for GenerateEvidenceUploadURLUseCase."""
import pytest
from datetime import datetime, timezone, timedelta
from uuid import uuid4
from unittest.mock import AsyncMock

from src.application.use_cases.generate_evidence_upload_url import GenerateEvidenceUploadURLUseCase
from src.application.ports.s3_service_port import PreSignedUploadURL
from src.domain.entities.visit import Visit, VisitStatus
from src.domain.exceptions import (
    VisitNotFoundError,
    UnauthorizedVisitAccessError,
)
from src.adapters.output.services.s3_service_adapter import InvalidContentTypeError

@pytest.fixture
def mock_visit_repository():
    """Mock visit repository."""
    return AsyncMock()

@pytest.fixture
def mock_s3_service():
    """Mock S3 service."""
    return AsyncMock()

@pytest.fixture
def mock_session():
    """Mock database session."""
    return AsyncMock()

@pytest.fixture
def use_case(mock_visit_repository, mock_s3_service):
    """GenerateEvidenceUploadURLUseCase instance."""
    return GenerateEvidenceUploadURLUseCase(
        visit_repository=mock_visit_repository,
        s3_service=mock_s3_service,
    )

@pytest.fixture
def visit():
    """Mock visit."""
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

class TestGenerateEvidenceUploadURLSuccess:
    """Test successful URL generation scenarios."""

    @pytest.mark.asyncio
    async def test_generate_upload_url_success(
        self, use_case, mock_visit_repository, mock_s3_service, mock_session, visit
    ):
        """Test successful pre-signed URL generation."""
        mock_visit_repository.find_by_id.return_value = visit

        expected_url = PreSignedUploadURL(
            upload_url="https://s3.amazonaws.com/bucket",
            fields={"key": "visits/123/photo.jpg", "Content-Type": "image/jpeg"},
            s3_url="https://s3.amazonaws.com/bucket/visits/123/photo.jpg",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        )
        mock_s3_service.generate_upload_url.return_value = expected_url

        result = await use_case.execute(
            visit_id=visit.id,            filename="photo.jpg",
            content_type="image/jpeg",
            session=mock_session,
        )

        assert result == expected_url
        mock_visit_repository.find_by_id.assert_called_once_with(visit.id, mock_session)
        mock_s3_service.generate_upload_url.assert_called_once_with(
            visit_id=visit.id,
            filename="photo.jpg",
            content_type="image/jpeg",
        )

    @pytest.mark.asyncio
    async def test_generate_upload_url_for_different_content_types(
        self, use_case, mock_visit_repository, mock_s3_service, mock_session, visit
    ):
        """Test generating URLs for different allowed content types."""
        mock_visit_repository.find_by_id.return_value = visit

        content_types = ["image/jpeg", "image/png", "image/heic", "video/mp4", "video/quicktime"]

        for content_type in content_types:
            mock_s3_service.generate_upload_url.return_value = PreSignedUploadURL(
                upload_url="https://s3.amazonaws.com/bucket",
                fields={"key": "test", "Content-Type": content_type},
                s3_url="https://s3.amazonaws.com/bucket/test",
                expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            )

            result = await use_case.execute(
                visit_id=visit.id,                filename=f"file.{content_type.split('/')[-1]}",
                content_type=content_type,
                session=mock_session,
            )

            assert result.fields["Content-Type"] == content_type

class TestGenerateEvidenceUploadURLFailures:
    """Test failure scenarios."""

    @pytest.mark.asyncio
    async def test_generate_url_visit_not_found(
        self, use_case, mock_visit_repository, mock_session
    ):
        """Test generating URL when visit doesn't exist."""
        visit_id = uuid4()
        mock_visit_repository.find_by_id.return_value = None

        with pytest.raises(VisitNotFoundError) as exc_info:
            await use_case.execute(
                visit_id=visit_id,                filename="photo.jpg",
                content_type="image/jpeg",
                session=mock_session,
            )

        assert exc_info.value.visit_id == visit_id

    
    @pytest.mark.asyncio
    async def test_generate_url_invalid_content_type(
        self, use_case, mock_visit_repository, mock_s3_service, mock_session, visit
    ):
        """Test generating URL with invalid content type."""
        mock_visit_repository.find_by_id.return_value = visit
        mock_s3_service.generate_upload_url.side_effect = InvalidContentTypeError(
            "Content type 'application/pdf' not allowed"
        )

        with pytest.raises(InvalidContentTypeError):
            await use_case.execute(
                visit_id=visit.id,                filename="document.pdf",
                content_type="application/pdf",  # Not allowed
                session=mock_session,
            )

class TestGenerateEvidenceUploadURLOwnership:
    """Test ownership verification."""

    