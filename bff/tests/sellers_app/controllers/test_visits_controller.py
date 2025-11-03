"""Unit tests for BFF visits controller (sellers app)."""
import pytest
from datetime import datetime, timezone, timedelta
from uuid import uuid4
from unittest.mock import AsyncMock, patch
from fastapi import HTTPException
from fastapi.testclient import TestClient

from sellers_app.controllers.visits_controller import (
    create_visit,
    update_visit_status,
    list_visits,
    generate_evidence_upload_url,
    confirm_evidence_upload,
)
from sellers_app.schemas.visit_schemas import (
    CreateVisitRequestBFF,
    UpdateVisitStatusRequestBFF,
    GenerateEvidenceUploadURLRequestBFF,
    ConfirmEvidenceUploadRequestBFF,
    VisitResponseBFF,
    PreSignedUploadURLResponseBFF,
    ListVisitsResponseBFF,
)
from sellers_app.sagas.create_visit_saga import ClientNotFoundError, ClientAssignedToOtherSellerError


@pytest.fixture
def seller_id():
    """Fixed seller ID."""
    return uuid4()


@pytest.fixture
def cognito_user_id():
    """Fixed cognito user ID."""
    return "cognito-user-123"


@pytest.fixture
def visit_response():
    """Mock visit response."""
    return VisitResponseBFF(
        id=uuid4(),
        seller_id=uuid4(),
        client_id=uuid4(),
        fecha_visita=datetime.now(timezone.utc) + timedelta(days=2),
        status="programada",
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


@pytest.fixture
def user_dict(cognito_user_id, seller_id):
    """Mock user dictionary from JWT."""
    return {
        "sub": cognito_user_id,
        "cognito:groups": ["seller_users"],
    }


class TestCreateVisitBFF:
    """Test create_visit BFF endpoint."""

    @pytest.mark.asyncio
    async def test_create_visit_success(self, user_dict, seller_id, visit_response):
        """Test successful visit creation via BFF."""
        request = CreateVisitRequestBFF(
            client_id=uuid4(),
            fecha_visita=datetime.now(timezone.utc) + timedelta(days=2),
            notas_visita="Test",
        )

        mock_visit_port = AsyncMock()
        mock_visit_port.create_visit.return_value = visit_response

        # Mock the saga
        mock_saga = AsyncMock()
        mock_saga.execute.return_value = visit_response

        mock_seller_port = AsyncMock()
        mock_seller_port.get_seller_by_cognito_user_id.return_value = {
            "id": str(seller_id),
            "nombre": "Test Seller"
        }

        mock_client_port = AsyncMock()

        with patch("sellers_app.controllers.visits_controller.CreateVisitSaga") as MockSaga, \
             patch("sellers_app.controllers.visits_controller.require_seller_user") as mock_user_dep, \
             patch("sellers_app.controllers.visits_controller.get_visit_port") as mock_visit_dep, \
             patch("sellers_app.controllers.visits_controller.get_seller_app_seller_port") as mock_seller_dep, \
             patch("sellers_app.controllers.visits_controller.get_seller_client_port") as mock_client_dep:

            mock_user_dep.return_value = user_dict
            mock_visit_dep.return_value = mock_visit_port
            mock_seller_dep.return_value = mock_seller_port
            mock_client_dep.return_value = mock_client_port
            MockSaga.return_value = mock_saga

            response = await create_visit(
                request=request,
                visit_port=mock_visit_port,
                seller_port=mock_seller_port,
                client_port=mock_client_port,
                user=user_dict,
            )

            assert response.id == visit_response.id
            assert response.status == "programada"
            mock_saga.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_visit_client_not_found(self, user_dict, seller_id):
        """Test create visit when client not found."""
        request = CreateVisitRequestBFF(
            client_id=uuid4(),
            fecha_visita=datetime.now(timezone.utc) + timedelta(days=2),
            notas_visita="Test",
        )

        mock_visit_port = AsyncMock()
        mock_seller_port = AsyncMock()
        mock_seller_port.get_seller_by_cognito_user_id.return_value = {
            "id": str(seller_id)
        }
        mock_client_port = AsyncMock()

        mock_saga = AsyncMock()
        mock_saga.execute.side_effect = ClientNotFoundError("Client 123 not found")

        with patch("sellers_app.controllers.visits_controller.CreateVisitSaga") as MockSaga:
            MockSaga.return_value = mock_saga

            with pytest.raises(HTTPException) as exc_info:
                await create_visit(
                    request=request,
                    visit_port=mock_visit_port,
                    seller_port=mock_seller_port,
                    client_port=mock_client_port,
                    user=user_dict,
                )

            assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_create_visit_client_assigned_to_other_seller(self, user_dict, seller_id):
        """Test create visit when client already assigned."""
        request = CreateVisitRequestBFF(
            client_id=uuid4(),
            fecha_visita=datetime.now(timezone.utc) + timedelta(days=2),
            notas_visita="Test",
        )

        client_id = uuid4()
        other_seller_id = uuid4()

        mock_visit_port = AsyncMock()
        mock_seller_port = AsyncMock()
        mock_seller_port.get_seller_by_cognito_user_id.return_value = {
            "id": str(seller_id)
        }
        mock_client_port = AsyncMock()

        mock_saga = AsyncMock()
        error = ClientAssignedToOtherSellerError(
            client_id=client_id,
            client_name="Test Client",
            assigned_seller_id=other_seller_id
        )
        mock_saga.execute.side_effect = error

        with patch("sellers_app.controllers.visits_controller.CreateVisitSaga") as MockSaga:
            MockSaga.return_value = mock_saga

            with pytest.raises(HTTPException) as exc_info:
                await create_visit(
                    request=request,
                    visit_port=mock_visit_port,
                    seller_port=mock_seller_port,
                    client_port=mock_client_port,
                    user=user_dict,
                )

            assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_create_visit_missing_token(self):
        """Test create visit without valid JWT token."""
        request = CreateVisitRequestBFF(
            client_id=uuid4(),
            fecha_visita=datetime.now(timezone.utc) + timedelta(days=2),
            notas_visita="Test",
        )

        user_dict = {"cognito:groups": ["seller_users"]}  # Missing 'sub'
        mock_visit_port = AsyncMock()
        mock_seller_port = AsyncMock()
        mock_client_port = AsyncMock()

        with pytest.raises(HTTPException) as exc_info:
            await create_visit(
                request=request,
                visit_port=mock_visit_port,
                seller_port=mock_seller_port,
                client_port=mock_client_port,
                user=user_dict,
            )

        assert exc_info.value.status_code == 401


class TestUpdateVisitStatusBFF:
    """Test update_visit_status BFF endpoint."""

    @pytest.mark.asyncio
    async def test_update_status_success(self, user_dict, seller_id, visit_response):
        """Test successful status update via BFF."""
        visit_id = uuid4()
        request = UpdateVisitStatusRequestBFF(
            status="completada",
            recomendaciones="Test recommendations",
        )

        updated_response = visit_response.model_copy(
            update={
                "status": "completada",
                "recomendaciones": "Test recommendations"
            }
        )

        mock_visit_port = AsyncMock()
        mock_visit_port.update_visit_status.return_value = updated_response

        mock_seller_port = AsyncMock()
        mock_seller_port.get_seller_by_cognito_user_id.return_value = {
            "id": str(seller_id)
        }

        response = await update_visit_status(
            visit_id=visit_id,
            request=request,
            visit_port=mock_visit_port,
            seller_port=mock_seller_port,
            user=user_dict,
        )

        assert response.status == "completada"
        assert response.recomendaciones == "Test recommendations"
        mock_visit_port.update_visit_status.assert_called_once_with(
            visit_id=visit_id, seller_id=seller_id, request=request
        )

    @pytest.mark.asyncio
    async def test_update_status_missing_token(self):
        """Test update status without valid JWT token."""
        visit_id = uuid4()
        request = UpdateVisitStatusRequestBFF(
            status="completada",
            recomendaciones="Test",
        )

        user_dict = {"cognito:groups": ["seller_users"]}  # Missing 'sub'
        mock_visit_port = AsyncMock()
        mock_seller_port = AsyncMock()

        with pytest.raises(HTTPException) as exc_info:
            await update_visit_status(
                visit_id=visit_id,
                request=request,
                visit_port=mock_visit_port,
                seller_port=mock_seller_port,
                user=user_dict,
            )

        assert exc_info.value.status_code == 401


class TestListVisitsBFF:
    """Test list_visits BFF endpoint."""

    @pytest.mark.asyncio
    async def test_list_visits_success(self, user_dict, seller_id, visit_response):
        """Test successful visit listing via BFF."""
        date = datetime.now(timezone.utc)
        list_response = ListVisitsResponseBFF(
            visits=[visit_response],
            count=1,
        )

        mock_visit_port = AsyncMock()
        mock_visit_port.list_visits.return_value = list_response

        mock_seller_port = AsyncMock()
        mock_seller_port.get_seller_by_cognito_user_id.return_value = {
            "id": str(seller_id)
        }

        response = await list_visits(
            date=date,
            visit_port=mock_visit_port,
            seller_port=mock_seller_port,
            user=user_dict,
        )

        assert response.count == 1
        assert len(response.visits) == 1
        mock_visit_port.list_visits.assert_called_once_with(
            seller_id=seller_id, date=date
        )

    @pytest.mark.asyncio
    async def test_list_visits_empty(self, user_dict, seller_id):
        """Test listing visits returns empty list."""
        date = datetime.now(timezone.utc)
        list_response = ListVisitsResponseBFF(visits=[], count=0)

        mock_visit_port = AsyncMock()
        mock_visit_port.list_visits.return_value = list_response

        mock_seller_port = AsyncMock()
        mock_seller_port.get_seller_by_cognito_user_id.return_value = {
            "id": str(seller_id)
        }

        response = await list_visits(
            date=date,
            visit_port=mock_visit_port,
            seller_port=mock_seller_port,
            user=user_dict,
        )

        assert response.count == 0
        assert len(response.visits) == 0

    @pytest.mark.asyncio
    async def test_list_visits_missing_token(self):
        """Test list visits without valid JWT token."""
        date = datetime.now(timezone.utc)
        user_dict = {"cognito:groups": ["seller_users"]}  # Missing 'sub'
        mock_visit_port = AsyncMock()
        mock_seller_port = AsyncMock()

        with pytest.raises(HTTPException) as exc_info:
            await list_visits(
                date=date,
                visit_port=mock_visit_port,
                seller_port=mock_seller_port,
                user=user_dict,
            )

        assert exc_info.value.status_code == 401


class TestGenerateEvidenceUploadURLBFF:
    """Test generate_evidence_upload_url BFF endpoint."""

    @pytest.mark.asyncio
    async def test_generate_url_success(self, user_dict, seller_id):
        """Test successful URL generation via BFF."""
        visit_id = uuid4()
        request = GenerateEvidenceUploadURLRequestBFF(
            filename="photo.jpg",
            content_type="image/jpeg",
        )

        upload_response = PreSignedUploadURLResponseBFF(
            upload_url="https://s3.amazonaws.com/bucket",
            fields={"key": "test"},
            s3_url="https://s3.amazonaws.com/bucket/test",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        )

        mock_visit_port = AsyncMock()
        mock_visit_port.generate_evidence_upload_url.return_value = upload_response

        mock_seller_port = AsyncMock()
        mock_seller_port.get_seller_by_cognito_user_id.return_value = {
            "id": str(seller_id)
        }

        response = await generate_evidence_upload_url(
            visit_id=visit_id,
            request=request,
            visit_port=mock_visit_port,
            seller_port=mock_seller_port,
            user=user_dict,
        )

        assert response.upload_url == upload_response.upload_url
        assert response.s3_url == upload_response.s3_url
        mock_visit_port.generate_evidence_upload_url.assert_called_once_with(
            visit_id=visit_id, seller_id=seller_id, request=request
        )

    @pytest.mark.asyncio
    async def test_generate_url_missing_token(self):
        """Test generate URL without valid JWT token."""
        visit_id = uuid4()
        request = GenerateEvidenceUploadURLRequestBFF(
            filename="photo.jpg",
            content_type="image/jpeg",
        )

        user_dict = {"cognito:groups": ["seller_users"]}  # Missing 'sub'
        mock_visit_port = AsyncMock()
        mock_seller_port = AsyncMock()

        with pytest.raises(HTTPException) as exc_info:
            await generate_evidence_upload_url(
                visit_id=visit_id,
                request=request,
                visit_port=mock_visit_port,
                seller_port=mock_seller_port,
                user=user_dict,
            )

        assert exc_info.value.status_code == 401


class TestConfirmEvidenceUploadBFF:
    """Test confirm_evidence_upload BFF endpoint."""

    @pytest.mark.asyncio
    async def test_confirm_upload_success(self, user_dict, seller_id, visit_response):
        """Test successful upload confirmation via BFF."""
        visit_id = uuid4()
        s3_url = "https://s3.amazonaws.com/bucket/photo.jpg"
        request = ConfirmEvidenceUploadRequestBFF(s3_url=s3_url)

        updated_response = visit_response.model_copy(
            update={"archivos_evidencia": s3_url}
        )

        mock_visit_port = AsyncMock()
        mock_visit_port.confirm_evidence_upload.return_value = updated_response

        mock_seller_port = AsyncMock()
        mock_seller_port.get_seller_by_cognito_user_id.return_value = {
            "id": str(seller_id)
        }

        response = await confirm_evidence_upload(
            visit_id=visit_id,
            request=request,
            visit_port=mock_visit_port,
            seller_port=mock_seller_port,
            user=user_dict,
        )

        assert response.archivos_evidencia == s3_url
        mock_visit_port.confirm_evidence_upload.assert_called_once_with(
            visit_id=visit_id, seller_id=seller_id, request=request
        )

    @pytest.mark.asyncio
    async def test_confirm_upload_missing_token(self):
        """Test confirm upload without valid JWT token."""
        visit_id = uuid4()
        request = ConfirmEvidenceUploadRequestBFF(
            s3_url="https://s3.amazonaws.com/bucket/photo.jpg"
        )

        user_dict = {"cognito:groups": ["seller_users"]}  # Missing 'sub'
        mock_visit_port = AsyncMock()
        mock_seller_port = AsyncMock()

        with pytest.raises(HTTPException) as exc_info:
            await confirm_evidence_upload(
                visit_id=visit_id,
                request=request,
                visit_port=mock_visit_port,
                seller_port=mock_seller_port,
                user=user_dict,
            )

        assert exc_info.value.status_code == 401
