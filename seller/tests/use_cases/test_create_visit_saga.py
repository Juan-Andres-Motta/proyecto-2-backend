"""Unit tests for CreateVisitSaga use case."""
import pytest
from datetime import datetime, timezone, timedelta
from uuid import uuid4, UUID
from unittest.mock import AsyncMock, MagicMock

from src.application.use_cases.create_visit_saga import CreateVisitSaga
from src.application.ports.client_service_port import ClientDTO
from src.domain.entities.visit import Visit, VisitStatus
from src.domain.exceptions import (
    VisitNotFoundError,
    ClientAssignedToOtherSellerError,
    InvalidVisitDateError,
    VisitTimeConflictError,
)


@pytest.fixture
def mock_visit_repository():
    """Mock visit repository."""
    return AsyncMock()


@pytest.fixture
def mock_client_service():
    """Mock client service."""
    return AsyncMock()


@pytest.fixture
def mock_session():
    """Mock database session."""
    return AsyncMock()


@pytest.fixture
def saga(mock_visit_repository, mock_client_service):
    """CreateVisitSaga instance with mocked dependencies."""
    return CreateVisitSaga(
        visit_repository=mock_visit_repository,
        client_service=mock_client_service,
    )


@pytest.fixture
def future_date():
    """Valid future date (2 days from now)."""
    return datetime.now(timezone.utc) + timedelta(days=2)


@pytest.fixture
def unassigned_client():
    """Mock unassigned client."""
    return ClientDTO(
        id=uuid4(),
        vendedor_asignado_id=None,
        nombre_institucion="Hospital Central",
        direccion="Calle 123",
        ciudad="Bogotá",
        pais="Colombia",
    )


class TestCreateVisitSagaSuccess:
    """Test successful visit creation scenarios."""

    @pytest.mark.asyncio
    async def test_create_visit_with_unassigned_client(
        self, saga, mock_client_service, mock_visit_repository, mock_session, unassigned_client, future_date
    ):
        """Test creating visit with unassigned client auto-assigns seller."""
        seller_id = uuid4()

        # Mock client service responses
        mock_client_service.get_client.return_value = unassigned_client
        mock_client_service.assign_seller.return_value = None

        # Mock repository responses
        mock_visit_repository.has_conflicting_visit.return_value = None
        mock_visit_repository.create.return_value = Visit(
            id=uuid4(),
            seller_id=seller_id,
            client_id=unassigned_client.id,
            fecha_visita=future_date,
            status=VisitStatus.PROGRAMADA,
            notas_visita="Test notes",
            recomendaciones=None,
            archivos_evidencia=None,
            client_nombre_institucion=unassigned_client.nombre_institucion,
            client_direccion=unassigned_client.direccion,
            client_ciudad=unassigned_client.ciudad,
            client_pais=unassigned_client.pais,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        # Execute saga
        result = await saga.execute(
            seller_id=seller_id,
            client_id=unassigned_client.id,
            fecha_visita=future_date,
            notas_visita="Test notes",
            session=mock_session,
        )

        # Verify client was fetched
        mock_client_service.get_client.assert_called_once_with(unassigned_client.id)

        # Verify seller was assigned
        mock_client_service.assign_seller.assert_called_once_with(unassigned_client.id, seller_id)

        # Verify conflict check
        mock_visit_repository.has_conflicting_visit.assert_called_once()

        # Verify visit was created
        mock_visit_repository.create.assert_called_once()
        assert result.seller_id == seller_id
        assert result.client_id == unassigned_client.id
        assert result.status == VisitStatus.PROGRAMADA

    @pytest.mark.asyncio
    async def test_create_visit_with_already_assigned_client(
        self, saga, mock_client_service, mock_visit_repository, mock_session, future_date
    ):
        """Test creating visit when client is already assigned to current seller."""
        seller_id = uuid4()
        assigned_client = ClientDTO(
            id=uuid4(),
            vendedor_asignado_id=seller_id,  # Already assigned to current seller
            nombre_institucion="Hospital Central",
            direccion="Calle 123",
            ciudad="Bogotá",
            pais="Colombia",
        )

        mock_client_service.get_client.return_value = assigned_client
        mock_visit_repository.has_conflicting_visit.return_value = None
        mock_visit_repository.create.return_value = Visit(
            id=uuid4(),
            seller_id=seller_id,
            client_id=assigned_client.id,
            fecha_visita=future_date,
            status=VisitStatus.PROGRAMADA,
            notas_visita=None,
            recomendaciones=None,
            archivos_evidencia=None,
            client_nombre_institucion=assigned_client.nombre_institucion,
            client_direccion=assigned_client.direccion,
            client_ciudad=assigned_client.ciudad,
            client_pais=assigned_client.pais,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        result = await saga.execute(
            seller_id=seller_id,
            client_id=assigned_client.id,
            fecha_visita=future_date,
            notas_visita=None,
            session=mock_session,
        )

        # Verify seller was NOT assigned (already assigned)
        mock_client_service.assign_seller.assert_not_called()

        # Verify visit was created
        mock_visit_repository.create.assert_called_once()
        assert result.seller_id == seller_id


class TestCreateVisitSagaFailures:
    """Test failure scenarios."""

    @pytest.mark.asyncio
    async def test_create_visit_with_nonexistent_client(
        self, saga, mock_client_service, mock_session, future_date
    ):
        """Test creating visit for non-existent client raises VisitNotFoundError."""
        seller_id = uuid4()
        client_id = uuid4()

        # Mock client not found
        mock_client_service.get_client.return_value = None

        with pytest.raises(VisitNotFoundError) as exc_info:
            await saga.execute(
                seller_id=seller_id,
                client_id=client_id,
                fecha_visita=future_date,
                notas_visita=None,
                session=mock_session,
            )

        assert exc_info.value.visit_id == client_id

    @pytest.mark.asyncio
    async def test_create_visit_with_client_assigned_to_other_seller(
        self, saga, mock_client_service, mock_session, future_date
    ):
        """Test creating visit when client assigned to other seller raises error."""
        seller_id = uuid4()
        other_seller_id = uuid4()
        client = ClientDTO(
            id=uuid4(),
            vendedor_asignado_id=other_seller_id,  # Assigned to different seller
            nombre_institucion="Hospital Central",
            direccion="Calle 123",
            ciudad="Bogotá",
            pais="Colombia",
        )

        mock_client_service.get_client.return_value = client

        with pytest.raises(ClientAssignedToOtherSellerError) as exc_info:
            await saga.execute(
                seller_id=seller_id,
                client_id=client.id,
                fecha_visita=future_date,
                notas_visita=None,
                session=mock_session,
            )

        assert exc_info.value.client_id == client.id
        assert exc_info.value.assigned_seller_id == other_seller_id

    @pytest.mark.asyncio
    async def test_create_visit_with_past_date(
        self, saga, mock_client_service, mock_session, unassigned_client
    ):
        """Test creating visit with past date raises InvalidVisitDateError."""
        seller_id = uuid4()
        past_date = datetime.now(timezone.utc) - timedelta(days=1)

        mock_client_service.get_client.return_value = unassigned_client

        with pytest.raises(InvalidVisitDateError):
            await saga.execute(
                seller_id=seller_id,
                client_id=unassigned_client.id,
                fecha_visita=past_date,
                notas_visita=None,
                session=mock_session,
            )

    @pytest.mark.asyncio
    async def test_create_visit_with_date_not_enough_in_advance(
        self, saga, mock_client_service, mock_session, unassigned_client
    ):
        """Test creating visit less than 1 day in advance raises error."""
        seller_id = uuid4()
        # 12 hours from now (less than 1 day)
        too_soon_date = datetime.now(timezone.utc) + timedelta(hours=12)

        mock_client_service.get_client.return_value = unassigned_client

        with pytest.raises(InvalidVisitDateError):
            await saga.execute(
                seller_id=seller_id,
                client_id=unassigned_client.id,
                fecha_visita=too_soon_date,
                notas_visita=None,
                session=mock_session,
            )

    @pytest.mark.asyncio
    async def test_create_visit_with_time_conflict(
        self, saga, mock_client_service, mock_visit_repository, mock_session, unassigned_client, future_date
    ):
        """Test creating visit within 180 minutes of existing visit raises error."""
        seller_id = uuid4()

        mock_client_service.get_client.return_value = unassigned_client
        mock_client_service.assign_seller.return_value = None

        # Mock conflicting visit
        conflicting_visit = Visit(
            id=uuid4(),
            seller_id=seller_id,
            client_id=uuid4(),
            fecha_visita=future_date + timedelta(minutes=100),  # Within 180 minutes
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
        mock_visit_repository.has_conflicting_visit.return_value = conflicting_visit

        with pytest.raises(VisitTimeConflictError) as exc_info:
            await saga.execute(
                seller_id=seller_id,
                client_id=unassigned_client.id,
                fecha_visita=future_date,
                notas_visita=None,
                session=mock_session,
            )

        assert exc_info.value.conflicting_visit == conflicting_visit

    @pytest.mark.asyncio
    async def test_create_visit_client_assignment_fails(
        self, saga, mock_client_service, mock_session, unassigned_client, future_date
    ):
        """Test creating visit when client assignment fails."""
        from src.adapters.output.services.client_service_adapter import (
            ClientAssignmentFailedError,
        )

        seller_id = uuid4()

        mock_client_service.get_client.return_value = unassigned_client
        # Assignment fails
        mock_client_service.assign_seller.side_effect = ClientAssignmentFailedError(
            "Assignment failed"
        )

        with pytest.raises(ClientAssignmentFailedError):
            await saga.execute(
                seller_id=seller_id,
                client_id=unassigned_client.id,
                fecha_visita=future_date,
                notas_visita=None,
                session=mock_session,
            )

        # Verify assignment was attempted
        mock_client_service.assign_seller.assert_called_once_with(
            unassigned_client.id, seller_id
        )


class TestCreateVisitSagaDataDenormalization:
    """Test denormalized client data preservation."""

    @pytest.mark.asyncio
    async def test_visit_preserves_client_snapshot(
        self, saga, mock_client_service, mock_visit_repository, mock_session, unassigned_client, future_date
    ):
        """Test that visit stores snapshot of client data."""
        seller_id = uuid4()

        mock_client_service.get_client.return_value = unassigned_client
        mock_client_service.assign_seller.return_value = None
        mock_visit_repository.has_conflicting_visit.return_value = None

        # Capture the visit passed to create()
        created_visit = None

        async def capture_visit(visit, session):
            nonlocal created_visit
            created_visit = visit
            return visit

        mock_visit_repository.create.side_effect = capture_visit

        await saga.execute(
            seller_id=seller_id,
            client_id=unassigned_client.id,
            fecha_visita=future_date,
            notas_visita="Test",
            session=mock_session,
        )

        # Verify denormalized fields match client
        assert created_visit.client_nombre_institucion == unassigned_client.nombre_institucion
        assert created_visit.client_direccion == unassigned_client.direccion
        assert created_visit.client_ciudad == unassigned_client.ciudad
        assert created_visit.client_pais == unassigned_client.pais
