"""Tests for sellers app visit adapter."""

from datetime import datetime
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from sellers_app.adapters.visit_adapter import VisitAdapter
from sellers_app.schemas.visit_schemas import (
    CreateVisitRequestBFF,
    UpdateVisitStatusRequestBFF,
    GenerateEvidenceUploadURLRequestBFF,
    ConfirmEvidenceUploadRequestBFF,
    VisitResponseBFF,
    PreSignedUploadURLResponseBFF,
    ListVisitsResponseBFF,
)
from common.exceptions import MicroserviceConnectionError, MicroserviceHTTPError


@pytest.fixture
def mock_http_client():
    """Create a mock HTTP client."""
    return Mock()


@pytest.fixture
def visit_adapter(mock_http_client):
    """Create a VisitAdapter instance."""
    return VisitAdapter(mock_http_client)


@pytest.fixture
def sample_visit_response_data():
    """Create sample visit response data."""
    return {
        "id": str(uuid4()),
        "seller_id": str(uuid4()),
        "client_id": str(uuid4()),
        "fecha_visita": datetime.now().isoformat(),
        "status": "pending",
        "notas_visita": "Test notes",
        "client_nombre_institucion": "Test Institution",
        "client_direccion": "123 Test St",
        "client_ciudad": "Test City",
        "client_pais": "US",
        "recomendaciones": None,
        "archivos_evidencia": None,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
    }


class TestVisitAdapterCreateVisit:
    """Tests for create_visit method."""

    @pytest.mark.asyncio
    async def test_create_visit_success(self, visit_adapter, mock_http_client, sample_visit_response_data):
        """Test creating a visit successfully."""
        seller_id = uuid4()
        client_id = uuid4()
        request = CreateVisitRequestBFF(
            client_id=client_id,
            fecha_visita=datetime.now(),
            notas_visita="Test notes",
        )

        mock_http_client.post = AsyncMock(return_value=sample_visit_response_data)

        result = await visit_adapter.create_visit(
            seller_id=seller_id,
            request=request,
            client_nombre_institucion="Test Institution",
            client_direccion="123 Test St",
            client_ciudad="Test City",
            client_pais="US",
        )

        # Verify HTTP client was called
        mock_http_client.post.assert_called_once()
        call_args = mock_http_client.post.call_args

        assert call_args[0][0] == "/seller/visits"
        assert "json" in call_args[1]
        payload = call_args[1]["json"]
        assert payload["seller_id"] == str(seller_id)
        assert payload["client_id"] == str(client_id)

        # Verify response
        assert isinstance(result, VisitResponseBFF)

    @pytest.mark.asyncio
    async def test_create_visit_connection_error(self, visit_adapter, mock_http_client):
        """Test create_visit handles connection error."""
        seller_id = uuid4()
        client_id = uuid4()
        request = CreateVisitRequestBFF(
            client_id=client_id,
            fecha_visita=datetime.now(),
            notas_visita="Test notes",
        )

        mock_http_client.post = AsyncMock(
            side_effect=MicroserviceConnectionError(
                service_name="seller", original_error="Connection refused"
            )
        )

        with pytest.raises(MicroserviceConnectionError):
            await visit_adapter.create_visit(
                seller_id=seller_id,
                request=request,
                client_nombre_institucion="Test Institution",
                client_direccion="123 Test St",
                client_ciudad="Test City",
                client_pais="US",
            )

    @pytest.mark.asyncio
    async def test_create_visit_http_error(self, visit_adapter, mock_http_client):
        """Test create_visit handles HTTP error."""
        seller_id = uuid4()
        client_id = uuid4()
        request = CreateVisitRequestBFF(
            client_id=client_id,
            fecha_visita=datetime.now(),
            notas_visita="Test notes",
        )

        mock_http_client.post = AsyncMock(
            side_effect=MicroserviceHTTPError(
                service_name="seller", status_code=400, response_text="Bad request"
            )
        )

        with pytest.raises(MicroserviceHTTPError):
            await visit_adapter.create_visit(
                seller_id=seller_id,
                request=request,
                client_nombre_institucion="Test Institution",
                client_direccion="123 Test St",
                client_ciudad="Test City",
                client_pais="US",
            )


class TestVisitAdapterUpdateVisitStatus:
    """Tests for update_visit_status method."""

    @pytest.mark.asyncio
    async def test_update_visit_status_success(self, visit_adapter, mock_http_client, sample_visit_response_data):
        """Test updating visit status successfully."""
        visit_id = uuid4()
        seller_id = uuid4()
        request = UpdateVisitStatusRequestBFF(
            status="completed",
            recomendaciones="Test recommendations",
        )

        updated_data = {**sample_visit_response_data, "status": "completed"}
        mock_http_client.patch = AsyncMock(return_value=updated_data)

        result = await visit_adapter.update_visit_status(
            visit_id=visit_id,
            seller_id=seller_id,
            request=request,
        )

        # Verify HTTP client was called
        mock_http_client.patch.assert_called_once()
        call_args = mock_http_client.patch.call_args

        assert f"/seller/visits/{visit_id}/status" in call_args[0][0]
        assert "json" in call_args[1]
        payload = call_args[1]["json"]
        assert payload["status"] == "completed"

        # Verify response
        assert isinstance(result, VisitResponseBFF)

    @pytest.mark.asyncio
    async def test_update_visit_status_not_found(self, visit_adapter, mock_http_client):
        """Test update_visit_status when visit not found."""
        visit_id = uuid4()
        seller_id = uuid4()
        request = UpdateVisitStatusRequestBFF(
            status="completed",
            recomendaciones="Test recommendations",
        )

        mock_http_client.patch = AsyncMock(
            side_effect=MicroserviceHTTPError(
                service_name="seller", status_code=404, response_text="Visit not found"
            )
        )

        with pytest.raises(MicroserviceHTTPError) as exc_info:
            await visit_adapter.update_visit_status(
                visit_id=visit_id,
                seller_id=seller_id,
                request=request,
            )

        assert exc_info.value.status_code == 404


class TestVisitAdapterListVisits:
    """Tests for list_visits method."""

    @pytest.mark.asyncio
    async def test_list_visits_success(self, visit_adapter, mock_http_client, sample_visit_response_data):
        """Test listing visits successfully."""
        seller_id = uuid4()
        date = datetime.now()

        response_data = {
            "visits": [sample_visit_response_data],
            "count": 1,
        }
        mock_http_client.get = AsyncMock(return_value=response_data)

        result = await visit_adapter.list_visits(
            seller_id=seller_id,
            date=date,
        )

        # Verify HTTP client was called
        mock_http_client.get.assert_called_once()
        call_args = mock_http_client.get.call_args

        assert call_args[0][0] == "/seller/visits"
        assert "params" in call_args[1]
        params = call_args[1]["params"]
        assert params["seller_id"] == str(seller_id)

        # Verify response
        assert isinstance(result, ListVisitsResponseBFF)

    @pytest.mark.asyncio
    async def test_list_visits_empty(self, visit_adapter, mock_http_client):
        """Test listing visits returns empty list."""
        seller_id = uuid4()
        date = datetime.now()

        response_data = {
            "visits": [],
            "count": 0,
        }
        mock_http_client.get = AsyncMock(return_value=response_data)

        result = await visit_adapter.list_visits(
            seller_id=seller_id,
            date=date,
        )

        assert result.count == 0
        assert len(result.visits) == 0


class TestVisitAdapterGenerateEvidenceUploadUrl:
    """Tests for generate_evidence_upload_url method."""

    @pytest.mark.asyncio
    async def test_generate_evidence_upload_url_success(self, visit_adapter, mock_http_client):
        """Test generating evidence upload URL successfully."""
        visit_id = uuid4()
        seller_id = uuid4()
        request = GenerateEvidenceUploadURLRequestBFF(
            filename="evidence.jpg",
            content_type="image/jpeg",
        )

        response_data = {
            "upload_url": "https://s3.example.com/upload",
            "fields": {"key": f"{visit_id}/evidence.jpg"},
            "s3_url": f"s3://bucket/{visit_id}/evidence.jpg",
            "expires_at": datetime.now().isoformat(),
        }
        mock_http_client.post = AsyncMock(return_value=response_data)

        result = await visit_adapter.generate_evidence_upload_url(
            visit_id=visit_id,
            seller_id=seller_id,
            request=request,
        )

        # Verify HTTP client was called
        mock_http_client.post.assert_called_once()
        call_args = mock_http_client.post.call_args

        assert f"/seller/visits/{visit_id}/evidence/upload-url" in call_args[0][0]
        assert "json" in call_args[1]
        payload = call_args[1]["json"]
        assert payload["filename"] == "evidence.jpg"

        # Verify response
        assert isinstance(result, PreSignedUploadURLResponseBFF)


class TestVisitAdapterConfirmEvidenceUpload:
    """Tests for confirm_evidence_upload method."""

    @pytest.mark.asyncio
    async def test_confirm_evidence_upload_success(self, visit_adapter, mock_http_client, sample_visit_response_data):
        """Test confirming evidence upload successfully."""
        visit_id = uuid4()
        seller_id = uuid4()
        request = ConfirmEvidenceUploadRequestBFF(
            s3_url="https://s3.example.com/bucket/evidence.jpg",
        )

        mock_http_client.post = AsyncMock(return_value=sample_visit_response_data)

        result = await visit_adapter.confirm_evidence_upload(
            visit_id=visit_id,
            seller_id=seller_id,
            request=request,
        )

        # Verify HTTP client was called
        mock_http_client.post.assert_called_once()
        call_args = mock_http_client.post.call_args

        assert f"/seller/visits/{visit_id}/evidence/confirm" in call_args[0][0]
        assert "json" in call_args[1]
        payload = call_args[1]["json"]
        assert payload["s3_url"] == "https://s3.example.com/bucket/evidence.jpg"

        # Verify response
        assert isinstance(result, VisitResponseBFF)

    @pytest.mark.asyncio
    async def test_confirm_evidence_upload_not_found(self, visit_adapter, mock_http_client):
        """Test confirm_evidence_upload when visit not found."""
        visit_id = uuid4()
        seller_id = uuid4()
        request = ConfirmEvidenceUploadRequestBFF(
            s3_url="https://s3.example.com/bucket/evidence.jpg",
        )

        mock_http_client.post = AsyncMock(
            side_effect=MicroserviceHTTPError(
                service_name="seller", status_code=404, response_text="Visit not found"
            )
        )

        with pytest.raises(MicroserviceHTTPError) as exc_info:
            await visit_adapter.confirm_evidence_upload(
                visit_id=visit_id,
                seller_id=seller_id,
                request=request,
            )

        assert exc_info.value.status_code == 404


class TestVisitAdapterInitialization:
    """Tests for VisitAdapter initialization."""

    def test_visit_adapter_initialization(self, mock_http_client):
        """Test VisitAdapter is properly initialized."""
        adapter = VisitAdapter(mock_http_client)

        assert adapter.client == mock_http_client

    def test_visit_adapter_has_correct_methods(self, mock_http_client):
        """Test VisitAdapter has all required methods."""
        adapter = VisitAdapter(mock_http_client)

        assert hasattr(adapter, "create_visit")
        assert hasattr(adapter, "update_visit_status")
        assert hasattr(adapter, "list_visits")
        assert hasattr(adapter, "generate_evidence_upload_url")
        assert hasattr(adapter, "confirm_evidence_upload")
