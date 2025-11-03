"""Tests for sellers app client adapter."""
import pytest
from unittest.mock import AsyncMock
from uuid import uuid4

from sellers_app.adapters.client_adapter import ClientAdapter
from sellers_app.schemas.client_schemas import ClientCreateInput


@pytest.mark.asyncio
async def test_create_client_success():
    """Test creating client successfully."""
    mock_http_client = AsyncMock()
    mock_http_client.post = AsyncMock(return_value={"cliente_id": "123", "message": "Client created"})

    adapter = ClientAdapter(mock_http_client)
    client_input = ClientCreateInput(
        cognito_user_id="cognito-123",
        email="test@hospital.com",
        telefono="+1234567890",
        nombre_institucion="Test Hospital",
        tipo_institucion="Hospital",
        nit="123456789",
        direccion="123 Test St",
        ciudad="Test City",
        pais="US",
        representante="John Doe"
    )

    result = await adapter.create_client(client_input)

    assert result == {"cliente_id": "123", "message": "Client created"}
    mock_http_client.post.assert_called_once()


@pytest.mark.asyncio
async def test_list_clients_without_filter():
    """Test listing all clients without filter."""
    from datetime import datetime
    mock_http_client = AsyncMock()
    mock_http_client.get = AsyncMock(return_value={
        "clients": [{
            "cliente_id": str(uuid4()),
            "cognito_user_id": "cognito-123",
            "email": "test@hospital.com",
            "telefono": "+1234567890",
            "nombre_institucion": "Test Hospital",
            "tipo_institucion": "Hospital",
            "nit": "123456789",
            "direccion": "123 Test St",
            "ciudad": "Test City",
            "pais": "US",
            "representante": "John Doe",
            "vendedor_asignado_id": None,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }],
        "total": 1
    })

    adapter = ClientAdapter(mock_http_client)

    result = await adapter.list_clients()

    assert result.total == 1
    assert len(result.clients) == 1
    mock_http_client.get.assert_called_once_with("/client/clients", params={})


@pytest.mark.asyncio
async def test_list_clients_with_seller_filter():
    """Test listing clients filtered by seller."""
    from datetime import datetime
    mock_http_client = AsyncMock()
    seller_id = uuid4()
    mock_http_client.get = AsyncMock(return_value={
        "clients": [{
            "cliente_id": str(uuid4()),
            "cognito_user_id": "cognito-123",
            "email": "test@hospital.com",
            "telefono": "+1234567890",
            "nombre_institucion": "Test Hospital",
            "tipo_institucion": "Hospital",
            "nit": "123456789",
            "direccion": "123 Test St",
            "ciudad": "Test City",
            "pais": "US",
            "representante": "John Doe",
            "vendedor_asignado_id": str(seller_id),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }],
        "total": 1
    })

    adapter = ClientAdapter(mock_http_client)

    result = await adapter.list_clients(vendedor_asignado_id=seller_id)

    assert result.total == 1
    mock_http_client.get.assert_called_once_with(
        "/client/clients",
        params={"vendedor_asignado_id": str(seller_id)}
    )


@pytest.mark.asyncio
async def test_get_client_by_id_success():
    """Test getting client by ID successfully."""
    from datetime import datetime
    mock_http_client = AsyncMock()
    client_id = uuid4()
    mock_http_client.get = AsyncMock(return_value={
        "cliente_id": str(client_id),
        "cognito_user_id": "cognito-123",
        "email": "test@hospital.com",
        "telefono": "+1234567890",
        "nombre_institucion": "Test Hospital",
        "tipo_institucion": "Hospital",
        "nit": "123456789",
        "direccion": "123 Test St",
        "ciudad": "Test City",
        "pais": "US",
        "representante": "John Doe",
        "vendedor_asignado_id": None,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    })

    adapter = ClientAdapter(mock_http_client)

    result = await adapter.get_client_by_id(client_id)

    assert result.cliente_id == client_id
    assert result.nombre_institucion == "Test Hospital"
    mock_http_client.get.assert_called_once_with(f"/client/clients/{client_id}")


@pytest.mark.asyncio
async def test_assign_seller_success():
    """Test assigning seller to client successfully."""
    mock_http_client = AsyncMock()
    client_id = uuid4()
    seller_id = uuid4()
    mock_http_client.patch = AsyncMock()

    adapter = ClientAdapter(mock_http_client)

    await adapter.assign_seller(client_id, seller_id)

    mock_http_client.patch.assert_called_once_with(
        f"/client/clients/{client_id}/assign-seller",
        json={"vendedor_asignado_id": str(seller_id)}
    )
