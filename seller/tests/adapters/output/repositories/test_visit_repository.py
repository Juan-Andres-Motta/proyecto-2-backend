"""Unit tests for VisitRepository."""
import pytest
from uuid import uuid4
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession

from src.adapters.output.repositories.visit_repository import VisitRepository
from src.domain.entities.visit import Visit, VisitStatus
from src.infrastructure.database.models import Visit as ORMVisit


@pytest.fixture
def mock_session():
    """Mock AsyncSession."""
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def repository(mock_session):
    """VisitRepository instance."""
    return VisitRepository(session=mock_session)


@pytest.fixture
def seller_id():
    """Fixed seller ID."""
    return uuid4()


@pytest.fixture
def client_id():
    """Fixed client ID."""
    return uuid4()


@pytest.fixture
def visit_id():
    """Fixed visit ID."""
    return uuid4()


@pytest.fixture
def visit_domain_entity(seller_id, client_id, visit_id):
    """Mock Visit domain entity."""
    future_date = datetime.now(timezone.utc) + timedelta(days=2)
    return Visit(
        id=visit_id,
        seller_id=seller_id,
        client_id=client_id,
        fecha_visita=future_date,
        status=VisitStatus.PROGRAMADA,
        notas_visita="Test notes",
        recomendaciones=None,
        archivos_evidencia=None,
        client_nombre_institucion="Hospital Central",
        client_direccion="Calle 123",
        client_ciudad="Bogotá",
        client_pais="Colombia",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def orm_visit_entity(seller_id, client_id, visit_id):
    """Mock ORM Visit entity."""
    future_date = datetime.now(timezone.utc) + timedelta(days=2)
    return ORMVisit(
        id=visit_id,
        seller_id=seller_id,
        client_id=client_id,
        fecha_visita=future_date,
        status="programada",
        notas_visita="Test notes",
        recomendaciones=None,
        archivos_evidencia=None,
        client_nombre_institucion="Hospital Central",
        client_direccion="Calle 123",
        client_ciudad="Bogotá",
        client_pais="Colombia",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


class TestVisitRepositoryCreate:
    """Test create method."""

    @pytest.mark.asyncio
    async def test_create_visit_success(self, repository, mock_session, visit_domain_entity, orm_visit_entity):
        """Test successfully creating a visit."""
        # Mock session methods
        mock_result = MagicMock()
        mock_session.flush = AsyncMock()
        mock_session.refresh = AsyncMock()
        mock_session.add = MagicMock()

        # Configure mock to return ORM entity after refresh
        mock_session.refresh.side_effect = lambda entity: setattr(
            entity, "id", orm_visit_entity.id
        )

        result = await repository.create(visit_domain_entity, mock_session)

        # Verify session methods were called
        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()
        mock_session.refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_visit_failure(self, repository, mock_session, visit_domain_entity):
        """Test create visit with database error."""
        mock_session.flush = AsyncMock(side_effect=Exception("Database error"))

        with pytest.raises(Exception) as exc_info:
            await repository.create(visit_domain_entity, mock_session)

        assert "Database error" in str(exc_info.value)


class TestVisitRepositoryFindById:
    """Test find_by_id method."""

    @pytest.mark.asyncio
    async def test_find_visit_by_id_success(self, repository, mock_session, visit_id, orm_visit_entity):
        """Test successfully finding a visit by ID."""
        # Setup mock result
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = orm_visit_entity
        mock_session.execute = AsyncMock(return_value=mock_result)

        result = await repository.find_by_id(visit_id, mock_session)

        assert result is not None
        assert result.id == visit_id
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_find_visit_by_id_not_found(self, repository, mock_session, visit_id):
        """Test finding non-existent visit returns None."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = None
        mock_session.execute = AsyncMock(return_value=mock_result)

        result = await repository.find_by_id(visit_id, mock_session)

        assert result is None

    @pytest.mark.asyncio
    async def test_find_visit_by_id_database_error(self, repository, mock_session, visit_id):
        """Test find_by_id with database error."""
        mock_session.execute = AsyncMock(side_effect=Exception("Database error"))

        with pytest.raises(Exception) as exc_info:
            await repository.find_by_id(visit_id, mock_session)

        assert "Database error" in str(exc_info.value)


class TestVisitRepositoryGetVisitsByDate:
    """Test get_visits_by_date method."""

    @pytest.mark.asyncio
    async def test_get_visits_by_date_single_visit(
        self, repository, mock_session, seller_id, orm_visit_entity
    ):
        """Test getting visits for a specific date with one visit."""
        date = datetime.now(timezone.utc) + timedelta(days=2)

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [orm_visit_entity]
        mock_session.execute = AsyncMock(return_value=mock_result)

        result = await repository.get_visits_by_date(seller_id, date, mock_session)

        assert len(result) == 1
        assert result[0].id == orm_visit_entity.id
        assert result[0].seller_id == seller_id

    @pytest.mark.asyncio
    async def test_get_visits_by_date_multiple_visits(
        self, repository, mock_session, seller_id, orm_visit_entity
    ):
        """Test getting multiple visits for a specific date."""
        date = datetime.now(timezone.utc) + timedelta(days=2)

        # Create second visit at different time on same date
        orm_visit_entity_2 = ORMVisit(
            id=uuid4(),
            seller_id=seller_id,
            client_id=uuid4(),
            fecha_visita=orm_visit_entity.fecha_visita + timedelta(hours=2),
            status="programada",
            notas_visita="Test notes 2",
            recomendaciones=None,
            archivos_evidencia=None,
            client_nombre_institucion="Hospital 2",
            client_direccion="Calle 456",
            client_ciudad="Medellín",
            client_pais="Colombia",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [
            orm_visit_entity,
            orm_visit_entity_2,
        ]
        mock_session.execute = AsyncMock(return_value=mock_result)

        result = await repository.get_visits_by_date(seller_id, date, mock_session)

        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_get_visits_by_date_empty_result(self, repository, mock_session, seller_id):
        """Test getting visits with no results."""
        date = datetime.now(timezone.utc) + timedelta(days=2)

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute = AsyncMock(return_value=mock_result)

        result = await repository.get_visits_by_date(seller_id, date, mock_session)

        assert result == []

    @pytest.mark.asyncio
    async def test_get_visits_by_date_database_error(self, repository, mock_session, seller_id):
        """Test get_visits_by_date with database error."""
        date = datetime.now(timezone.utc) + timedelta(days=2)
        mock_session.execute = AsyncMock(side_effect=Exception("Database error"))

        with pytest.raises(Exception) as exc_info:
            await repository.get_visits_by_date(seller_id, date, mock_session)

        assert "Database error" in str(exc_info.value)


class TestVisitRepositoryHasConflictingVisit:
    """Test has_conflicting_visit method."""

    @pytest.mark.asyncio
    async def test_has_conflicting_visit_found(
        self, repository, mock_session, seller_id, orm_visit_entity
    ):
        """Test finding a conflicting visit."""
        fecha_visita = datetime.now(timezone.utc) + timedelta(days=2)

        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = orm_visit_entity
        mock_session.execute = AsyncMock(return_value=mock_result)

        result = await repository.has_conflicting_visit(seller_id, fecha_visita, mock_session)

        assert result is not None
        assert result.id == orm_visit_entity.id

    @pytest.mark.asyncio
    async def test_has_conflicting_visit_not_found(
        self, repository, mock_session, seller_id
    ):
        """Test no conflicting visit found."""
        fecha_visita = datetime.now(timezone.utc) + timedelta(days=2)

        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = None
        mock_session.execute = AsyncMock(return_value=mock_result)

        result = await repository.has_conflicting_visit(seller_id, fecha_visita, mock_session)

        assert result is None

    @pytest.mark.asyncio
    async def test_has_conflicting_visit_within_180_minutes_before(
        self, repository, mock_session, seller_id, orm_visit_entity
    ):
        """Test conflicting visit within 180 minutes before."""
        # Existing visit at specific time
        existing_time = datetime.now(timezone.utc) + timedelta(days=2, hours=10)
        orm_visit_entity.fecha_visita = existing_time

        # New visit 100 minutes after (within conflict window)
        new_time = existing_time + timedelta(minutes=100)

        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = orm_visit_entity
        mock_session.execute = AsyncMock(return_value=mock_result)

        result = await repository.has_conflicting_visit(seller_id, new_time, mock_session)

        assert result is not None

    @pytest.mark.asyncio
    async def test_has_conflicting_visit_within_180_minutes_after(
        self, repository, mock_session, seller_id, orm_visit_entity
    ):
        """Test conflicting visit within 180 minutes after."""
        # Existing visit at specific time
        existing_time = datetime.now(timezone.utc) + timedelta(days=2, hours=10)
        orm_visit_entity.fecha_visita = existing_time

        # New visit 100 minutes before (within conflict window)
        new_time = existing_time - timedelta(minutes=100)

        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = orm_visit_entity
        mock_session.execute = AsyncMock(return_value=mock_result)

        result = await repository.has_conflicting_visit(seller_id, new_time, mock_session)

        assert result is not None

    @pytest.mark.asyncio
    async def test_has_conflicting_visit_outside_180_minutes_before(
        self, repository, mock_session, seller_id
    ):
        """Test no conflict when visit is more than 180 minutes before."""
        # Existing visit at specific time
        existing_time = datetime.now(timezone.utc) + timedelta(days=2, hours=10)

        # New visit 200 minutes after (outside conflict window)
        new_time = existing_time + timedelta(minutes=200)

        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = None
        mock_session.execute = AsyncMock(return_value=mock_result)

        result = await repository.has_conflicting_visit(seller_id, new_time, mock_session)

        assert result is None

    @pytest.mark.asyncio
    async def test_has_conflicting_visit_outside_180_minutes_after(
        self, repository, mock_session, seller_id
    ):
        """Test no conflict when visit is more than 180 minutes after."""
        # Existing visit at specific time
        existing_time = datetime.now(timezone.utc) + timedelta(days=2, hours=10)

        # New visit 200 minutes before (outside conflict window)
        new_time = existing_time - timedelta(minutes=200)

        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = None
        mock_session.execute = AsyncMock(return_value=mock_result)

        result = await repository.has_conflicting_visit(seller_id, new_time, mock_session)

        assert result is None

    @pytest.mark.asyncio
    async def test_has_conflicting_visit_database_error(
        self, repository, mock_session, seller_id
    ):
        """Test has_conflicting_visit with database error."""
        fecha_visita = datetime.now(timezone.utc) + timedelta(days=2)
        mock_session.execute = AsyncMock(side_effect=Exception("Database error"))

        with pytest.raises(Exception) as exc_info:
            await repository.has_conflicting_visit(seller_id, fecha_visita, mock_session)

        assert "Database error" in str(exc_info.value)


class TestVisitRepositoryMappingMethods:
    """Test ORM to domain entity mapping methods."""

    def test_to_domain_converts_orm_to_domain(self, repository, orm_visit_entity):
        """Test _to_domain correctly converts ORM entity to domain entity."""
        domain_visit = repository._to_domain(orm_visit_entity)

        assert domain_visit.id == orm_visit_entity.id
        assert domain_visit.seller_id == orm_visit_entity.seller_id
        assert domain_visit.client_id == orm_visit_entity.client_id
        assert domain_visit.fecha_visita == orm_visit_entity.fecha_visita
        assert domain_visit.status == VisitStatus(orm_visit_entity.status)
        assert domain_visit.notas_visita == orm_visit_entity.notas_visita
        assert domain_visit.client_nombre_institucion == orm_visit_entity.client_nombre_institucion

    def test_to_orm_converts_domain_to_orm(self, repository, visit_domain_entity):
        """Test _to_orm correctly converts domain entity to ORM entity."""
        orm_visit = repository._to_orm(visit_domain_entity)

        assert orm_visit.id == visit_domain_entity.id
        assert orm_visit.seller_id == visit_domain_entity.seller_id
        assert orm_visit.client_id == visit_domain_entity.client_id
        assert orm_visit.fecha_visita == visit_domain_entity.fecha_visita
        assert orm_visit.status == visit_domain_entity.status.value
        assert orm_visit.notas_visita == visit_domain_entity.notas_visita

    def test_to_domain_completada_status(self, repository, orm_visit_entity):
        """Test mapping COMPLETADA status."""
        orm_visit_entity.status = "completada"

        domain_visit = repository._to_domain(orm_visit_entity)

        assert domain_visit.status == VisitStatus.COMPLETADA

    def test_to_domain_cancelada_status(self, repository, orm_visit_entity):
        """Test mapping CANCELADA status."""
        orm_visit_entity.status = "cancelada"

        domain_visit = repository._to_domain(orm_visit_entity)

        assert domain_visit.status == VisitStatus.CANCELADA

    def test_to_orm_preserves_all_fields(self, repository, visit_domain_entity):
        """Test _to_orm preserves all fields from domain entity."""
        orm_visit = repository._to_orm(visit_domain_entity)

        assert orm_visit.recomendaciones == visit_domain_entity.recomendaciones
        assert orm_visit.archivos_evidencia == visit_domain_entity.archivos_evidencia
        assert orm_visit.client_direccion == visit_domain_entity.client_direccion
        assert orm_visit.client_ciudad == visit_domain_entity.client_ciudad
        assert orm_visit.client_pais == visit_domain_entity.client_pais
        assert orm_visit.created_at == visit_domain_entity.created_at
        assert orm_visit.updated_at == visit_domain_entity.updated_at


class TestVisitRepositoryUpdate:
    """Test update method."""

    @pytest.mark.asyncio
    async def test_update_visit_success(self, repository, mock_session, visit_domain_entity, orm_visit_entity):
        """Test successfully updating a visit."""
        from dataclasses import replace

        # Setup: Mock find to return the existing ORM entity
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = orm_visit_entity
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.flush = AsyncMock()
        mock_session.refresh = AsyncMock()

        # Create a domain entity with updated fields
        updated_visit = replace(
            visit_domain_entity,
            status=VisitStatus.COMPLETADA,
            recomendaciones="Test recommendation",
            archivos_evidencia="https://s3.amazonaws.com/test.jpg",
        )

        result = await repository.update(updated_visit, mock_session)

        # Verify session methods were called
        mock_session.execute.assert_called_once()
        mock_session.flush.assert_called_once()
        mock_session.refresh.assert_called_once()
        assert result is not None

    @pytest.mark.asyncio
    async def test_update_visit_not_found(self, repository, mock_session, visit_domain_entity):
        """Test updating non-existent visit raises error."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = None
        mock_session.execute = AsyncMock(return_value=mock_result)

        with pytest.raises(ValueError) as exc_info:
            await repository.update(visit_domain_entity, mock_session)

        assert "not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_update_visit_updates_status(self, repository, mock_session, orm_visit_entity, visit_domain_entity):
        """Test that update correctly updates visit status."""
        from dataclasses import replace

        # Setup: Mock find to return the existing ORM entity
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = orm_visit_entity
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.flush = AsyncMock()
        mock_session.refresh = AsyncMock()

        # Create updated visit with new status
        updated_visit = replace(
            visit_domain_entity,
            status=VisitStatus.COMPLETADA
        )

        await repository.update(updated_visit, mock_session)

        # Verify status was updated in ORM object
        assert orm_visit_entity.status == VisitStatus.COMPLETADA.value

    @pytest.mark.asyncio
    async def test_update_visit_updates_recomendaciones(self, repository, mock_session, orm_visit_entity, visit_domain_entity):
        """Test that update correctly updates recomendaciones."""
        # Setup: Mock find to return the existing ORM entity
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = orm_visit_entity
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.flush = AsyncMock()
        mock_session.refresh = AsyncMock()

        from dataclasses import replace

        new_recomendaciones = "New recommendation text"
        updated_visit = replace(
            visit_domain_entity,
            recomendaciones=new_recomendaciones
        )

        await repository.update(updated_visit, mock_session)

        # Verify recomendaciones was updated in ORM object
        assert orm_visit_entity.recomendaciones == new_recomendaciones

    @pytest.mark.asyncio
    async def test_update_visit_updates_archivos_evidencia(self, repository, mock_session, orm_visit_entity, visit_domain_entity):
        """Test that update correctly updates archivos_evidencia."""
        from dataclasses import replace

        # Setup: Mock find to return the existing ORM entity
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = orm_visit_entity
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.flush = AsyncMock()
        mock_session.refresh = AsyncMock()

        s3_url = "https://s3.amazonaws.com/bucket/photo.jpg"
        updated_visit = replace(
            visit_domain_entity,
            archivos_evidencia=s3_url
        )

        await repository.update(updated_visit, mock_session)

        # Verify archivos_evidencia was updated in ORM object
        assert orm_visit_entity.archivos_evidencia == s3_url

    @pytest.mark.asyncio
    async def test_update_visit_updates_timestamp(self, repository, mock_session, orm_visit_entity, visit_domain_entity):
        """Test that update correctly updates updated_at timestamp."""
        from dataclasses import replace

        # Setup: Mock find to return the existing ORM entity
        old_timestamp = orm_visit_entity.updated_at
        new_timestamp = datetime.now(timezone.utc)

        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = orm_visit_entity
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.flush = AsyncMock()
        mock_session.refresh = AsyncMock()

        updated_visit = replace(
            visit_domain_entity,
            updated_at=new_timestamp
        )

        await repository.update(updated_visit, mock_session)

        # Verify timestamp was updated in ORM object
        assert orm_visit_entity.updated_at == new_timestamp

    @pytest.mark.asyncio
    async def test_update_visit_updates_notas_visita(self, repository, mock_session, orm_visit_entity, visit_domain_entity):
        """Test that update correctly updates notas_visita."""
        from dataclasses import replace

        # Setup: Mock find to return the existing ORM entity
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = orm_visit_entity
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.flush = AsyncMock()
        mock_session.refresh = AsyncMock()

        new_notes = "Updated visit notes"
        updated_visit = replace(
            visit_domain_entity,
            notas_visita=new_notes
        )

        await repository.update(updated_visit, mock_session)

        # Verify notas_visita was updated in ORM object
        assert orm_visit_entity.notas_visita == new_notes

    @pytest.mark.asyncio
    async def test_update_visit_database_error(self, repository, mock_session, visit_domain_entity):
        """Test update with database error."""
        mock_session.execute = AsyncMock(side_effect=Exception("Database error"))

        with pytest.raises(Exception) as exc_info:
            await repository.update(visit_domain_entity, mock_session)

        assert "Database error" in str(exc_info.value)


class TestVisitRepositoryFindBySellerAndDateRange:
    """Test find_by_seller_and_date_range method."""

    @pytest.mark.asyncio
    async def test_find_by_date_range_with_both_dates(self, repository, mock_session, seller_id, orm_visit_entity):
        """Test finding visits with both date_from and date_to."""
        date_from = (datetime.now(timezone.utc) - timedelta(days=7)).date()
        date_to = (datetime.now(timezone.utc) + timedelta(days=7)).date()

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [orm_visit_entity]
        mock_session.execute = AsyncMock(return_value=mock_result)

        result = await repository.find_by_seller_and_date_range(
            seller_id=seller_id,
            date_from=date_from,
            date_to=date_to,
            page=1,
            page_size=10,
            session=mock_session,
        )

        assert len(result) == 1
        assert result[0].seller_id == seller_id
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_find_by_date_range_with_date_to_only(self, repository, mock_session, seller_id, orm_visit_entity):
        """Test finding visits with date_to only (PAST ordering - descending)."""
        date_to = (datetime.now(timezone.utc) - timedelta(days=7)).date()

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [orm_visit_entity]
        mock_session.execute = AsyncMock(return_value=mock_result)

        result = await repository.find_by_seller_and_date_range(
            seller_id=seller_id,
            date_from=None,
            date_to=date_to,
            page=1,
            page_size=10,
            session=mock_session,
        )

        assert len(result) == 1
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_find_by_date_range_with_date_from_only(self, repository, mock_session, seller_id, orm_visit_entity):
        """Test finding visits with date_from only (ascending order)."""
        date_from = (datetime.now(timezone.utc) - timedelta(days=7)).date()

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [orm_visit_entity]
        mock_session.execute = AsyncMock(return_value=mock_result)

        result = await repository.find_by_seller_and_date_range(
            seller_id=seller_id,
            date_from=date_from,
            date_to=None,
            page=1,
            page_size=10,
            session=mock_session,
        )

        assert len(result) == 1
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_find_by_date_range_with_no_dates(self, repository, mock_session, seller_id, orm_visit_entity):
        """Test finding visits with no date filters."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [orm_visit_entity]
        mock_session.execute = AsyncMock(return_value=mock_result)

        result = await repository.find_by_seller_and_date_range(
            seller_id=seller_id,
            date_from=None,
            date_to=None,
            page=1,
            page_size=10,
            session=mock_session,
        )

        assert len(result) == 1
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_find_by_date_range_with_client_name_filter(self, repository, mock_session, seller_id, orm_visit_entity):
        """Test finding visits with client name filter."""
        date_from = (datetime.now(timezone.utc) - timedelta(days=7)).date()
        date_to = (datetime.now(timezone.utc) + timedelta(days=7)).date()

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [orm_visit_entity]
        mock_session.execute = AsyncMock(return_value=mock_result)

        result = await repository.find_by_seller_and_date_range(
            seller_id=seller_id,
            date_from=date_from,
            date_to=date_to,
            page=1,
            page_size=10,
            session=mock_session,
            client_name="Hospital",
        )

        assert len(result) == 1
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_find_by_date_range_pagination(self, repository, mock_session, seller_id, orm_visit_entity):
        """Test pagination in find_by_date_range."""
        date_from = (datetime.now(timezone.utc) - timedelta(days=7)).date()
        date_to = (datetime.now(timezone.utc) + timedelta(days=7)).date()

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [orm_visit_entity]
        mock_session.execute = AsyncMock(return_value=mock_result)

        # Test page 2 with page_size 5
        result = await repository.find_by_seller_and_date_range(
            seller_id=seller_id,
            date_from=date_from,
            date_to=date_to,
            page=2,
            page_size=5,
            session=mock_session,
        )

        assert len(result) == 1
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_find_by_date_range_empty_result(self, repository, mock_session, seller_id):
        """Test finding visits with no matching results."""
        date_from = (datetime.now(timezone.utc) - timedelta(days=7)).date()
        date_to = (datetime.now(timezone.utc) + timedelta(days=7)).date()

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute = AsyncMock(return_value=mock_result)

        result = await repository.find_by_seller_and_date_range(
            seller_id=seller_id,
            date_from=date_from,
            date_to=date_to,
            page=1,
            page_size=10,
            session=mock_session,
        )

        assert result == []
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_find_by_date_range_multiple_visits(self, repository, mock_session, seller_id, orm_visit_entity):
        """Test finding multiple visits."""
        date_from = (datetime.now(timezone.utc) - timedelta(days=7)).date()
        date_to = (datetime.now(timezone.utc) + timedelta(days=7)).date()

        orm_visit_entity_2 = ORMVisit(
            id=uuid4(),
            seller_id=seller_id,
            client_id=uuid4(),
            fecha_visita=orm_visit_entity.fecha_visita + timedelta(hours=2),
            status="programada",
            notas_visita="Test notes 2",
            recomendaciones=None,
            archivos_evidencia=None,
            client_nombre_institucion="Hospital 2",
            client_direccion="Calle 456",
            client_ciudad="Medellín",
            client_pais="Colombia",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [orm_visit_entity, orm_visit_entity_2]
        mock_session.execute = AsyncMock(return_value=mock_result)

        result = await repository.find_by_seller_and_date_range(
            seller_id=seller_id,
            date_from=date_from,
            date_to=date_to,
            page=1,
            page_size=10,
            session=mock_session,
        )

        assert len(result) == 2
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_find_by_date_range_database_error(self, repository, mock_session, seller_id):
        """Test find_by_date_range with database error."""
        date_from = (datetime.now(timezone.utc) - timedelta(days=7)).date()
        date_to = (datetime.now(timezone.utc) + timedelta(days=7)).date()

        mock_session.execute = AsyncMock(side_effect=Exception("Database error"))

        with pytest.raises(Exception) as exc_info:
            await repository.find_by_seller_and_date_range(
                seller_id=seller_id,
                date_from=date_from,
                date_to=date_to,
                page=1,
                page_size=10,
                session=mock_session,
            )

        assert "Database error" in str(exc_info.value)


class TestVisitRepositoryCountBySellerAndDateRange:
    """Test count_by_seller_and_date_range method."""

    @pytest.mark.asyncio
    async def test_count_with_both_dates(self, repository, mock_session, seller_id):
        """Test counting visits with both date_from and date_to."""
        date_from = (datetime.now(timezone.utc) - timedelta(days=7)).date()
        date_to = (datetime.now(timezone.utc) + timedelta(days=7)).date()

        mock_result = MagicMock()
        mock_result.scalar.return_value = 5
        mock_session.execute = AsyncMock(return_value=mock_result)

        count = await repository.count_by_seller_and_date_range(
            seller_id=seller_id,
            date_from=date_from,
            date_to=date_to,
            session=mock_session,
        )

        assert count == 5
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_count_with_date_to_only(self, repository, mock_session, seller_id):
        """Test counting visits with date_to only."""
        date_to = (datetime.now(timezone.utc) - timedelta(days=7)).date()

        mock_result = MagicMock()
        mock_result.scalar.return_value = 3
        mock_session.execute = AsyncMock(return_value=mock_result)

        count = await repository.count_by_seller_and_date_range(
            seller_id=seller_id,
            date_from=None,
            date_to=date_to,
            session=mock_session,
        )

        assert count == 3
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_count_with_date_from_only(self, repository, mock_session, seller_id):
        """Test counting visits with date_from only."""
        date_from = (datetime.now(timezone.utc) - timedelta(days=7)).date()

        mock_result = MagicMock()
        mock_result.scalar.return_value = 8
        mock_session.execute = AsyncMock(return_value=mock_result)

        count = await repository.count_by_seller_and_date_range(
            seller_id=seller_id,
            date_from=date_from,
            date_to=None,
            session=mock_session,
        )

        assert count == 8
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_count_with_no_dates(self, repository, mock_session, seller_id):
        """Test counting visits with no date filters."""
        mock_result = MagicMock()
        mock_result.scalar.return_value = 15
        mock_session.execute = AsyncMock(return_value=mock_result)

        count = await repository.count_by_seller_and_date_range(
            seller_id=seller_id,
            date_from=None,
            date_to=None,
            session=mock_session,
        )

        assert count == 15
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_count_with_client_name_filter(self, repository, mock_session, seller_id):
        """Test counting visits with client name filter."""
        date_from = (datetime.now(timezone.utc) - timedelta(days=7)).date()
        date_to = (datetime.now(timezone.utc) + timedelta(days=7)).date()

        mock_result = MagicMock()
        mock_result.scalar.return_value = 2
        mock_session.execute = AsyncMock(return_value=mock_result)

        count = await repository.count_by_seller_and_date_range(
            seller_id=seller_id,
            date_from=date_from,
            date_to=date_to,
            session=mock_session,
            client_name="Hospital",
        )

        assert count == 2
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_count_zero_results(self, repository, mock_session, seller_id):
        """Test counting visits with zero results."""
        date_from = (datetime.now(timezone.utc) - timedelta(days=7)).date()
        date_to = (datetime.now(timezone.utc) + timedelta(days=7)).date()

        mock_result = MagicMock()
        mock_result.scalar.return_value = 0
        mock_session.execute = AsyncMock(return_value=mock_result)

        count = await repository.count_by_seller_and_date_range(
            seller_id=seller_id,
            date_from=date_from,
            date_to=date_to,
            session=mock_session,
        )

        assert count == 0
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_count_with_none_result(self, repository, mock_session, seller_id):
        """Test counting visits when scalar returns None (defaults to 0)."""
        date_from = (datetime.now(timezone.utc) - timedelta(days=7)).date()
        date_to = (datetime.now(timezone.utc) + timedelta(days=7)).date()

        mock_result = MagicMock()
        mock_result.scalar.return_value = None
        mock_session.execute = AsyncMock(return_value=mock_result)

        count = await repository.count_by_seller_and_date_range(
            seller_id=seller_id,
            date_from=date_from,
            date_to=date_to,
            session=mock_session,
        )

        assert count == 0
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_count_database_error(self, repository, mock_session, seller_id):
        """Test count_by_date_range with database error."""
        date_from = (datetime.now(timezone.utc) - timedelta(days=7)).date()
        date_to = (datetime.now(timezone.utc) + timedelta(days=7)).date()

        mock_session.execute = AsyncMock(side_effect=Exception("Database error"))

        with pytest.raises(Exception) as exc_info:
            await repository.count_by_seller_and_date_range(
                seller_id=seller_id,
                date_from=date_from,
                date_to=date_to,
                session=mock_session,
            )

        assert "Database error" in str(exc_info.value)
