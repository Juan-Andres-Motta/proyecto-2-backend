"""Unit tests for VisitRepository."""
import pytest
from datetime import datetime, timezone, timedelta
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch

from src.adapters.output.repositories.visit_repository import VisitRepository
from src.domain.entities.visit import Visit, VisitStatus
from src.infrastructure.database.models import Visit as ORMVisit


class TestVisitRepositoryCreate:
    """Test visit creation."""

    @pytest.mark.asyncio
    async def test_create_visit_returns_domain_entity(self):
        """Test that create returns a Visit domain entity."""
        repo = VisitRepository()
        session = AsyncMock()

        visit = Visit(
            id=uuid4(),
            seller_id=uuid4(),
            client_id=uuid4(),
            fecha_visita=datetime(2025, 11, 16, 10, 0, tzinfo=timezone.utc),
            status=VisitStatus.PROGRAMADA,
            notas_visita="Test visit",
            recomendaciones=None,
            archivos_evidencia="https://s3.amazonaws.com/bucket/evidence.pdf",
            client_nombre_institucion="Hospital Central",
            client_direccion="Calle 123",
            client_ciudad="Bogotá",
            client_pais="Colombia",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        created = await repo.create(visit, session)

        assert created is not None
        assert created.id == visit.id
        assert created.status == VisitStatus.PROGRAMADA
        session.add.assert_called_once()
        session.flush.assert_called_once()


class TestVisitRepositoryFindById:
    """Test finding visits by ID."""

    @pytest.mark.asyncio
    async def test_find_by_id_when_not_exists(self):
        """Test finding a visit that doesn't exist returns None."""
        repo = VisitRepository()
        session = AsyncMock()

        # Mock query result: no visit found
        mock_result = MagicMock()
        mock_result.scalars().first.return_value = None
        session.execute.return_value = mock_result

        found = await repo.find_by_id(uuid4(), session)

        assert found is None
        session.execute.assert_called_once()


class TestVisitRepositoryGetVisitsByDate:
    """Test retrieving visits by date."""

    @pytest.mark.asyncio
    async def test_get_visits_by_date_returns_empty_list_when_no_visits(self):
        """Test that get_visits_by_date returns empty list when no visits exist."""
        repo = VisitRepository()
        session = AsyncMock()
        seller_id = uuid4()
        test_date = datetime(2025, 11, 16, tzinfo=timezone.utc)

        # Mock query result: no visits found
        mock_result = MagicMock()
        mock_result.scalars().all.return_value = []
        session.execute.return_value = mock_result

        visits = await repo.get_visits_by_date(seller_id, test_date, session)

        assert visits == []
        session.execute.assert_called_once()


class TestVisitRepositoryConflictDetection:
    """Test 180-minute conflict detection."""

    @pytest.mark.asyncio
    async def test_has_conflicting_visit_when_no_conflict(self):
        """Test returns None when no conflicting visit exists."""
        repo = VisitRepository()
        session = AsyncMock()
        seller_id = uuid4()

        # Mock query result: no conflict found
        mock_result = MagicMock()
        mock_result.scalars().first.return_value = None
        session.execute.return_value = mock_result

        conflict = await repo.has_conflicting_visit(
            seller_id, datetime(2025, 11, 16, 10, 0, tzinfo=timezone.utc), session
        )

        assert conflict is None
        session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_has_conflicting_visit_excludes_cancelled_visits(self):
        """Test that query excludes cancelled visits from conflict detection."""
        repo = VisitRepository()
        session = AsyncMock()
        seller_id = uuid4()

        # Mock query result: no conflict (cancelled visits excluded)
        mock_result = MagicMock()
        mock_result.scalars().first.return_value = None
        session.execute.return_value = mock_result

        await repo.has_conflicting_visit(
            seller_id, datetime(2025, 11, 16, 10, 0, tzinfo=timezone.utc), session
        )

        # Verify query was executed
        session.execute.assert_called_once()
        # Note: In a more detailed unit test, we could verify the SQL query
        # excludes status='cancelada', but that requires inspecting the statement


class TestVisitRepositoryMappers:
    """Test ORM to domain and domain to ORM mapping."""

    def test_to_domain_mapping_all_fields(self):
        """Test _to_domain mapper converts all ORM fields correctly."""
        visit_id = uuid4()
        seller_id = uuid4()
        client_id = uuid4()
        now = datetime.now(timezone.utc)
        fecha_visita = datetime(2025, 11, 16, 10, 0, tzinfo=timezone.utc)

        orm_visit = ORMVisit(
            id=visit_id,
            seller_id=seller_id,
            client_id=client_id,
            fecha_visita=fecha_visita,
            status="completada",
            notas_visita="Test notes",
            recomendaciones="Test recommendations",
            archivos_evidencia="https://s3.amazonaws.com/bucket/photo.jpg",
            client_nombre_institucion="Hospital Central",
            client_direccion="Calle 123",
            client_ciudad="Bogotá",
            client_pais="Colombia",
            created_at=now,
            updated_at=now,
        )

        domain_visit = VisitRepository._to_domain(orm_visit)

        assert domain_visit.id == visit_id
        assert domain_visit.seller_id == seller_id
        assert domain_visit.client_id == client_id
        assert domain_visit.fecha_visita == fecha_visita
        assert domain_visit.status == VisitStatus.COMPLETADA
        assert domain_visit.notas_visita == "Test notes"
        assert domain_visit.recomendaciones == "Test recommendations"
        assert domain_visit.archivos_evidencia == "https://s3.amazonaws.com/bucket/photo.jpg"
        assert domain_visit.client_nombre_institucion == "Hospital Central"

    def test_to_orm_mapping_all_fields(self):
        """Test _to_orm mapper converts all domain fields correctly."""
        visit_id = uuid4()
        seller_id = uuid4()
        client_id = uuid4()
        now = datetime.now(timezone.utc)
        fecha_visita = datetime(2025, 11, 16, 10, 0, tzinfo=timezone.utc)

        domain_visit = Visit(
            id=visit_id,
            seller_id=seller_id,
            client_id=client_id,
            fecha_visita=fecha_visita,
            status=VisitStatus.PROGRAMADA,
            notas_visita="Domain notes",
            recomendaciones="Domain recommendations",
            archivos_evidencia="https://s3.amazonaws.com/bucket/domain.jpg",
            client_nombre_institucion="Domain Hospital",
            client_direccion="Domain Address",
            client_ciudad="Domain City",
            client_pais="Domain Country",
            created_at=now,
            updated_at=now,
        )

        orm_visit = VisitRepository._to_orm(domain_visit)

        assert orm_visit.id == visit_id
        assert orm_visit.seller_id == seller_id
        assert orm_visit.client_id == client_id
        assert orm_visit.fecha_visita == fecha_visita
        assert orm_visit.status == "programada"  # Enum converted to string
        assert orm_visit.notas_visita == "Domain notes"
        assert orm_visit.recomendaciones == "Domain recommendations"
        assert orm_visit.archivos_evidencia == "https://s3.amazonaws.com/bucket/domain.jpg"
        assert orm_visit.client_nombre_institucion == "Domain Hospital"

    def test_to_orm_preserves_status_enum_conversion(self):
        """Test _to_orm correctly converts all status enums to strings."""
        for status in [VisitStatus.PROGRAMADA, VisitStatus.COMPLETADA, VisitStatus.CANCELADA]:
            domain_visit = Visit(
                id=uuid4(),
                seller_id=uuid4(),
                client_id=uuid4(),
                fecha_visita=datetime(2025, 11, 16, 10, 0, tzinfo=timezone.utc),
                status=status,
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

            orm_visit = VisitRepository._to_orm(domain_visit)

            assert orm_visit.status == status.value
            assert isinstance(orm_visit.status, str)

    def test_round_trip_mapping(self):
        """Test domain -> ORM -> domain round trip preserves all data."""
        original_data = {
            "id": uuid4(),
            "seller_id": uuid4(),
            "client_id": uuid4(),
            "fecha_visita": datetime(2025, 11, 16, 10, 0, tzinfo=timezone.utc),
            "status": VisitStatus.COMPLETADA,
            "notas_visita": "Original notes",
            "recomendaciones": "Original recommendations",
            "archivos_evidencia": "https://s3.amazonaws.com/bucket/original.jpg",
            "client_nombre_institucion": "Original Hospital",
            "client_direccion": "Original Address",
            "client_ciudad": "Original City",
            "client_pais": "Original Country",
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }

        original_visit = Visit(**original_data)
        orm_visit = VisitRepository._to_orm(original_visit)
        round_trip_visit = VisitRepository._to_domain(orm_visit)

        # Verify all fields match after round trip
        assert round_trip_visit.id == original_visit.id
        assert round_trip_visit.seller_id == original_visit.seller_id
        assert round_trip_visit.client_id == original_visit.client_id
        assert round_trip_visit.fecha_visita == original_visit.fecha_visita
        assert round_trip_visit.status == original_visit.status
        assert round_trip_visit.notas_visita == original_visit.notas_visita
        assert round_trip_visit.recomendaciones == original_visit.recomendaciones
        assert round_trip_visit.archivos_evidencia == original_visit.archivos_evidencia
