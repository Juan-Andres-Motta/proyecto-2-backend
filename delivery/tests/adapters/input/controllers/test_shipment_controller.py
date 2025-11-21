"""Tests for Shipment Controller using FastAPI dependency overrides."""

import pytest
from datetime import date, datetime
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock

from fastapi import FastAPI, status
from httpx import ASGITransport, AsyncClient

from src.adapters.input.controllers.shipment_controller import router
from src.domain.entities.shipment import Shipment
from src.domain.value_objects import ShipmentStatus
from src.domain.exceptions import EntityNotFoundError, InvalidStatusTransitionError
from src.infrastructure.dependencies import (
    get_get_shipment_by_order_use_case,
    get_update_shipment_status_use_case,
)


class TestGetShipment:
    """Tests for get_shipment endpoint."""

    @pytest.mark.asyncio
    async def test_get_shipment_success(self):
        """Test getting shipment by order ID."""
        order_id = uuid4()
        shipment_id = uuid4()
        route_id = uuid4()

        app = FastAPI()
        app.include_router(router, prefix="/delivery")

        mock_use_case = MagicMock()
        mock_use_case.execute = AsyncMock(return_value={
            "shipment_id": str(shipment_id),
            "order_id": str(order_id),
            "shipment_status": "pending",
            "vehicle_plate": "ABC-123",
            "driver_name": "Juan Perez",
            "fecha_entrega_estimada": date.today().isoformat(),
            "route_id": str(route_id),
        })

        app.dependency_overrides[get_get_shipment_by_order_use_case] = lambda: mock_use_case

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get(f"/delivery/shipments/{order_id}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["shipment_id"] == str(shipment_id)
        assert data["order_id"] == str(order_id)
        assert data["vehicle_plate"] == "ABC-123"

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_get_shipment_not_found(self):
        """Test getting shipment for non-existent order."""
        order_id = uuid4()

        app = FastAPI()
        app.include_router(router, prefix="/delivery")

        mock_use_case = MagicMock()
        mock_use_case.execute = AsyncMock(
            side_effect=EntityNotFoundError("Shipment", str(order_id))
        )

        app.dependency_overrides[get_get_shipment_by_order_use_case] = lambda: mock_use_case

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get(f"/delivery/shipments/{order_id}")

        assert response.status_code == status.HTTP_404_NOT_FOUND

        app.dependency_overrides.clear()


class TestUpdateShipmentStatus:
    """Tests for update_shipment_status endpoint."""

    @pytest.mark.asyncio
    async def test_update_shipment_status_success(self):
        """Test updating shipment status."""
        order_id = uuid4()
        shipment_id = uuid4()
        route_id = uuid4()

        app = FastAPI()
        app.include_router(router, prefix="/delivery")

        mock_shipment = Shipment(
            id=shipment_id,
            order_id=order_id,
            customer_id=uuid4(),
            route_id=route_id,
            direccion_entrega="Calle 123",
            ciudad_entrega="Bogota",
            pais_entrega="Colombia",
            latitude=-74.0,
            longitude=4.6,
            fecha_pedido=datetime.now(),
            fecha_entrega_estimada=date.today(),
            shipment_status=ShipmentStatus.IN_TRANSIT,
        )

        mock_use_case = MagicMock()
        mock_use_case.execute = AsyncMock(return_value=mock_shipment)

        app.dependency_overrides[get_update_shipment_status_use_case] = lambda: mock_use_case

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.patch(
                f"/delivery/shipments/{order_id}/status",
                json={"shipment_status": "in_transit"},
            )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["shipment_status"] == "in_transit"
        assert data["message"] == "Shipment status updated successfully"

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_update_shipment_status_not_found(self):
        """Test updating non-existent shipment."""
        order_id = uuid4()

        app = FastAPI()
        app.include_router(router, prefix="/delivery")

        mock_use_case = MagicMock()
        mock_use_case.execute = AsyncMock(
            side_effect=EntityNotFoundError("Shipment", str(order_id))
        )

        app.dependency_overrides[get_update_shipment_status_use_case] = lambda: mock_use_case

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.patch(
                f"/delivery/shipments/{order_id}/status",
                json={"shipment_status": "in_transit"},
            )

        assert response.status_code == status.HTTP_404_NOT_FOUND

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_update_shipment_status_invalid_transition(self):
        """Test invalid status transition."""
        order_id = uuid4()

        app = FastAPI()
        app.include_router(router, prefix="/delivery")

        mock_use_case = MagicMock()
        mock_use_case.execute = AsyncMock(
            side_effect=InvalidStatusTransitionError("Shipment", "pending", "delivered")
        )

        app.dependency_overrides[get_update_shipment_status_use_case] = lambda: mock_use_case

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.patch(
                f"/delivery/shipments/{order_id}/status",
                json={"shipment_status": "delivered"},
            )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_update_shipment_status_value_error(self):
        """Test value error in status update."""
        order_id = uuid4()

        app = FastAPI()
        app.include_router(router, prefix="/delivery")

        mock_use_case = MagicMock()
        mock_use_case.execute = AsyncMock(side_effect=ValueError("Invalid status"))

        app.dependency_overrides[get_update_shipment_status_use_case] = lambda: mock_use_case

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.patch(
                f"/delivery/shipments/{order_id}/status",
                json={"shipment_status": "in_transit"},
            )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

        app.dependency_overrides.clear()
