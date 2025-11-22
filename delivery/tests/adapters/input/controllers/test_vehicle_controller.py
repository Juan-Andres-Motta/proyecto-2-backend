"""Tests for Vehicle Controller using FastAPI dependency overrides."""

import pytest
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock

from fastapi import FastAPI, status
from httpx import ASGITransport, AsyncClient

from src.adapters.input.controllers.vehicle_controller import router
from src.domain.entities.vehicle import Vehicle
from src.domain.exceptions import EntityNotFoundError, ValidationError
from src.infrastructure.dependencies import (
    get_create_vehicle_use_case,
    get_delete_vehicle_use_case,
    get_list_vehicles_use_case,
    get_update_vehicle_use_case,
)


class TestListVehicles:
    """Tests for list_vehicles endpoint."""

    @pytest.mark.asyncio
    async def test_list_vehicles_success(self):
        """Test listing vehicles."""
        vehicle_id = uuid4()

        app = FastAPI()
        app.include_router(router, prefix="/delivery")

        mock_vehicle = Vehicle(
            id=vehicle_id,
            placa="ABC-123",
            driver_name="Juan Perez",
            driver_phone="555-1234",
            is_active=True,
        )

        mock_use_case = MagicMock()
        mock_use_case.execute = AsyncMock(return_value=[mock_vehicle])

        app.dependency_overrides[get_list_vehicles_use_case] = lambda: mock_use_case

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/delivery/vehicles")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["placa"] == "ABC-123"

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_list_vehicles_empty(self):
        """Test listing vehicles with no results."""
        app = FastAPI()
        app.include_router(router, prefix="/delivery")

        mock_use_case = MagicMock()
        mock_use_case.execute = AsyncMock(return_value=[])

        app.dependency_overrides[get_list_vehicles_use_case] = lambda: mock_use_case

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/delivery/vehicles")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 0
        assert data["items"] == []

        app.dependency_overrides.clear()


class TestCreateVehicle:
    """Tests for create_vehicle endpoint."""

    @pytest.mark.asyncio
    async def test_create_vehicle_success(self):
        """Test creating a vehicle."""
        vehicle_id = uuid4()

        app = FastAPI()
        app.include_router(router, prefix="/delivery")

        mock_vehicle = Vehicle(
            id=vehicle_id,
            placa="ABC-123",
            driver_name="Juan Perez",
            driver_phone="555-1234",
            is_active=True,
        )

        mock_use_case = MagicMock()
        mock_use_case.execute = AsyncMock(return_value=mock_vehicle)

        app.dependency_overrides[get_create_vehicle_use_case] = lambda: mock_use_case

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/delivery/vehicles",
                json={
                    "placa": "ABC-123",
                    "driver_name": "Juan Perez",
                    "driver_phone": "555-1234",
                },
            )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["placa"] == "ABC-123"
        assert data["driver_name"] == "Juan Perez"

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_create_vehicle_validation_error(self):
        """Test creating a vehicle with validation error."""
        app = FastAPI()
        app.include_router(router, prefix="/delivery")

        mock_use_case = MagicMock()
        mock_use_case.execute = AsyncMock(
            side_effect=ValidationError("Vehicle with plate ABC-123 already exists")
        )

        app.dependency_overrides[get_create_vehicle_use_case] = lambda: mock_use_case

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/delivery/vehicles",
                json={
                    "placa": "ABC-123",
                    "driver_name": "Juan Perez",
                    "driver_phone": "555-1234",
                },
            )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

        app.dependency_overrides.clear()


class TestUpdateVehicle:
    """Tests for update_vehicle endpoint."""

    @pytest.mark.asyncio
    async def test_update_vehicle_success(self):
        """Test updating a vehicle."""
        vehicle_id = uuid4()

        app = FastAPI()
        app.include_router(router, prefix="/delivery")

        mock_vehicle = Vehicle(
            id=vehicle_id,
            placa="ABC-123",
            driver_name="Pedro Garcia",
            driver_phone="555-5678",
            is_active=True,
        )

        mock_use_case = MagicMock()
        mock_use_case.execute = AsyncMock(return_value=mock_vehicle)

        app.dependency_overrides[get_update_vehicle_use_case] = lambda: mock_use_case

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.put(
                f"/delivery/vehicles/{vehicle_id}",
                json={
                    "driver_name": "Pedro Garcia",
                    "driver_phone": "555-5678",
                },
            )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["driver_name"] == "Pedro Garcia"
        assert data["driver_phone"] == "555-5678"

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_update_vehicle_not_found(self):
        """Test updating non-existent vehicle."""
        vehicle_id = uuid4()

        app = FastAPI()
        app.include_router(router, prefix="/delivery")

        mock_use_case = MagicMock()
        mock_use_case.execute = AsyncMock(
            side_effect=EntityNotFoundError("Vehicle", str(vehicle_id))
        )

        app.dependency_overrides[get_update_vehicle_use_case] = lambda: mock_use_case

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.put(
                f"/delivery/vehicles/{vehicle_id}",
                json={
                    "driver_name": "Pedro Garcia",
                    "driver_phone": "555-5678",
                },
            )

        assert response.status_code == status.HTTP_404_NOT_FOUND

        app.dependency_overrides.clear()


class TestDeleteVehicle:
    """Tests for delete_vehicle endpoint."""

    @pytest.mark.asyncio
    async def test_delete_vehicle_success(self):
        """Test deleting a vehicle."""
        vehicle_id = uuid4()

        app = FastAPI()
        app.include_router(router, prefix="/delivery")

        mock_use_case = MagicMock()
        mock_use_case.execute = AsyncMock(return_value=None)

        app.dependency_overrides[get_delete_vehicle_use_case] = lambda: mock_use_case

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.delete(f"/delivery/vehicles/{vehicle_id}")

        assert response.status_code == status.HTTP_204_NO_CONTENT

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_delete_vehicle_not_found(self):
        """Test deleting non-existent vehicle."""
        vehicle_id = uuid4()

        app = FastAPI()
        app.include_router(router, prefix="/delivery")

        mock_use_case = MagicMock()
        mock_use_case.execute = AsyncMock(
            side_effect=EntityNotFoundError("Vehicle", str(vehicle_id))
        )

        app.dependency_overrides[get_delete_vehicle_use_case] = lambda: mock_use_case

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.delete(f"/delivery/vehicles/{vehicle_id}")

        assert response.status_code == status.HTTP_404_NOT_FOUND

        app.dependency_overrides.clear()
