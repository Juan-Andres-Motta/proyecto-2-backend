"""Tests for CreateVisitSaga."""
import pytest
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

from sellers_app.sagas.create_visit_saga import (
    CreateVisitSaga,
    ClientNotFoundError,
    ClientAssignedToOtherSellerError,
)
from sellers_app.schemas.visit_schemas import CreateVisitRequestBFF, VisitResponseBFF
from sellers_app.schemas.client_schemas import ClientResponse


@pytest.fixture
def mock_client_adapter():
    """Create a mock client adapter."""
    return AsyncMock()


@pytest.fixture
def mock_visit_adapter():
    """Create a mock visit adapter."""
    return AsyncMock()


@pytest.fixture
def saga(mock_client_adapter, mock_visit_adapter):
    """Create a CreateVisitSaga instance."""
    return CreateVisitSaga(
        client_adapter=mock_client_adapter,
        visit_adapter=mock_visit_adapter,
    )


@pytest.fixture
def seller_id():
    """Create a seller ID."""
    return uuid4()


@pytest.fixture
def client_id():
    """Create a client ID."""
    return uuid4()


@pytest.fixture
def create_visit_request(client_id):
    """Create a visit request."""
    from datetime import datetime
    return CreateVisitRequestBFF(
        client_id=client_id,
        fecha_visita=datetime.fromisoformat("2025-12-25T10:00:00"),
        notas_visita="Test visit notes",
    )


@pytest.fixture
def client_response(client_id):
    """Create a client response."""
    return ClientResponse(
        cliente_id=client_id,
        cognito_user_id="cognito-123",
        email="test@hospital.com",
        telefono="+1234567890",
        nombre_institucion="Test Hospital",
        tipo_institucion="Hospital",
        nit="123456789",
        direccion="123 Test St",
        ciudad="Test City",
        pais="US",
        representante="John Doe",
        vendedor_asignado_id=None,
        created_at="2025-01-01T00:00:00",
        updated_at="2025-01-01T00:00:00",
    )


@pytest.fixture
def visit_response(client_id, seller_id):
    """Create a visit response."""
    from datetime import datetime
    return VisitResponseBFF(
        id=uuid4(),
        seller_id=seller_id,
        client_id=client_id,
        client_nombre_institucion="Test Hospital",
        client_direccion="123 Test St",
        client_ciudad="Test City",
        client_pais="US",
        fecha_visita=datetime.fromisoformat("2025-12-25T10:00:00"),
        status="programada",
        notas_visita="Test visit notes",
        recomendaciones=None,
        archivos_evidencia=None,
        created_at=datetime.fromisoformat("2025-01-01T00:00:00"),
        updated_at=datetime.fromisoformat("2025-01-01T00:00:00"),
    )


class TestCreateVisitSagaSuccess:
    """Test successful saga execution."""

    @pytest.mark.asyncio
    async def test_execute_with_unassigned_client(
        self,
        saga,
        mock_client_adapter,
        mock_visit_adapter,
        seller_id,
        client_id,
        create_visit_request,
        client_response,
        visit_response,
    ):
        """Test saga execution when client is unassigned."""
        # Setup mocks
        mock_client_adapter.get_client_by_id.return_value = client_response
        mock_client_adapter.assign_seller.return_value = None
        mock_visit_adapter.create_visit.return_value = visit_response

        # Execute saga
        result = await saga.execute(seller_id, create_visit_request)

        # Verify result
        assert result.id == visit_response.id
        assert result.seller_id == seller_id
        assert result.client_nombre_institucion == "Test Hospital"

        # Verify calls were made
        mock_client_adapter.get_client_by_id.assert_called_once_with(client_id)
        mock_client_adapter.assign_seller.assert_called_once_with(client_id, seller_id)
        mock_visit_adapter.create_visit.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_with_already_assigned_client(
        self,
        saga,
        mock_client_adapter,
        mock_visit_adapter,
        seller_id,
        client_id,
        create_visit_request,
        visit_response,
    ):
        """Test saga execution when client is already assigned to same seller."""
        # Setup client response with already assigned seller
        client_response = ClientResponse(
            cliente_id=client_id,
            cognito_user_id="cognito-123",
            email="test@hospital.com",
            telefono="+1234567890",
            nombre_institucion="Test Hospital",
            tipo_institucion="Hospital",
            nit="123456789",
            direccion="123 Test St",
            ciudad="Test City",
            pais="US",
            representante="John Doe",
            vendedor_asignado_id=seller_id,  # Already assigned to this seller
            created_at="2025-01-01T00:00:00",
            updated_at="2025-01-01T00:00:00",
        )

        mock_client_adapter.get_client_by_id.return_value = client_response
        mock_visit_adapter.create_visit.return_value = visit_response

        # Execute saga
        result = await saga.execute(seller_id, create_visit_request)

        # Verify result
        assert result.id == visit_response.id

        # Verify assign_seller was NOT called
        mock_client_adapter.get_client_by_id.assert_called_once_with(client_id)
        mock_client_adapter.assign_seller.assert_not_called()
        mock_visit_adapter.create_visit.assert_called_once()


class TestCreateVisitSagaErrors:
    """Test saga error handling."""

    @pytest.mark.asyncio
    async def test_client_not_found_error(
        self,
        saga,
        mock_client_adapter,
        seller_id,
        client_id,
        create_visit_request,
    ):
        """Test saga when client is not found."""
        # Setup mock to raise exception
        mock_client_adapter.get_client_by_id.side_effect = Exception("Client not found")

        # Execute saga and verify it raises ClientNotFoundError
        with pytest.raises(ClientNotFoundError) as exc_info:
            await saga.execute(seller_id, create_visit_request)

        # Verify error contains correct client_id
        assert exc_info.value.client_id == client_id

    @pytest.mark.asyncio
    async def test_client_assigned_to_different_seller(
        self,
        saga,
        mock_client_adapter,
        seller_id,
        client_id,
        create_visit_request,
    ):
        """Test saga when client is assigned to a different seller."""
        # Setup client response with different seller assignment
        different_seller_id = uuid4()
        client_response = ClientResponse(
            cliente_id=client_id,
            cognito_user_id="cognito-123",
            email="test@hospital.com",
            telefono="+1234567890",
            nombre_institucion="Test Hospital",
            tipo_institucion="Hospital",
            nit="123456789",
            direccion="123 Test St",
            ciudad="Test City",
            pais="US",
            representante="John Doe",
            vendedor_asignado_id=different_seller_id,  # Assigned to different seller
            created_at="2025-01-01T00:00:00",
            updated_at="2025-01-01T00:00:00",
        )

        mock_client_adapter.get_client_by_id.return_value = client_response

        # Execute saga and verify it raises ClientAssignedToOtherSellerError
        with pytest.raises(ClientAssignedToOtherSellerError) as exc_info:
            await saga.execute(seller_id, create_visit_request)

        # Verify error details
        assert exc_info.value.client_id == client_id
        assert exc_info.value.client_name == "Test Hospital"
        assert exc_info.value.assigned_seller_id == different_seller_id

    @pytest.mark.asyncio
    async def test_assign_seller_failure_aborts_saga(
        self,
        saga,
        mock_client_adapter,
        seller_id,
        client_id,
        create_visit_request,
        client_response,
    ):
        """Test saga when seller assignment fails."""
        # Setup mocks
        mock_client_adapter.get_client_by_id.return_value = client_response
        mock_client_adapter.assign_seller.side_effect = Exception("Assignment failed")

        # Execute saga and verify it raises the exception
        with pytest.raises(Exception) as exc_info:
            await saga.execute(seller_id, create_visit_request)

        assert "Assignment failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_visit_creation_failure(
        self,
        saga,
        mock_client_adapter,
        mock_visit_adapter,
        seller_id,
        client_id,
        create_visit_request,
        client_response,
    ):
        """Test saga when visit creation fails."""
        # Setup mocks
        mock_client_adapter.get_client_by_id.return_value = client_response
        mock_client_adapter.assign_seller.return_value = None
        mock_visit_adapter.create_visit.side_effect = Exception("Visit creation failed")

        # Execute saga and verify it raises the exception
        with pytest.raises(Exception) as exc_info:
            await saga.execute(seller_id, create_visit_request)

        assert "Visit creation failed" in str(exc_info.value)


class TestCreateVisitSagaExceptionClasses:
    """Test custom exception classes."""

    def test_client_not_found_error_message(self):
        """Test ClientNotFoundError message formatting."""
        client_id = uuid4()
        error = ClientNotFoundError(client_id)

        assert str(error) == f"Client {client_id} not found"
        assert error.client_id == client_id

    def test_client_assigned_to_other_seller_error_message(self):
        """Test ClientAssignedToOtherSellerError message formatting."""
        client_id = uuid4()
        client_name = "Test Hospital"
        assigned_seller_id = uuid4()

        error = ClientAssignedToOtherSellerError(
            client_id=client_id,
            client_name=client_name,
            assigned_seller_id=assigned_seller_id,
        )

        expected_msg = (
            f"Client {client_name} ({client_id}) is already assigned to seller {assigned_seller_id}"
        )
        assert str(error) == expected_msg
        assert error.client_id == client_id
        assert error.client_name == client_name
        assert error.assigned_seller_id == assigned_seller_id
