"""Unit tests for UpdateVisitStatusUseCase."""
import pytest
from datetime import datetime, timezone
from uuid import uuid4
from unittest.mock import AsyncMock
from dataclasses import replace

from src.application.use_cases.update_visit_status import UpdateVisitStatusUseCase
from src.domain.entities.visit import Visit, VisitStatus
from src.domain.exceptions import (
    VisitNotFoundError,
    UnauthorizedVisitAccessError,
    InvalidStatusTransitionError,
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
    """UpdateVisitStatusUseCase instance."""
    return UpdateVisitStatusUseCase(visit_repository=mock_visit_repository)

@pytest.fixture
def programmed_visit():
    """Mock programmed visit."""
    return Visit(
        id=uuid4(),
        seller_id=uuid4(),
        client_id=uuid4(),
        fecha_visita=datetime.now(timezone.utc),
        status=VisitStatus.PROGRAMADA,
        notas_visita="Test notes",
        recomendaciones=None,
        archivos_evidencia=None,
        client_nombre_institucion="Hospital",
        client_direccion="Address",
        client_ciudad="City",
        client_pais="Country",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

class TestUpdateVisitStatusSuccess:
    """Test successful status update scenarios."""

    @pytest.mark.asyncio
    async def test_update_status_programada_to_completada(
        self, use_case, mock_visit_repository, mock_session, programmed_visit
    ):
        """Test updating status from programada to completada."""
        mock_visit_repository.find_by_id.return_value = programmed_visit

        # Mock the update method to return the updated visit
        updated_visit = replace(
            programmed_visit,
            status=VisitStatus.COMPLETADA,
            recomendaciones="Recommend Product X",
        )
        mock_visit_repository.update.return_value = updated_visit

        result = await use_case.execute(
            visit_id=programmed_visit.id,
            new_status=VisitStatus.COMPLETADA,
            recomendaciones="Recommend Product X",
            session=mock_session,
        )

        assert result.status == VisitStatus.COMPLETADA
        assert result.recomendaciones == "Recommend Product X"
        mock_visit_repository.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_status_programada_to_cancelada(
        self, use_case, mock_visit_repository, mock_session, programmed_visit
    ):
        """Test updating status from programada to cancelada."""
        mock_visit_repository.find_by_id.return_value = programmed_visit

        # Mock the update method to return the updated visit
        updated_visit = replace(programmed_visit, status=VisitStatus.CANCELADA)
        mock_visit_repository.update.return_value = updated_visit

        result = await use_case.execute(
            visit_id=programmed_visit.id,
            new_status=VisitStatus.CANCELADA,
            recomendaciones=None,
            session=mock_session,
        )

        assert result.status == VisitStatus.CANCELADA
        mock_visit_repository.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_status_with_no_recommendations(
        self, use_case, mock_visit_repository, mock_session, programmed_visit
    ):
        """Test updating status without providing recommendations."""
        mock_visit_repository.find_by_id.return_value = programmed_visit

        # Mock the update method to return the updated visit
        updated_visit = replace(programmed_visit, status=VisitStatus.COMPLETADA)
        mock_visit_repository.update.return_value = updated_visit

        result = await use_case.execute(
            visit_id=programmed_visit.id,
            new_status=VisitStatus.COMPLETADA,
            recomendaciones=None,
            session=mock_session,
        )

        assert result.status == VisitStatus.COMPLETADA
        assert result.recomendaciones is None

    @pytest.mark.asyncio
    async def test_update_status_to_same_status(
        self, use_case, mock_visit_repository, mock_session, programmed_visit
    ):
        """Test updating status to the same status (no-op)."""
        mock_visit_repository.find_by_id.return_value = programmed_visit

        # Mock the update method to return the same visit
        updated_visit = replace(programmed_visit)
        mock_visit_repository.update.return_value = updated_visit

        result = await use_case.execute(
            visit_id=programmed_visit.id,
            new_status=VisitStatus.PROGRAMADA,
            recomendaciones=None,
            session=mock_session,
        )

        # Should succeed (no-op)
        assert result.status == VisitStatus.PROGRAMADA
        mock_visit_repository.update.assert_called_once()

class TestUpdateVisitStatusFailures:
    """Test failure scenarios."""

    @pytest.mark.asyncio
    async def test_update_status_visit_not_found(
        self, use_case, mock_visit_repository, mock_session
    ):
        """Test updating status when visit doesn't exist."""
        visit_id = uuid4()
        mock_visit_repository.find_by_id.return_value = None

        with pytest.raises(VisitNotFoundError) as exc_info:
            await use_case.execute(
                visit_id=visit_id,                new_status=VisitStatus.COMPLETADA,
                recomendaciones=None,
                session=mock_session,
            )

        assert exc_info.value.visit_id == visit_id

    
    @pytest.mark.asyncio
    async def test_update_status_invalid_transition_from_completada(
        self, use_case, mock_visit_repository, mock_session
    ):
        """Test invalid transition from completada to programada."""
        completed_visit = Visit(
            id=uuid4(),
            seller_id=uuid4(),
            client_id=uuid4(),
            fecha_visita=datetime.now(timezone.utc),
            status=VisitStatus.COMPLETADA,  # Already completed
            notas_visita=None,
            recomendaciones=None,
            archivos_evidencia=None,
            client_nombre_institucion="Hospital",
            client_direccion="Address",
            client_ciudad="City",
            client_pais="Country",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        mock_visit_repository.find_by_id.return_value = completed_visit

        with pytest.raises(InvalidStatusTransitionError):
            await use_case.execute(
                visit_id=completed_visit.id,                new_status=VisitStatus.PROGRAMADA,
                recomendaciones=None,
                session=mock_session,
            )

    @pytest.mark.asyncio
    async def test_update_status_invalid_transition_from_cancelada(
        self, use_case, mock_visit_repository, mock_session
    ):
        """Test invalid transition from cancelada to completada."""
        cancelled_visit = Visit(
            id=uuid4(),
            seller_id=uuid4(),
            client_id=uuid4(),
            fecha_visita=datetime.now(timezone.utc),
            status=VisitStatus.CANCELADA,  # Already cancelled
            notas_visita=None,
            recomendaciones=None,
            archivos_evidencia=None,
            client_nombre_institucion="Hospital",
            client_direccion="Address",
            client_ciudad="City",
            client_pais="Country",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        mock_visit_repository.find_by_id.return_value = cancelled_visit

        with pytest.raises(InvalidStatusTransitionError):
            await use_case.execute(
                visit_id=cancelled_visit.id,                new_status=VisitStatus.COMPLETADA,
                recomendaciones=None,
                session=mock_session,
            )

class TestUpdateVisitStatusTimestampUpdate:
    """Test that updated_at timestamp is updated."""

    @pytest.mark.asyncio
    async def test_updated_at_timestamp_changes(
        self, use_case, mock_visit_repository, mock_session, programmed_visit
    ):
        """Test that updated_at timestamp is modified."""
        from dataclasses import replace

        original_updated_at = programmed_visit.updated_at
        mock_visit_repository.find_by_id.return_value = programmed_visit

        # Mock the update method to return the updated visit with new timestamp
        updated_visit = replace(
            programmed_visit,
            status=VisitStatus.COMPLETADA,
            recomendaciones="Test",
            updated_at=datetime.now(timezone.utc),
        )
        mock_visit_repository.update.return_value = updated_visit

        result = await use_case.execute(
            visit_id=programmed_visit.id,
            new_status=VisitStatus.COMPLETADA,
            recomendaciones="Test",
            session=mock_session,
        )

        # updated_at should be changed (newer timestamp)
        assert result.updated_at >= original_updated_at
