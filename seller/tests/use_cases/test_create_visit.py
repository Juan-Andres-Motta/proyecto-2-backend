"""Tests for CreateVisitUseCase."""
import pytest
from datetime import datetime, timedelta, timezone
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock

from src.application.use_cases.create_visit import CreateVisitUseCase
from src.domain.entities.visit import Visit, VisitStatus
from src.domain.exceptions import VisitTimeConflictError, InvalidVisitDateError


@pytest.fixture
def visit_repository():
    """Mock visit repository."""
    return AsyncMock()


@pytest.fixture
def create_visit_use_case(visit_repository):
    """Create visit use case instance."""
    return CreateVisitUseCase(visit_repository)


@pytest.fixture
def seller_id():
    """Fixed seller ID."""
    return uuid4()


@pytest.fixture
def client_id():
    """Fixed client ID."""
    return uuid4()


@pytest.fixture
def future_date():
    """Future date for visit."""
    return datetime.now(timezone.utc) + timedelta(days=2)


@pytest.fixture
def session():
    """Mock database session."""
    return MagicMock()


class TestCreateVisitUseCase:
    """Test CreateVisitUseCase."""

    @pytest.mark.asyncio
    async def test_execute_successfully_creates_visit(
        self,
        create_visit_use_case,
        visit_repository,
        seller_id,
        client_id,
        future_date,
        session,
    ):
        """Test successfully creating a visit."""
        # Setup
        visit_repository.has_conflicting_visit.return_value = None
        created_visit = Visit(
            id=uuid4(),
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
        visit_repository.create.return_value = created_visit

        # Execute
        result = await create_visit_use_case.execute(
            seller_id=seller_id,
            client_id=client_id,
            fecha_visita=future_date,
            notas_visita="Test notes",
            client_nombre_institucion="Hospital Central",
            client_direccion="Calle 123",
            client_ciudad="Bogotá",
            client_pais="Colombia",
            session=session,
        )

        # Assert
        assert result.id == created_visit.id
        assert result.seller_id == seller_id
        assert result.client_id == client_id
        assert result.status == VisitStatus.PROGRAMADA
        assert result.notas_visita == "Test notes"
        assert result.client_nombre_institucion == "Hospital Central"
        visit_repository.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_validates_future_date(
        self,
        create_visit_use_case,
        seller_id,
        client_id,
        session,
    ):
        """Test that past dates are rejected."""
        past_date = datetime.now(timezone.utc) - timedelta(days=1)

        with pytest.raises(InvalidVisitDateError):
            await create_visit_use_case.execute(
                seller_id=seller_id,
                client_id=client_id,
                fecha_visita=past_date,
                notas_visita=None,
                client_nombre_institucion="Hospital",
                client_direccion="Address",
                client_ciudad="City",
                client_pais="Country",
                session=session,
            )

    @pytest.mark.asyncio
    async def test_execute_detects_time_conflicts(
        self,
        create_visit_use_case,
        visit_repository,
        seller_id,
        client_id,
        future_date,
        session,
    ):
        """Test that time conflicts are detected."""
        # Setup conflicting visit
        conflicting_visit = Visit(
            id=uuid4(),
            seller_id=seller_id,
            client_id=client_id,
            fecha_visita=future_date,
            status=VisitStatus.PROGRAMADA,
            notas_visita=None,
            recomendaciones=None,
            archivos_evidencia=None,
            client_nombre_institucion="Other Hospital",
            client_direccion="Other Address",
            client_ciudad="Other City",
            client_pais="Other Country",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        visit_repository.has_conflicting_visit.return_value = conflicting_visit

        # Execute and assert
        with pytest.raises(VisitTimeConflictError):
            await create_visit_use_case.execute(
                seller_id=seller_id,
                client_id=client_id,
                fecha_visita=future_date,
                notas_visita=None,
                client_nombre_institucion="Hospital Central",
                client_direccion="Calle 123",
                client_ciudad="Bogotá",
                client_pais="Colombia",
                session=session,
            )

    @pytest.mark.asyncio
    async def test_execute_with_no_notes(
        self,
        create_visit_use_case,
        visit_repository,
        seller_id,
        client_id,
        future_date,
        session,
    ):
        """Test creating visit without notes."""
        # Setup
        visit_repository.has_conflicting_visit.return_value = None
        created_visit = Visit(
            id=uuid4(),
            seller_id=seller_id,
            client_id=client_id,
            fecha_visita=future_date,
            status=VisitStatus.PROGRAMADA,
            notas_visita=None,
            recomendaciones=None,
            archivos_evidencia=None,
            client_nombre_institucion="Hospital Central",
            client_direccion="Calle 123",
            client_ciudad="Bogotá",
            client_pais="Colombia",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        visit_repository.create.return_value = created_visit

        # Execute
        result = await create_visit_use_case.execute(
            seller_id=seller_id,
            client_id=client_id,
            fecha_visita=future_date,
            notas_visita=None,
            client_nombre_institucion="Hospital Central",
            client_direccion="Calle 123",
            client_ciudad="Bogotá",
            client_pais="Colombia",
            session=session,
        )

        # Assert
        assert result.notas_visita is None

    @pytest.mark.asyncio
    async def test_execute_calls_has_conflicting_visit_with_correct_params(
        self,
        create_visit_use_case,
        visit_repository,
        seller_id,
        client_id,
        future_date,
        session,
    ):
        """Test that has_conflicting_visit is called with correct parameters."""
        # Setup
        visit_repository.has_conflicting_visit.return_value = None
        created_visit = Visit(
            id=uuid4(),
            seller_id=seller_id,
            client_id=client_id,
            fecha_visita=future_date,
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
        visit_repository.create.return_value = created_visit

        # Execute
        await create_visit_use_case.execute(
            seller_id=seller_id,
            client_id=client_id,
            fecha_visita=future_date,
            notas_visita=None,
            client_nombre_institucion="Hospital",
            client_direccion="Address",
            client_ciudad="City",
            client_pais="Country",
            session=session,
        )

        # Assert
        visit_repository.has_conflicting_visit.assert_called_once_with(
            seller_id=seller_id,
            fecha_visita=future_date,
            session=session,
        )

    @pytest.mark.asyncio
    async def test_execute_creates_visit_with_correct_denormalized_data(
        self,
        create_visit_use_case,
        visit_repository,
        seller_id,
        client_id,
        future_date,
        session,
    ):
        """Test that visit is created with correct denormalized client data."""
        # Setup
        visit_repository.has_conflicting_visit.return_value = None
        created_visit = Visit(
            id=uuid4(),
            seller_id=seller_id,
            client_id=client_id,
            fecha_visita=future_date,
            status=VisitStatus.PROGRAMADA,
            notas_visita="Notes",
            recomendaciones=None,
            archivos_evidencia=None,
            client_nombre_institucion="Specific Hospital",
            client_direccion="Specific Address",
            client_ciudad="Specific City",
            client_pais="Specific Country",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        visit_repository.create.return_value = created_visit

        # Execute
        result = await create_visit_use_case.execute(
            seller_id=seller_id,
            client_id=client_id,
            fecha_visita=future_date,
            notas_visita="Notes",
            client_nombre_institucion="Specific Hospital",
            client_direccion="Specific Address",
            client_ciudad="Specific City",
            client_pais="Specific Country",
            session=session,
        )

        # Assert
        assert result.client_nombre_institucion == "Specific Hospital"
        assert result.client_direccion == "Specific Address"
        assert result.client_ciudad == "Specific City"
        assert result.client_pais == "Specific Country"

    @pytest.mark.asyncio
    async def test_execute_validates_date_at_least_one_day_ahead(
        self,
        create_visit_use_case,
        seller_id,
        client_id,
        session,
    ):
        """Test that dates less than 1 day ahead are rejected."""
        # Date is less than 1 day ahead
        almost_future_date = datetime.now(timezone.utc) + timedelta(hours=12)

        with pytest.raises(InvalidVisitDateError):
            await create_visit_use_case.execute(
                seller_id=seller_id,
                client_id=client_id,
                fecha_visita=almost_future_date,
                notas_visita=None,
                client_nombre_institucion="Hospital",
                client_direccion="Address",
                client_ciudad="City",
                client_pais="Country",
                session=session,
            )
