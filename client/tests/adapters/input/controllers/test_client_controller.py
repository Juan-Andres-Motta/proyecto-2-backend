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


@pytest.mark.asyncio
async def test_create_client_success():
    """Test creating a new client successfully."""
    app = FastAPI()
    app.include_router(router)

    cliente_id = uuid.uuid4()

    # Mock created client
    created_client = Client(
        cliente_id=cliente_id,
        cognito_user_id="cognito-new-client",
        email="newclient@example.com",
        telefono="+9876543210",
        nombre_institucion="New Hospital",
        tipo_institucion="hospital",
        nit="987654321",
        direccion="456 New St",
        ciudad="New City",
        pais="New Country",
        representante="Jane Smith",
        vendedor_asignado_id=None,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )

    with patch(
        "src.adapters.input.controllers.client_controller.CreateClientUseCase"
    ) as MockUseCase:
        mock_use_case = MockUseCase.return_value
        mock_use_case.execute = AsyncMock(return_value=created_client)

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/clients",
                json={
                    "cognito_user_id": "cognito-new-client",
                    "email": "newclient@example.com",
                    "telefono": "+9876543210",
                    "nombre_institucion": "New Hospital",
                    "tipo_institucion": "hospital",
                    "nit": "987654321",
                    "direccion": "456 New St",
                    "ciudad": "New City",
                    "pais": "New Country",
                    "representante": "Jane Smith",
                }
            )

        assert response.status_code == 201
        data = response.json()
        assert data["cliente_id"] == str(cliente_id)
        assert data["message"] == "Client created successfully"


@pytest.mark.asyncio
async def test_list_clients_without_filter():
    """Test listing all clients without filter."""
    app = FastAPI()
    app.include_router(router)

    cliente_id_1 = uuid.uuid4()
    cliente_id_2 = uuid.uuid4()

    # Mock clients
    clients = [
        Client(
            cliente_id=cliente_id_1,
            cognito_user_id="cognito-client-1",
            email="client1@example.com",
            telefono="+1111111111",
            nombre_institucion="Hospital 1",
            tipo_institucion="hospital",
            nit="111111111",
            direccion="111 St",
            ciudad="City 1",
            pais="Country 1",
            representante="Rep 1",
            vendedor_asignado_id=None,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        ),
        Client(
            cliente_id=cliente_id_2,
            cognito_user_id="cognito-client-2",
            email="client2@example.com",
            telefono="+2222222222",
            nombre_institucion="Hospital 2",
            tipo_institucion="hospital",
            nit="222222222",
            direccion="222 St",
            ciudad="City 2",
            pais="Country 2",
            representante="Rep 2",
            vendedor_asignado_id=None,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        ),
    ]

    with patch(
        "src.adapters.input.controllers.client_controller.ListClientsUseCase"
    ) as MockUseCase:
        mock_use_case = MockUseCase.return_value
        mock_use_case.execute = AsyncMock(return_value=clients)

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/clients")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["clients"]) == 2
        assert data["clients"][0]["cliente_id"] == str(cliente_id_1)
        assert data["clients"][1]["cliente_id"] == str(cliente_id_2)


@pytest.mark.asyncio
async def test_list_clients_with_seller_filter():
    """Test listing clients filtered by seller ID."""
    app = FastAPI()
    app.include_router(router)

    cliente_id = uuid.uuid4()
    vendedor_id = uuid.uuid4()

    # Mock client
    clients = [
        Client(
            cliente_id=cliente_id,
            cognito_user_id="cognito-seller-client",
            email="sellerclient@example.com",
            telefono="+3333333333",
            nombre_institucion="Seller Hospital",
            tipo_institucion="hospital",
            nit="333333333",
            direccion="333 St",
            ciudad="City 3",
            pais="Country 3",
            representante="Rep 3",
            vendedor_asignado_id=vendedor_id,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        ),
    ]

    with patch(
        "src.adapters.input.controllers.client_controller.ListClientsUseCase"
    ) as MockUseCase:
        mock_use_case = MockUseCase.return_value
        mock_use_case.execute = AsyncMock(return_value=clients)

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get(f"/clients?vendedor_asignado_id={vendedor_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["clients"][0]["cliente_id"] == str(cliente_id)
        assert data["clients"][0]["vendedor_asignado_id"] == str(vendedor_id)


@pytest.mark.asyncio
async def test_get_client_by_id_success():
    """Test getting a client by ID."""
    app = FastAPI()
    app.include_router(router)

    cliente_id = uuid.uuid4()

    # Create mock client
    mock_client = Client(
        cliente_id=cliente_id,
        cognito_user_id="cognito-by-id",
        email="byid@example.com",
        telefono="+4444444444",
        nombre_institucion="By ID Hospital",
        tipo_institucion="hospital",
        nit="444444444",
        direccion="444 St",
        ciudad="City 4",
        pais="Country 4",
        representante="Rep 4",
        vendedor_asignado_id=None,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )

    with patch(
        "src.adapters.input.controllers.client_controller.ClientRepository"
    ) as MockRepository:
        mock_repo = MockRepository.return_value
        mock_repo.find_by_id = AsyncMock(return_value=mock_client)

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get(f"/clients/{cliente_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["cliente_id"] == str(cliente_id)
        assert data["email"] == "byid@example.com"
        assert data["nombre_institucion"] == "By ID Hospital"


@pytest.mark.asyncio
async def test_get_client_by_id_not_found():
    """Test getting a client by ID when not found."""
    from src.domain.exceptions import ClientNotFoundException
    from src.infrastructure.api.exception_handlers import register_exception_handlers

    app = FastAPI()
    register_exception_handlers(app)
    app.include_router(router)

    cliente_id = uuid.uuid4()

    with patch(
        "src.adapters.input.controllers.client_controller.ClientRepository"
    ) as MockRepository:
        mock_repo = MockRepository.return_value
        mock_repo.find_by_id = AsyncMock(return_value=None)

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get(f"/clients/{cliente_id}")

        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
