"""Tests for client controller endpoints."""

import uuid
from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from src.adapters.input.controllers.client_controller import router
from src.domain.entities.client import Client


@pytest.mark.asyncio
async def test_get_client_by_cognito_user_id_success():
    """Test getting a client by Cognito User ID."""
    app = FastAPI()
    app.include_router(router)

    cognito_user_id = "us-east-1:12345678-1234-1234-1234-123456789012"
    cliente_id = uuid.uuid4()

    # Create mock client
    mock_client = Client(
        cliente_id=cliente_id,
        cognito_user_id=cognito_user_id,
        email="test@example.com",
        telefono="+1234567890",
        nombre_institucion="Test Hospital",
        tipo_institucion="hospital",
        nit="123456789",
        direccion="123 Test St",
        ciudad="Test City",
        pais="Test Country",
        representante="John Doe",
        vendedor_asignado_id=None,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )

    with patch(
        "src.adapters.input.controllers.client_controller.ClientRepository"
    ) as MockRepository:
        mock_repo = MockRepository.return_value
        mock_repo.find_by_cognito_user_id = AsyncMock(return_value=mock_client)

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get(f"/clients/by-cognito/{cognito_user_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["cliente_id"] == str(cliente_id)
        assert data["cognito_user_id"] == cognito_user_id
        assert data["email"] == "test@example.com"
        assert data["nombre_institucion"] == "Test Hospital"


@pytest.mark.asyncio
async def test_get_client_by_cognito_user_id_not_found():
    """Test getting a client by Cognito User ID when not found."""
    app = FastAPI()
    app.include_router(router)

    cognito_user_id = "us-east-1:99999999-9999-9999-9999-999999999999"

    with patch(
        "src.adapters.input.controllers.client_controller.ClientRepository"
    ) as MockRepository:
        mock_repo = MockRepository.return_value
        mock_repo.find_by_cognito_user_id = AsyncMock(return_value=None)

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get(f"/clients/by-cognito/{cognito_user_id}")

        assert response.status_code == 404
        data = response.json()
        assert "Client not found" in data["detail"]


@pytest.mark.asyncio
async def test_assign_seller_success():
    """Test successful seller assignment to unassigned client."""
    app = FastAPI()
    app.include_router(router)

    cliente_id = uuid.uuid4()
    vendedor_id = uuid.uuid4()
    now = datetime.now()

    # Mock updated client
    updated_client = Client(
        cliente_id=cliente_id,
        cognito_user_id="cognito-test-123",
        email="test@hospital.com",
        telefono="+1234567890",
        nombre_institucion="Test Hospital",
        tipo_institucion="hospital",
        nit="123456789",
        direccion="123 Test St",
        ciudad="Test City",
        pais="Test Country",
        representante="John Doe",
        vendedor_asignado_id=vendedor_id,
        created_at=now,
        updated_at=now,
    )

    with patch(
        "src.adapters.input.controllers.client_controller.AssignSellerUseCase"
    ) as MockUseCase:
        mock_use_case = MockUseCase.return_value
        mock_use_case.execute = AsyncMock(return_value=updated_client)

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.patch(
                f"/clients/{cliente_id}/assign-seller",
                json={"vendedor_asignado_id": str(vendedor_id)}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["cliente_id"] == str(cliente_id)
        assert data["vendedor_asignado_id"] == str(vendedor_id)
        assert data["nombre_institucion"] == "Test Hospital"


@pytest.mark.asyncio
async def test_assign_seller_client_not_found():
    """Test assigning seller to non-existent client."""
    from src.domain.exceptions import ClientNotFoundException

    app = FastAPI()
    app.include_router(router)

    cliente_id = uuid.uuid4()
    vendedor_id = uuid.uuid4()

    with patch(
        "src.adapters.input.controllers.client_controller.AssignSellerUseCase"
    ) as MockUseCase:
        mock_use_case = MockUseCase.return_value
        mock_use_case.execute = AsyncMock(
            side_effect=ClientNotFoundException(cliente_id)
        )

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.patch(
                f"/clients/{cliente_id}/assign-seller",
                json={"vendedor_asignado_id": str(vendedor_id)}
            )

        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert data["detail"]["error"] == "CLIENT_NOT_FOUND"


@pytest.mark.asyncio
async def test_assign_seller_already_assigned():
    """Test assigning seller when client already assigned to different seller."""
    from src.domain.exceptions import ClientAlreadyAssignedException

    app = FastAPI()
    app.include_router(router)

    cliente_id = uuid.uuid4()
    existing_vendedor_id = uuid.uuid4()
    new_vendedor_id = uuid.uuid4()

    with patch(
        "src.adapters.input.controllers.client_controller.AssignSellerUseCase"
    ) as MockUseCase:
        mock_use_case = MockUseCase.return_value
        mock_use_case.execute = AsyncMock(
            side_effect=ClientAlreadyAssignedException(cliente_id, existing_vendedor_id)
        )

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.patch(
                f"/clients/{cliente_id}/assign-seller",
                json={"vendedor_asignado_id": str(new_vendedor_id)}
            )

        assert response.status_code == 409
        data = response.json()
        assert "detail" in data
        assert data["detail"]["error"] == "CLIENT_ALREADY_ASSIGNED"
        assert data["detail"]["details"]["cliente_id"] == str(cliente_id)
        assert data["detail"]["details"]["current_vendedor_asignado_id"] == str(existing_vendedor_id)
