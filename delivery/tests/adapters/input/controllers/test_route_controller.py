"""Tests for Route Controller using FastAPI dependency overrides."""

import pytest
from datetime import date, timedelta
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import FastAPI, status
from httpx import ASGITransport, AsyncClient

from src.adapters.input.controllers.route_controller import router
from src.domain.entities.route import Route
from src.domain.value_objects import RouteStatus
from src.domain.exceptions import EntityNotFoundError, InvalidStatusTransitionError
from src.infrastructure.dependencies import (
    get_generate_routes_use_case,
    get_list_routes_use_case,
    get_get_route_use_case,
    get_update_route_status_use_case,
)
from src.infrastructure.database.config import get_db


class TestGenerateRoutes:
    """Tests for generate_routes endpoint."""

    @pytest.mark.asyncio
    async def test_generate_routes_success(self):
        """Test successful route generation."""
        vehicle_ids = [uuid4(), uuid4()]
        delivery_date = date.today() + timedelta(days=1)

        app = FastAPI()
        app.include_router(router, prefix="/delivery")

        # Create mocks
        mock_use_case = MagicMock()
        mock_use_case.execute = AsyncMock(return_value=None)

        mock_shipment_repo = MagicMock()
        mock_shipment_repo.find_pending_by_date = AsyncMock(return_value=[MagicMock(), MagicMock()])

        # Override dependencies
        app.dependency_overrides[get_generate_routes_use_case] = lambda: mock_use_case

        with patch(
            "src.adapters.input.controllers.route_controller.get_shipment_repository",
            return_value=mock_shipment_repo
        ):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.post(
                    "/delivery/routes/generate",
                    json={
                        "fecha_entrega_estimada": delivery_date.isoformat(),
                        "vehicle_ids": [str(vid) for vid in vehicle_ids],
                    },
                )

            assert response.status_code == status.HTTP_202_ACCEPTED
            data = response.json()
            assert data["message"] == "Route generation started"
            assert data["num_vehicles"] == 2
            assert data["num_pending_shipments"] == 2

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_generate_routes_empty_vehicle_list(self):
        """Test route generation with empty vehicle list."""
        app = FastAPI()
        app.include_router(router, prefix="/delivery")

        mock_use_case = MagicMock()
        mock_use_case.execute = AsyncMock(return_value=None)

        mock_shipment_repo = MagicMock()
        mock_shipment_repo.find_pending_by_date = AsyncMock(return_value=[])

        app.dependency_overrides[get_generate_routes_use_case] = lambda: mock_use_case

        with patch(
            "src.adapters.input.controllers.route_controller.get_shipment_repository",
            return_value=mock_shipment_repo
        ):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.post(
                    "/delivery/routes/generate",
                    json={
                        "fecha_entrega_estimada": date.today().isoformat(),
                        "vehicle_ids": [],
                    },
                )

            assert response.status_code == status.HTTP_202_ACCEPTED
            assert response.json()["num_vehicles"] == 0

        app.dependency_overrides.clear()


class TestListRoutes:
    """Tests for list_routes endpoint."""

    @pytest.mark.asyncio
    async def test_list_routes_success(self):
        """Test listing routes with results."""
        route_id = uuid4()
        vehicle_id = uuid4()

        app = FastAPI()
        app.include_router(router, prefix="/delivery")

        mock_use_case = MagicMock()
        mock_use_case.execute = AsyncMock(return_value=(
            [
                {
                    "id": str(route_id),
                    "vehicle_id": str(vehicle_id),
                    "vehicle_plate": "ABC-123",
                    "driver_name": "Juan Perez",
                    "fecha_ruta": date.today().isoformat(),
                    "estado_ruta": "planeada",
                    "duracion_estimada_minutos": 120,
                    "total_distance_km": 45.5,
                    "total_orders": 5,
                }
            ],
            1,
        ))

        app.dependency_overrides[get_list_routes_use_case] = lambda: mock_use_case

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/delivery/routes")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["vehicle_plate"] == "ABC-123"

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_list_routes_empty(self):
        """Test listing routes with no results."""
        app = FastAPI()
        app.include_router(router, prefix="/delivery")

        mock_use_case = MagicMock()
        mock_use_case.execute = AsyncMock(return_value=([], 0))

        app.dependency_overrides[get_list_routes_use_case] = lambda: mock_use_case

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/delivery/routes")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 0
        assert data["items"] == []

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_list_routes_with_filters(self):
        """Test listing routes with date and status filters."""
        app = FastAPI()
        app.include_router(router, prefix="/delivery")

        mock_use_case = MagicMock()
        mock_use_case.execute = AsyncMock(return_value=([], 0))

        app.dependency_overrides[get_list_routes_use_case] = lambda: mock_use_case

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get(
                "/delivery/routes",
                params={
                    "fecha_ruta": date.today().isoformat(),
                    "estado_ruta": "planeada",
                    "page": 2,
                    "page_size": 10,
                },
            )

        assert response.status_code == status.HTTP_200_OK
        mock_use_case.execute.assert_called_once_with(
            fecha_ruta=date.today(),
            estado_ruta="planeada",
            page=2,
            page_size=10,
        )

        app.dependency_overrides.clear()


class TestGetRoute:
    """Tests for get_route endpoint."""

    @pytest.mark.asyncio
    async def test_get_route_success(self):
        """Test getting route details."""
        route_id = uuid4()
        vehicle_id = uuid4()
        shipment_id = uuid4()
        order_id = uuid4()

        app = FastAPI()
        app.include_router(router, prefix="/delivery")

        mock_use_case = MagicMock()
        mock_use_case.execute = AsyncMock(return_value={
            "id": str(route_id),
            "vehicle_id": str(vehicle_id),
            "vehicle_plate": "ABC-123",
            "driver_name": "Juan Perez",
            "driver_phone": "555-1234",
            "fecha_ruta": date.today().isoformat(),
            "estado_ruta": "en_progreso",
            "duracion_estimada_minutos": 90,
            "total_distance_km": 30.5,
            "total_orders": 2,
            "shipments": [
                {
                    "id": str(shipment_id),
                    "order_id": str(order_id),
                    "sequence_in_route": 1,
                    "direccion_entrega": "Calle 123",
                    "ciudad_entrega": "Bogota",
                    "shipment_status": "in_transit",
                }
            ],
        })

        app.dependency_overrides[get_get_route_use_case] = lambda: mock_use_case

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get(f"/delivery/routes/{route_id}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == str(route_id)
        assert len(data["shipments"]) == 1

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_get_route_not_found(self):
        """Test getting non-existent route."""
        route_id = uuid4()

        app = FastAPI()
        app.include_router(router, prefix="/delivery")

        mock_use_case = MagicMock()
        mock_use_case.execute = AsyncMock(side_effect=EntityNotFoundError("Route", str(route_id)))

        app.dependency_overrides[get_get_route_use_case] = lambda: mock_use_case

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get(f"/delivery/routes/{route_id}")

        assert response.status_code == status.HTTP_404_NOT_FOUND

        app.dependency_overrides.clear()


class TestUpdateRouteStatus:
    """Tests for update_route_status endpoint."""

    @pytest.mark.asyncio
    async def test_update_route_status_success(self):
        """Test updating route status."""
        route_id = uuid4()
        vehicle_id = uuid4()

        app = FastAPI()
        app.include_router(router, prefix="/delivery")

        mock_route = Route(
            id=route_id,
            vehicle_id=vehicle_id,
            fecha_ruta=date.today(),
            estado_ruta=RouteStatus.EN_PROGRESO,
            duracion_estimada_minutos=60,
            total_distance_km=20.0,
            total_orders=3,
        )

        mock_use_case = MagicMock()
        mock_use_case.execute = AsyncMock(return_value=mock_route)

        app.dependency_overrides[get_update_route_status_use_case] = lambda: mock_use_case

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.patch(
                f"/delivery/routes/{route_id}/status",
                json={"estado_ruta": "en_progreso"},
            )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["estado_ruta"] == "en_progreso"

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_update_route_status_not_found(self):
        """Test updating non-existent route."""
        route_id = uuid4()

        app = FastAPI()
        app.include_router(router, prefix="/delivery")

        mock_use_case = MagicMock()
        mock_use_case.execute = AsyncMock(side_effect=EntityNotFoundError("Route", str(route_id)))

        app.dependency_overrides[get_update_route_status_use_case] = lambda: mock_use_case

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.patch(
                f"/delivery/routes/{route_id}/status",
                json={"estado_ruta": "en_progreso"},
            )

        assert response.status_code == status.HTTP_404_NOT_FOUND

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_update_route_status_invalid_transition(self):
        """Test invalid status transition."""
        route_id = uuid4()

        app = FastAPI()
        app.include_router(router, prefix="/delivery")

        mock_use_case = MagicMock()
        mock_use_case.execute = AsyncMock(
            side_effect=InvalidStatusTransitionError("Route", "planeada", "completada")
        )

        app.dependency_overrides[get_update_route_status_use_case] = lambda: mock_use_case

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.patch(
                f"/delivery/routes/{route_id}/status",
                json={"estado_ruta": "completada"},
            )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_update_route_status_invalid_value(self):
        """Test invalid status value - Pydantic validation rejects invalid enum."""
        route_id = uuid4()

        app = FastAPI()
        app.include_router(router, prefix="/delivery")

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.patch(
                f"/delivery/routes/{route_id}/status",
                json={"estado_ruta": "invalid"},
            )

        # Pydantic returns 422 for invalid enum values
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_update_route_status_value_error(self):
        """Test ValueError from use case."""
        route_id = uuid4()

        app = FastAPI()
        app.include_router(router, prefix="/delivery")

        mock_use_case = MagicMock()
        mock_use_case.execute = AsyncMock(side_effect=ValueError("Invalid status value"))

        app.dependency_overrides[get_update_route_status_use_case] = lambda: mock_use_case

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.patch(
                f"/delivery/routes/{route_id}/status",
                json={"estado_ruta": "en_progreso"},
            )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

        app.dependency_overrides.clear()
