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
