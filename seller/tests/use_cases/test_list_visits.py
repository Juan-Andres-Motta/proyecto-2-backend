"""Unit tests for ListVisitsUseCase."""
import pytest
from datetime import datetime, timezone, timedelta
from uuid import uuid4
from unittest.mock import AsyncMock

from src.application.use_cases.list_visits import ListVisitsUseCase
from src.domain.entities.visit import Visit, VisitStatus


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
    """ListVisitsUseCase instance."""
    return ListVisitsUseCase(visit_repository=mock_visit_repository)


@pytest.fixture
def seller_id():
    """Fixed seller ID for tests."""
    return uuid4()


@pytest.fixture
def test_date():
    """Test date."""
    return datetime(2025, 11, 16, 0, 0, 0, tzinfo=timezone.utc)


class TestListVisitsSuccess:
    """Test successful visit listing scenarios."""

    @pytest.mark.asyncio
    async def test_list_visits_returns_visits(
        self, use_case, mock_visit_repository, mock_session, seller_id, test_date
    ):
        """Test listing visits returns list of Visit entities."""
        visit1 = Visit(
            id=uuid4(),
            seller_id=seller_id,
            client_id=uuid4(),
            fecha_visita=datetime(2025, 11, 16, 10, 0, tzinfo=timezone.utc),
            status=VisitStatus.PROGRAMADA,
            notas_visita="Morning visit",
            recomendaciones=None,
            archivos_evidencia=None,
            client_nombre_institucion="Hospital A",
            client_direccion="Address A",
            client_ciudad="City A",
            client_pais="Country A",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        visit2 = Visit(
            id=uuid4(),
            seller_id=seller_id,
            client_id=uuid4(),
            fecha_visita=datetime(2025, 11, 16, 14, 0, tzinfo=timezone.utc),
            status=VisitStatus.PROGRAMADA,
            notas_visita="Afternoon visit",
            recomendaciones=None,
            archivos_evidencia=None,
            client_nombre_institucion="Hospital B",
            client_direccion="Address B",
            client_ciudad="City B",
            client_pais="Country B",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        mock_visit_repository.get_visits_by_date.return_value = [visit1, visit2]

        result = await use_case.execute(
            seller_id=seller_id, date=test_date, session=mock_session
        )

        assert len(result) == 2
        assert result[0] == visit1
        assert result[1] == visit2
        mock_visit_repository.get_visits_by_date.assert_called_once_with(
            seller_id=seller_id, date=test_date, session=mock_session
        )

    @pytest.mark.asyncio
    async def test_list_visits_returns_empty_list_when_no_visits(
        self, use_case, mock_visit_repository, mock_session, seller_id, test_date
    ):
        """Test listing visits returns empty list when no visits exist."""
        mock_visit_repository.get_visits_by_date.return_value = []

        result = await use_case.execute(
            seller_id=seller_id, date=test_date, session=mock_session
        )

        assert result == []
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_list_visits_with_different_statuses(
        self, use_case, mock_visit_repository, mock_session, seller_id, test_date
    ):
        """Test listing visits includes all statuses."""
        programmed = Visit(
            id=uuid4(),
            seller_id=seller_id,
            client_id=uuid4(),
            fecha_visita=datetime(2025, 11, 16, 10, 0, tzinfo=timezone.utc),
            status=VisitStatus.PROGRAMADA,
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
        completed = Visit(
            id=uuid4(),
            seller_id=seller_id,
            client_id=uuid4(),
            fecha_visita=datetime(2025, 11, 16, 11, 0, tzinfo=timezone.utc),
            status=VisitStatus.COMPLETADA,
            notas_visita=None,
            recomendaciones="Recommended products",
            archivos_evidencia=None,
            client_nombre_institucion="Clinic",
            client_direccion="Address 2",
            client_ciudad="City 2",
            client_pais="Country 2",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        cancelled = Visit(
            id=uuid4(),
            seller_id=seller_id,
            client_id=uuid4(),
            fecha_visita=datetime(2025, 11, 16, 12, 0, tzinfo=timezone.utc),
            status=VisitStatus.CANCELADA,
            notas_visita=None,
            recomendaciones=None,
            archivos_evidencia=None,
            client_nombre_institucion="Center",
            client_direccion="Address 3",
            client_ciudad="City 3",
            client_pais="Country 3",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        mock_visit_repository.get_visits_by_date.return_value = [programmed, completed, cancelled]

        result = await use_case.execute(
            seller_id=seller_id, date=test_date, session=mock_session
        )

        assert len(result) == 3
        assert result[0].status == VisitStatus.PROGRAMADA
        assert result[1].status == VisitStatus.COMPLETADA
        assert result[2].status == VisitStatus.CANCELADA

    @pytest.mark.asyncio
    async def test_list_visits_chronological_order(
        self, use_case, mock_visit_repository, mock_session, seller_id, test_date
    ):
        """Test visits are ordered chronologically by fecha_visita."""
        # Repository should return visits in chronological order
        early = Visit(
            id=uuid4(),
            seller_id=seller_id,
            client_id=uuid4(),
            fecha_visita=datetime(2025, 11, 16, 8, 0, tzinfo=timezone.utc),
            status=VisitStatus.PROGRAMADA,
            notas_visita="Early",
            recomendaciones=None,
            archivos_evidencia=None,
            client_nombre_institucion="Hospital",
            client_direccion="Address",
            client_ciudad="City",
            client_pais="Country",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        late = Visit(
            id=uuid4(),
            seller_id=seller_id,
            client_id=uuid4(),
            fecha_visita=datetime(2025, 11, 16, 16, 0, tzinfo=timezone.utc),
            status=VisitStatus.PROGRAMADA,
            notas_visita="Late",
            recomendaciones=None,
            archivos_evidencia=None,
            client_nombre_institucion="Clinic",
            client_direccion="Address 2",
            client_ciudad="City 2",
            client_pais="Country 2",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        # Repository guarantees chronological order
        mock_visit_repository.get_visits_by_date.return_value = [early, late]

        result = await use_case.execute(
            seller_id=seller_id, date=test_date, session=mock_session
        )

        # Verify order is preserved
        assert result[0].fecha_visita < result[1].fecha_visita
        assert result[0].notas_visita == "Early"
        assert result[1].notas_visita == "Late"
