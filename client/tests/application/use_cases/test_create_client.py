"""Tests for CreateClientUseCase."""
import pytest

from src.adapters.output.repositories.client_repository import ClientRepository
from src.application.use_cases.create_client import CreateClientUseCase
from src.domain.exceptions import DuplicateCognitoUserException, DuplicateNITException


@pytest.mark.asyncio
async def test_create_client_success(db_session):
    """Test successful client creation."""
    repo = ClientRepository(db_session)
    use_case = CreateClientUseCase(repo)

    client_data = {
        "cognito_user_id": "cognito-test-123",
        "email": "test@hospital.com",
        "telefono": "+1234567890",
        "nombre_institucion": "Test Hospital",
        "tipo_institucion": "hospital",
        "nit": "123456789",
        "direccion": "123 Test St",
        "ciudad": "Test City",
        "pais": "Test Country",
        "representante": "John Doe",
        "vendedor_asignado_id": None
    }

    client = await use_case.execute(client_data)

    assert client.cliente_id is not None
    assert client.cognito_user_id == "cognito-test-123"
    assert client.email == "test@hospital.com"
    assert client.nombre_institucion == "Test Hospital"


@pytest.mark.asyncio
async def test_create_client_duplicate_nit(db_session):
    """Test creating client with duplicate NIT raises exception."""
    repo = ClientRepository(db_session)
    use_case = CreateClientUseCase(repo)

    client_data = {
        "cognito_user_id": "cognito-first",
        "email": "first@hospital.com",
        "telefono": "+1234567890",
        "nombre_institucion": "First Hospital",
        "tipo_institucion": "hospital",
        "nit": "999888777",
        "direccion": "123 Test St",
        "ciudad": "Test City",
        "pais": "Test Country",
        "representante": "John Doe",
        "vendedor_asignado_id": None
    }

    # Create first client
    await use_case.execute(client_data)

    # Try to create second client with same NIT
    duplicate_data = client_data.copy()
    duplicate_data["cognito_user_id"] = "cognito-second"
    duplicate_data["email"] = "second@hospital.com"

    with pytest.raises(DuplicateNITException) as exc_info:
        await use_case.execute(duplicate_data)

    assert "999888777" in str(exc_info.value)


@pytest.mark.asyncio
async def test_create_client_duplicate_cognito_user_id(db_session):
    """Test creating client with duplicate Cognito User ID raises exception."""
    repo = ClientRepository(db_session)
    use_case = CreateClientUseCase(repo)

    client_data = {
        "cognito_user_id": "cognito-duplicate",
        "email": "first@hospital.com",
        "telefono": "+1234567890",
        "nombre_institucion": "First Hospital",
        "tipo_institucion": "hospital",
        "nit": "111222333",
        "direccion": "123 Test St",
        "ciudad": "Test City",
        "pais": "Test Country",
        "representante": "John Doe",
        "vendedor_asignado_id": None
    }

    # Create first client
    await use_case.execute(client_data)

    # Try to create second client with same Cognito User ID
    duplicate_data = client_data.copy()
    duplicate_data["nit"] = "444555666"
    duplicate_data["email"] = "second@hospital.com"

    with pytest.raises(DuplicateCognitoUserException) as exc_info:
        await use_case.execute(duplicate_data)

    assert "cognito-duplicate" in str(exc_info.value)
