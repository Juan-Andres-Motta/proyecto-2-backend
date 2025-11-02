"""Tests for AssignSellerUseCase."""
import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.application.use_cases.assign_seller import AssignSellerUseCase
from src.domain.entities.client import Client
from src.domain.exceptions import ClientAlreadyAssignedException, ClientNotFoundException


@pytest.mark.asyncio
async def test_assign_seller_success():
    """Test successful seller assignment to unassigned client."""
    # Arrange
    cliente_id = uuid.uuid4()
    vendedor_id = uuid.uuid4()
    now = datetime.now()

    mock_client = Client(
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
        vendedor_asignado_id=None,  # Not assigned yet
        created_at=now,
        updated_at=now
    )

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
        vendedor_asignado_id=vendedor_id,  # Now assigned
        created_at=now,
        updated_at=now
    )

    mock_repo = MagicMock()
    mock_repo.find_by_id = AsyncMock(return_value=mock_client)
    mock_repo.update = AsyncMock(return_value=updated_client)

    use_case = AssignSellerUseCase(mock_repo)

    # Act
    result = await use_case.execute(cliente_id, vendedor_id)

    # Assert
    assert result.cliente_id == cliente_id
    assert result.vendedor_asignado_id == vendedor_id
    mock_repo.find_by_id.assert_awaited_once_with(cliente_id)
    mock_repo.update.assert_awaited_once()


@pytest.mark.asyncio
async def test_assign_seller_idempotent_same_seller():
    """Test assigning the same seller again is idempotent."""
    # Arrange
    cliente_id = uuid.uuid4()
    vendedor_id = uuid.uuid4()
    now = datetime.now()

    mock_client = Client(
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
        vendedor_asignado_id=vendedor_id,  # Already assigned to this seller
        created_at=now,
        updated_at=now
    )

    mock_repo = MagicMock()
    mock_repo.find_by_id = AsyncMock(return_value=mock_client)
    mock_repo.update = AsyncMock()  # Should not be called

    use_case = AssignSellerUseCase(mock_repo)

    # Act
    result = await use_case.execute(cliente_id, vendedor_id)

    # Assert
    assert result.cliente_id == cliente_id
    assert result.vendedor_asignado_id == vendedor_id
    mock_repo.find_by_id.assert_awaited_once_with(cliente_id)
    mock_repo.update.assert_not_awaited()  # No update needed


@pytest.mark.asyncio
async def test_assign_seller_client_not_found():
    """Test assigning seller to non-existent client raises exception."""
    # Arrange
    cliente_id = uuid.uuid4()
    vendedor_id = uuid.uuid4()

    mock_repo = MagicMock()
    mock_repo.find_by_id = AsyncMock(return_value=None)

    use_case = AssignSellerUseCase(mock_repo)

    # Act & Assert
    with pytest.raises(ClientNotFoundException) as exc_info:
        await use_case.execute(cliente_id, vendedor_id)

    assert exc_info.value.cliente_id == cliente_id
    assert exc_info.value.error_code == "CLIENT_NOT_FOUND"
    mock_repo.find_by_id.assert_awaited_once_with(cliente_id)


@pytest.mark.asyncio
async def test_assign_seller_already_assigned_to_different_seller():
    """Test assigning seller when client already assigned to different seller."""
    # Arrange
    cliente_id = uuid.uuid4()
    existing_vendedor_id = uuid.uuid4()
    new_vendedor_id = uuid.uuid4()
    now = datetime.now()

    mock_client = Client(
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
        vendedor_asignado_id=existing_vendedor_id,  # Already assigned
        created_at=now,
        updated_at=now
    )

    mock_repo = MagicMock()
    mock_repo.find_by_id = AsyncMock(return_value=mock_client)

    use_case = AssignSellerUseCase(mock_repo)

    # Act & Assert
    with pytest.raises(ClientAlreadyAssignedException) as exc_info:
        await use_case.execute(cliente_id, new_vendedor_id)

    assert exc_info.value.cliente_id == cliente_id
    assert exc_info.value.vendedor_asignado_id == existing_vendedor_id
    assert exc_info.value.error_code == "CLIENT_ALREADY_ASSIGNED"
    mock_repo.find_by_id.assert_awaited_once_with(cliente_id)
