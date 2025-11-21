"""Unit tests for delivery adapter."""

from datetime import date
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from client_app.adapters.delivery_adapter import DeliveryAdapter
from client_app.schemas.shipment_schemas import ShipmentInfo
from common.exceptions import MicroserviceHTTPError, MicroserviceConnectionError
from web.adapters.http_client import HttpClient


@pytest.fixture
def mock_http_client():
    """Create mock HTTP client."""
    return Mock(spec=HttpClient)


@pytest.fixture
def delivery_adapter(mock_http_client):
    """Create delivery adapter with mocked HTTP client."""
    return DeliveryAdapter(mock_http_client)


@pytest.fixture
def sample_shipment_data():
    """Create sample shipment data from delivery service."""
    return {
        "shipment_id": str(uuid4()),
        "shipment_status": "in_transit",
        "vehicle_plate": "ABC-123",
        "driver_name": "John Doe",
        "fecha_entrega_estimada": "2025-01-20",
        "route_id": str(uuid4()),
    }


class TestDeliveryAdapterGetShipment:
    """Tests for DeliveryAdapter.get_shipment_by_order."""

    @pytest.mark.asyncio
    async def test_get_shipment_by_order_success(self, delivery_adapter, mock_http_client, sample_shipment_data):
        """Test get_shipment_by_order returns ShipmentInfo when found."""
        order_id = uuid4()
        mock_http_client.get = AsyncMock(return_value=sample_shipment_data)

        result = await delivery_adapter.get_shipment_by_order(order_id)

        # Verify HTTP client was called with correct endpoint
        mock_http_client.get.assert_called_once_with(
            f"/delivery/orders/{order_id}/shipment"
        )

        # Verify result is ShipmentInfo instance
        assert isinstance(result, ShipmentInfo)
        assert result.shipment_status == "in_transit"
        assert result.vehicle_plate == "ABC-123"
        assert result.driver_name == "John Doe"

    @pytest.mark.asyncio
    async def test_get_shipment_by_order_with_all_fields(self, delivery_adapter, mock_http_client):
        """Test get_shipment_by_order correctly maps all shipment fields."""
        order_id = uuid4()
        shipment_id = uuid4()
        route_id = uuid4()

        shipment_data = {
            "shipment_id": str(shipment_id),
            "shipment_status": "delivered",
            "vehicle_plate": "XYZ-789",
            "driver_name": "Jane Smith",
            "fecha_entrega_estimada": "2025-01-25",
            "route_id": str(route_id),
        }
        mock_http_client.get = AsyncMock(return_value=shipment_data)

        result = await delivery_adapter.get_shipment_by_order(order_id)

        assert result.shipment_id == shipment_id
        assert result.shipment_status == "delivered"
        assert result.vehicle_plate == "XYZ-789"
        assert result.driver_name == "Jane Smith"
        assert result.route_id == route_id

    @pytest.mark.asyncio
    async def test_get_shipment_by_order_with_optional_fields_none(self, delivery_adapter, mock_http_client):
        """Test get_shipment_by_order handles optional fields as None."""
        order_id = uuid4()

        shipment_data = {
            "shipment_id": str(uuid4()),
            "shipment_status": "pending",
            "vehicle_plate": None,
            "driver_name": None,
            "fecha_entrega_estimada": "2025-01-30",
            "route_id": None,
        }
        mock_http_client.get = AsyncMock(return_value=shipment_data)

        result = await delivery_adapter.get_shipment_by_order(order_id)

        assert result.vehicle_plate is None
        assert result.driver_name is None
        assert result.route_id is None

    @pytest.mark.asyncio
    async def test_get_shipment_by_order_not_found_returns_none(
        self, delivery_adapter, mock_http_client
    ):
        """Test get_shipment_by_order returns None on 404."""
        order_id = uuid4()
        mock_http_client.get = AsyncMock(
            side_effect=MicroserviceHTTPError(
                service_name="delivery",
                status_code=404,
                response_text="Shipment not found",
            )
        )

        result = await delivery_adapter.get_shipment_by_order(order_id)

        assert result is None
        mock_http_client.get.assert_called_once_with(
            f"/delivery/orders/{order_id}/shipment"
        )

    @pytest.mark.asyncio
    async def test_get_shipment_by_order_http_error_non_404(
        self, delivery_adapter, mock_http_client
    ):
        """Test get_shipment_by_order raises on non-404 HTTP errors."""
        order_id = uuid4()
        mock_http_client.get = AsyncMock(
            side_effect=MicroserviceHTTPError(
                service_name="delivery",
                status_code=500,
                response_text="Internal server error",
            )
        )

        with pytest.raises(MicroserviceHTTPError) as exc_info:
            await delivery_adapter.get_shipment_by_order(order_id)

        assert exc_info.value.status_code == 500

    @pytest.mark.asyncio
    async def test_get_shipment_by_order_forbidden_error(
        self, delivery_adapter, mock_http_client
    ):
        """Test get_shipment_by_order raises on 403 Forbidden."""
        order_id = uuid4()
        mock_http_client.get = AsyncMock(
            side_effect=MicroserviceHTTPError(
                service_name="delivery",
                status_code=403,
                response_text="Forbidden",
            )
        )

        with pytest.raises(MicroserviceHTTPError) as exc_info:
            await delivery_adapter.get_shipment_by_order(order_id)

        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_get_shipment_by_order_bad_request_error(
        self, delivery_adapter, mock_http_client
    ):
        """Test get_shipment_by_order raises on 400 Bad Request."""
        order_id = uuid4()
        mock_http_client.get = AsyncMock(
            side_effect=MicroserviceHTTPError(
                service_name="delivery",
                status_code=400,
                response_text="Bad request",
            )
        )

        with pytest.raises(MicroserviceHTTPError) as exc_info:
            await delivery_adapter.get_shipment_by_order(order_id)

        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_get_shipment_by_order_connection_error(
        self, delivery_adapter, mock_http_client
    ):
        """Test get_shipment_by_order raises on connection errors."""
        order_id = uuid4()
        mock_http_client.get = AsyncMock(
            side_effect=MicroserviceConnectionError(
                service_name="delivery",
                original_error="Connection refused",
            )
        )

        with pytest.raises(MicroserviceConnectionError):
            await delivery_adapter.get_shipment_by_order(order_id)

    @pytest.mark.asyncio
    async def test_get_shipment_by_order_timeout_error(
        self, delivery_adapter, mock_http_client
    ):
        """Test get_shipment_by_order raises on timeout errors."""
        order_id = uuid4()
        mock_http_client.get = AsyncMock(
            side_effect=MicroserviceConnectionError(
                service_name="delivery",
                original_error="Request timeout",
            )
        )

        with pytest.raises(MicroserviceConnectionError):
            await delivery_adapter.get_shipment_by_order(order_id)

    @pytest.mark.asyncio
    async def test_get_shipment_by_order_multiple_calls(
        self, delivery_adapter, mock_http_client, sample_shipment_data
    ):
        """Test multiple sequential calls to get_shipment_by_order."""
        order_id_1 = uuid4()
        order_id_2 = uuid4()

        mock_http_client.get = AsyncMock(return_value=sample_shipment_data)

        result_1 = await delivery_adapter.get_shipment_by_order(order_id_1)
        result_2 = await delivery_adapter.get_shipment_by_order(order_id_2)

        assert isinstance(result_1, ShipmentInfo)
        assert isinstance(result_2, ShipmentInfo)
        assert mock_http_client.get.call_count == 2

    @pytest.mark.asyncio
    async def test_get_shipment_by_order_correct_endpoint_url(
        self, delivery_adapter, mock_http_client, sample_shipment_data
    ):
        """Test that correct endpoint URL is constructed."""
        order_id = uuid4()
        mock_http_client.get = AsyncMock(return_value=sample_shipment_data)

        await delivery_adapter.get_shipment_by_order(order_id)

        expected_endpoint = f"/delivery/orders/{order_id}/shipment"
        mock_http_client.get.assert_called_once_with(expected_endpoint)
