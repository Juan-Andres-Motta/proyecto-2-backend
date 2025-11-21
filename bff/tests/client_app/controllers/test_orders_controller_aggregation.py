"""Unit tests for orders controller aggregation with delivery service integration."""

from datetime import date, datetime
from unittest.mock import AsyncMock, Mock
from uuid import UUID, uuid4

import pytest
from fastapi import HTTPException

from client_app.controllers.orders_controller import (
    _enrich_orders_with_shipments,
    _fetch_shipment_safe,
    list_my_orders,
)
from client_app.ports.client_port import ClientPort
from client_app.ports.delivery_port import DeliveryPort
from client_app.ports.order_port import OrderPort
from client_app.schemas.order_schemas import (
    OrderItemResponse,
    OrderResponse,
    PaginatedOrdersResponse,
)
from client_app.schemas.shipment_schemas import ShipmentInfo
from common.exceptions import MicroserviceConnectionError, MicroserviceHTTPError


@pytest.fixture
def mock_order_port():
    """Create a mock order port."""
    return Mock(spec=OrderPort)


@pytest.fixture
def mock_client_port():
    """Create a mock client port."""
    return Mock(spec=ClientPort)


@pytest.fixture
def mock_delivery_port():
    """Create a mock delivery port."""
    return Mock(spec=DeliveryPort)


@pytest.fixture
def mock_user():
    """Create a mock authenticated user."""
    return {
        "sub": "cognito-user-123",
        "email": "test@example.com",
        "custom:user_type": "client",
    }


@pytest.fixture
def sample_shipment():
    """Create sample shipment info."""
    return ShipmentInfo(
        shipment_id=uuid4(),
        shipment_status="in_transit",
        vehicle_plate="ABC-123",
        driver_name="John Doe",
        fecha_entrega_estimada=date(2025, 1, 20),
        route_id=uuid4(),
    )


@pytest.fixture
def sample_order_item():
    """Create sample order item response."""
    return OrderItemResponse(
        id=uuid4(),
        pedido_id=uuid4(),
        inventario_id=uuid4(),
        cantidad=5,
        precio_unitario=100.0,
        precio_total=500.0,
        product_name="Test Product",
        product_sku="TEST-001",
        warehouse_id=uuid4(),
        warehouse_name="Warehouse A",
        warehouse_city="Bogota",
        warehouse_country="Colombia",
        batch_number="BATCH-001",
        expiration_date=date(2026, 12, 31),
        created_at=datetime(2025, 1, 1, 10, 0, 0),
        updated_at=datetime(2025, 1, 1, 10, 0, 0),
    )


@pytest.fixture
def sample_order(sample_order_item):
    """Create sample order response."""
    return OrderResponse(
        id=uuid4(),
        customer_id=uuid4(),
        seller_id=None,
        route_id=None,
        fecha_pedido=datetime(2025, 1, 1, 10, 0, 0),
        fecha_entrega_estimada=date(2025, 1, 20),
        metodo_creacion="app_cliente",
        direccion_entrega="Calle 123",
        ciudad_entrega="Bogota",
        pais_entrega="Colombia",
        customer_name="Test Customer",
        customer_phone="+1234567890",
        customer_email="customer@test.com",
        seller_name=None,
        seller_email=None,
        monto_total=500.0,
        created_at=datetime(2025, 1, 1, 10, 0, 0),
        updated_at=datetime(2025, 1, 1, 10, 0, 0),
        items=[sample_order_item],
        shipment=None,
    )


@pytest.fixture
def paginated_orders_response(sample_order):
    """Create paginated orders response with one order."""
    return PaginatedOrdersResponse(
        items=[sample_order],
        total=1,
        page=1,
        size=10,
        has_next=False,
        has_previous=False,
    )


class TestFetchShipmentSafe:
    """Tests for _fetch_shipment_safe helper function."""

    @pytest.mark.asyncio
    async def test_fetch_shipment_safe_returns_shipment_info(self, mock_delivery_port, sample_shipment):
        """Test _fetch_shipment_safe returns ShipmentInfo when successful."""
        order_id = uuid4()
        mock_delivery_port.get_shipment_by_order = AsyncMock(return_value=sample_shipment)

        result = await _fetch_shipment_safe(mock_delivery_port, order_id)

        assert result == sample_shipment
        mock_delivery_port.get_shipment_by_order.assert_called_once_with(order_id)

    @pytest.mark.asyncio
    async def test_fetch_shipment_safe_returns_none_on_not_found(self, mock_delivery_port):
        """Test _fetch_shipment_safe returns None when shipment not found."""
        order_id = uuid4()
        mock_delivery_port.get_shipment_by_order = AsyncMock(return_value=None)

        result = await _fetch_shipment_safe(mock_delivery_port, order_id)

        assert result is None

    @pytest.mark.asyncio
    async def test_fetch_shipment_safe_handles_http_error_gracefully(self, mock_delivery_port):
        """Test _fetch_shipment_safe returns None on HTTP error."""
        order_id = uuid4()
        mock_delivery_port.get_shipment_by_order = AsyncMock(
            side_effect=MicroserviceHTTPError(
                service_name="delivery",
                status_code=500,
                response_text="Internal server error",
            )
        )

        result = await _fetch_shipment_safe(mock_delivery_port, order_id)

        assert result is None

    @pytest.mark.asyncio
    async def test_fetch_shipment_safe_handles_connection_error_gracefully(self, mock_delivery_port):
        """Test _fetch_shipment_safe returns None on connection error."""
        order_id = uuid4()
        mock_delivery_port.get_shipment_by_order = AsyncMock(
            side_effect=MicroserviceConnectionError(
                service_name="delivery",
                original_error="Connection refused",
            )
        )

        result = await _fetch_shipment_safe(mock_delivery_port, order_id)

        assert result is None

    @pytest.mark.asyncio
    async def test_fetch_shipment_safe_handles_generic_exception(self, mock_delivery_port):
        """Test _fetch_shipment_safe handles any exception gracefully."""
        order_id = uuid4()
        mock_delivery_port.get_shipment_by_order = AsyncMock(
            side_effect=Exception("Unexpected error")
        )

        result = await _fetch_shipment_safe(mock_delivery_port, order_id)

        assert result is None


class TestEnrichOrdersWithShipments:
    """Tests for _enrich_orders_with_shipments function."""

    @pytest.mark.asyncio
    async def test_enrich_orders_with_shipment_info(
        self, mock_delivery_port, sample_order, sample_shipment
    ):
        """Test enrich_orders adds shipment info to orders."""
        mock_delivery_port.get_shipment_by_order = AsyncMock(return_value=sample_shipment)

        # Create order with no shipment
        order = sample_order
        order.shipment = None
        orders = [order]

        result = await _enrich_orders_with_shipments(orders, mock_delivery_port)

        assert len(result) == 1
        assert result[0].shipment == sample_shipment
        mock_delivery_port.get_shipment_by_order.assert_called_once_with(order.id)

    @pytest.mark.asyncio
    async def test_enrich_orders_without_shipment(self, mock_delivery_port, sample_order):
        """Test enrich_orders sets shipment to None when not found."""
        mock_delivery_port.get_shipment_by_order = AsyncMock(return_value=None)

        orders = [sample_order]

        result = await _enrich_orders_with_shipments(orders, mock_delivery_port)

        assert len(result) == 1
        assert result[0].shipment is None

    @pytest.mark.asyncio
    async def test_enrich_orders_parallel_fetching(
        self, mock_delivery_port, sample_order, sample_shipment
    ):
        """Test multiple orders fetch shipments in parallel."""
        # Create 3 independent orders with different IDs
        order_1 = OrderResponse(
            id=uuid4(),
            customer_id=uuid4(),
            seller_id=None,
            route_id=None,
            fecha_pedido=datetime(2025, 1, 1, 10, 0, 0),
            fecha_entrega_estimada=date(2025, 1, 20),
            metodo_creacion="app_cliente",
            direccion_entrega="Calle 123",
            ciudad_entrega="Bogota",
            pais_entrega="Colombia",
            customer_name="Test Customer",
            customer_phone="+1234567890",
            customer_email="customer@test.com",
            seller_name=None,
            seller_email=None,
            monto_total=500.0,
            created_at=datetime(2025, 1, 1, 10, 0, 0),
            updated_at=datetime(2025, 1, 1, 10, 0, 0),
            items=[],
            shipment=None,
        )

        order_2 = OrderResponse(
            id=uuid4(),
            customer_id=uuid4(),
            seller_id=None,
            route_id=None,
            fecha_pedido=datetime(2025, 1, 1, 10, 0, 0),
            fecha_entrega_estimada=date(2025, 1, 20),
            metodo_creacion="app_cliente",
            direccion_entrega="Calle 456",
            ciudad_entrega="Medellin",
            pais_entrega="Colombia",
            customer_name="Test Customer 2",
            customer_phone="+0987654321",
            customer_email="customer2@test.com",
            seller_name=None,
            seller_email=None,
            monto_total=600.0,
            created_at=datetime(2025, 1, 1, 10, 0, 0),
            updated_at=datetime(2025, 1, 1, 10, 0, 0),
            items=[],
            shipment=None,
        )

        order_3 = OrderResponse(
            id=uuid4(),
            customer_id=uuid4(),
            seller_id=None,
            route_id=None,
            fecha_pedido=datetime(2025, 1, 1, 10, 0, 0),
            fecha_entrega_estimada=date(2025, 1, 20),
            metodo_creacion="app_cliente",
            direccion_entrega="Calle 789",
            ciudad_entrega="Cali",
            pais_entrega="Colombia",
            customer_name="Test Customer 3",
            customer_phone="+5555555555",
            customer_email="customer3@test.com",
            seller_name=None,
            seller_email=None,
            monto_total=700.0,
            created_at=datetime(2025, 1, 1, 10, 0, 0),
            updated_at=datetime(2025, 1, 1, 10, 0, 0),
            items=[],
            shipment=None,
        )

        orders = [order_1, order_2, order_3]

        # Mock delivery port to return shipment for first two, None for third
        mock_delivery_port.get_shipment_by_order = AsyncMock(
            side_effect=[sample_shipment, sample_shipment, None]
        )

        result = await _enrich_orders_with_shipments(orders, mock_delivery_port)

        assert len(result) == 3
        assert result[0].shipment == sample_shipment
        assert result[1].shipment == sample_shipment
        assert result[2].shipment is None
        # Verify all three orders were fetched
        assert mock_delivery_port.get_shipment_by_order.call_count == 3

    @pytest.mark.asyncio
    async def test_enrich_orders_shipment_fetch_error_graceful(
        self, mock_delivery_port, sample_order
    ):
        """Test shipment errors don't break order listing."""
        mock_delivery_port.get_shipment_by_order = AsyncMock(
            side_effect=Exception("Delivery service error")
        )

        orders = [sample_order]

        result = await _enrich_orders_with_shipments(orders, mock_delivery_port)

        # Order should still be in result with shipment as None
        assert len(result) == 1
        assert result[0].shipment is None

    @pytest.mark.asyncio
    async def test_enrich_orders_empty_list(self, mock_delivery_port):
        """Test enrich_orders handles empty list."""
        orders = []

        result = await _enrich_orders_with_shipments(orders, mock_delivery_port)

        assert result == []
        mock_delivery_port.get_shipment_by_order.assert_not_called()

    @pytest.mark.asyncio
    async def test_enrich_orders_maintains_order_sequence(
        self, mock_delivery_port, sample_order
    ):
        """Test enrichment maintains order of items."""
        # Create multiple orders with different IDs
        orders = [
            OrderResponse(
                id=uuid4(),
                customer_id=uuid4(),
                seller_id=None,
                route_id=None,
                fecha_pedido=datetime(2025, 1, 1, 10, 0, 0),
                fecha_entrega_estimada=date(2025, 1, 20),
                metodo_creacion="app_cliente",
                direccion_entrega="Calle 123",
                ciudad_entrega="Bogota",
                pais_entrega="Colombia",
                customer_name="Customer 1",
                customer_phone="+1234567890",
                customer_email="c1@test.com",
                seller_name=None,
                seller_email=None,
                monto_total=500.0,
                created_at=datetime(2025, 1, 1, 10, 0, 0),
                updated_at=datetime(2025, 1, 1, 10, 0, 0),
                items=[],
                shipment=None,
            ),
            OrderResponse(
                id=uuid4(),
                customer_id=uuid4(),
                seller_id=None,
                route_id=None,
                fecha_pedido=datetime(2025, 1, 2, 10, 0, 0),
                fecha_entrega_estimada=date(2025, 1, 21),
                metodo_creacion="app_cliente",
                direccion_entrega="Calle 456",
                ciudad_entrega="Medellin",
                pais_entrega="Colombia",
                customer_name="Customer 2",
                customer_phone="+0987654321",
                customer_email="c2@test.com",
                seller_name=None,
                seller_email=None,
                monto_total=750.0,
                created_at=datetime(2025, 1, 2, 10, 0, 0),
                updated_at=datetime(2025, 1, 2, 10, 0, 0),
                items=[],
                shipment=None,
            ),
        ]

        original_ids = [order.id for order in orders]

        mock_delivery_port.get_shipment_by_order = AsyncMock(return_value=None)

        result = await _enrich_orders_with_shipments(orders, mock_delivery_port)

        result_ids = [order.id for order in result]
        assert result_ids == original_ids

    @pytest.mark.asyncio
    async def test_enrich_orders_mixed_success_and_failure(
        self, mock_delivery_port, sample_shipment
    ):
        """Test enrichment when some shipments fetch succeeds and some fail."""
        # Create 3 independent orders
        order_1 = OrderResponse(
            id=uuid4(),
            customer_id=uuid4(),
            seller_id=None,
            route_id=None,
            fecha_pedido=datetime(2025, 1, 1, 10, 0, 0),
            fecha_entrega_estimada=date(2025, 1, 20),
            metodo_creacion="app_cliente",
            direccion_entrega="Calle 123",
            ciudad_entrega="Bogota",
            pais_entrega="Colombia",
            customer_name="Test Customer 1",
            customer_phone="+1234567890",
            customer_email="customer1@test.com",
            seller_name=None,
            seller_email=None,
            monto_total=500.0,
            created_at=datetime(2025, 1, 1, 10, 0, 0),
            updated_at=datetime(2025, 1, 1, 10, 0, 0),
            items=[],
            shipment=None,
        )

        order_2 = OrderResponse(
            id=uuid4(),
            customer_id=uuid4(),
            seller_id=None,
            route_id=None,
            fecha_pedido=datetime(2025, 1, 1, 10, 0, 0),
            fecha_entrega_estimada=date(2025, 1, 20),
            metodo_creacion="app_cliente",
            direccion_entrega="Calle 456",
            ciudad_entrega="Medellin",
            pais_entrega="Colombia",
            customer_name="Test Customer 2",
            customer_phone="+0987654321",
            customer_email="customer2@test.com",
            seller_name=None,
            seller_email=None,
            monto_total=600.0,
            created_at=datetime(2025, 1, 1, 10, 0, 0),
            updated_at=datetime(2025, 1, 1, 10, 0, 0),
            items=[],
            shipment=None,
        )

        order_3 = OrderResponse(
            id=uuid4(),
            customer_id=uuid4(),
            seller_id=None,
            route_id=None,
            fecha_pedido=datetime(2025, 1, 1, 10, 0, 0),
            fecha_entrega_estimada=date(2025, 1, 20),
            metodo_creacion="app_cliente",
            direccion_entrega="Calle 789",
            ciudad_entrega="Cali",
            pais_entrega="Colombia",
            customer_name="Test Customer 3",
            customer_phone="+5555555555",
            customer_email="customer3@test.com",
            seller_name=None,
            seller_email=None,
            monto_total=700.0,
            created_at=datetime(2025, 1, 1, 10, 0, 0),
            updated_at=datetime(2025, 1, 1, 10, 0, 0),
            items=[],
            shipment=None,
        )

        orders = [order_1, order_2, order_3]

        # Mix of success, failure, and success
        mock_delivery_port.get_shipment_by_order = AsyncMock(
            side_effect=[sample_shipment, Exception("Error"), sample_shipment]
        )

        result = await _enrich_orders_with_shipments(orders, mock_delivery_port)

        assert result[0].shipment == sample_shipment
        assert result[1].shipment is None  # Failed gracefully
        assert result[2].shipment == sample_shipment


class TestListMyOrdersWithShipments:
    """Tests for list_my_orders endpoint with shipment integration."""

    @pytest.mark.asyncio
    async def test_list_my_orders_with_shipment_info(
        self, mock_order_port, mock_client_port, mock_delivery_port, mock_user, sample_shipment
    ):
        """Test list_my_orders enriches orders with shipment info."""
        cliente_id = uuid4()
        order_id = uuid4()

        mock_client_port.get_client_by_cognito_user_id = AsyncMock(
            return_value={"cliente_id": cliente_id}
        )

        # Create order response
        order = OrderResponse(
            id=order_id,
            customer_id=cliente_id,
            seller_id=None,
            route_id=None,
            fecha_pedido=datetime(2025, 1, 1, 10, 0, 0),
            fecha_entrega_estimada=date(2025, 1, 20),
            metodo_creacion="app_cliente",
            direccion_entrega="Calle 123",
            ciudad_entrega="Bogota",
            pais_entrega="Colombia",
            customer_name="Test Customer",
            customer_phone="+1234567890",
            customer_email="customer@test.com",
            seller_name=None,
            seller_email=None,
            monto_total=500.0,
            created_at=datetime(2025, 1, 1, 10, 0, 0),
            updated_at=datetime(2025, 1, 1, 10, 0, 0),
            items=[],
            shipment=None,
        )

        paginated_response = PaginatedOrdersResponse(
            items=[order],
            total=1,
            page=1,
            size=10,
            has_next=False,
            has_previous=False,
        )

        mock_order_port.list_customer_orders = AsyncMock(
            return_value=paginated_response
        )

        mock_delivery_port.get_shipment_by_order = AsyncMock(
            return_value=sample_shipment
        )

        result = await list_my_orders(
            limit=10,
            offset=0,
            order_port=mock_order_port,
            client_port=mock_client_port,
            delivery_port=mock_delivery_port,
            user=mock_user,
        )

        assert result.items[0].shipment == sample_shipment
        mock_delivery_port.get_shipment_by_order.assert_called_once_with(order_id)

    @pytest.mark.asyncio
    async def test_list_my_orders_without_shipment(
        self, mock_order_port, mock_client_port, mock_delivery_port, mock_user
    ):
        """Test list_my_orders without shipment info (not found)."""
        cliente_id = uuid4()

        mock_client_port.get_client_by_cognito_user_id = AsyncMock(
            return_value={"cliente_id": cliente_id}
        )

        order = OrderResponse(
            id=uuid4(),
            customer_id=cliente_id,
            seller_id=None,
            route_id=None,
            fecha_pedido=datetime(2025, 1, 1, 10, 0, 0),
            fecha_entrega_estimada=date(2025, 1, 20),
            metodo_creacion="app_cliente",
            direccion_entrega="Calle 123",
            ciudad_entrega="Bogota",
            pais_entrega="Colombia",
            customer_name="Test Customer",
            customer_phone="+1234567890",
            customer_email="customer@test.com",
            seller_name=None,
            seller_email=None,
            monto_total=500.0,
            created_at=datetime(2025, 1, 1, 10, 0, 0),
            updated_at=datetime(2025, 1, 1, 10, 0, 0),
            items=[],
            shipment=None,
        )

        paginated_response = PaginatedOrdersResponse(
            items=[order],
            total=1,
            page=1,
            size=10,
            has_next=False,
            has_previous=False,
        )

        mock_order_port.list_customer_orders = AsyncMock(
            return_value=paginated_response
        )

        mock_delivery_port.get_shipment_by_order = AsyncMock(return_value=None)

        result = await list_my_orders(
            limit=10,
            offset=0,
            order_port=mock_order_port,
            client_port=mock_client_port,
            delivery_port=mock_delivery_port,
            user=mock_user,
        )

        assert result.items[0].shipment is None

    @pytest.mark.asyncio
    async def test_list_my_orders_shipment_fetch_error_graceful(
        self, mock_order_port, mock_client_port, mock_delivery_port, mock_user
    ):
        """Test shipment errors don't break order listing."""
        cliente_id = uuid4()

        mock_client_port.get_client_by_cognito_user_id = AsyncMock(
            return_value={"cliente_id": cliente_id}
        )

        order = OrderResponse(
            id=uuid4(),
            customer_id=cliente_id,
            seller_id=None,
            route_id=None,
            fecha_pedido=datetime(2025, 1, 1, 10, 0, 0),
            fecha_entrega_estimada=date(2025, 1, 20),
            metodo_creacion="app_cliente",
            direccion_entrega="Calle 123",
            ciudad_entrega="Bogota",
            pais_entrega="Colombia",
            customer_name="Test Customer",
            customer_phone="+1234567890",
            customer_email="customer@test.com",
            seller_name=None,
            seller_email=None,
            monto_total=500.0,
            created_at=datetime(2025, 1, 1, 10, 0, 0),
            updated_at=datetime(2025, 1, 1, 10, 0, 0),
            items=[],
            shipment=None,
        )

        paginated_response = PaginatedOrdersResponse(
            items=[order],
            total=1,
            page=1,
            size=10,
            has_next=False,
            has_previous=False,
        )

        mock_order_port.list_customer_orders = AsyncMock(
            return_value=paginated_response
        )

        # Delivery service throws error
        mock_delivery_port.get_shipment_by_order = AsyncMock(
            side_effect=MicroserviceConnectionError(
                service_name="delivery",
                original_error="Connection refused",
            )
        )

        # Should not raise - gracefully handles error
        result = await list_my_orders(
            limit=10,
            offset=0,
            order_port=mock_order_port,
            client_port=mock_client_port,
            delivery_port=mock_delivery_port,
            user=mock_user,
        )

        assert len(result.items) == 1
        assert result.items[0].shipment is None

    @pytest.mark.asyncio
    async def test_list_my_orders_multiple_orders_with_shipments(
        self, mock_order_port, mock_client_port, mock_delivery_port, mock_user, sample_shipment
    ):
        """Test listing multiple orders with shipment info."""
        cliente_id = uuid4()

        mock_client_port.get_client_by_cognito_user_id = AsyncMock(
            return_value={"cliente_id": cliente_id}
        )

        # Create multiple orders
        orders = [
            OrderResponse(
                id=uuid4(),
                customer_id=cliente_id,
                seller_id=None,
                route_id=None,
                fecha_pedido=datetime(2025, 1, 1, 10, 0, 0),
                fecha_entrega_estimada=date(2025, 1, 20),
                metodo_creacion="app_cliente",
                direccion_entrega="Calle 123",
                ciudad_entrega="Bogota",
                pais_entrega="Colombia",
                customer_name="Test Customer",
                customer_phone="+1234567890",
                customer_email="customer@test.com",
                seller_name=None,
                seller_email=None,
                monto_total=500.0,
                created_at=datetime(2025, 1, 1, 10, 0, 0),
                updated_at=datetime(2025, 1, 1, 10, 0, 0),
                items=[],
                shipment=None,
            ),
            OrderResponse(
                id=uuid4(),
                customer_id=cliente_id,
                seller_id=None,
                route_id=None,
                fecha_pedido=datetime(2025, 1, 2, 10, 0, 0),
                fecha_entrega_estimada=date(2025, 1, 21),
                metodo_creacion="app_cliente",
                direccion_entrega="Calle 456",
                ciudad_entrega="Medellin",
                pais_entrega="Colombia",
                customer_name="Test Customer",
                customer_phone="+1234567890",
                customer_email="customer@test.com",
                seller_name=None,
                seller_email=None,
                monto_total=750.0,
                created_at=datetime(2025, 1, 2, 10, 0, 0),
                updated_at=datetime(2025, 1, 2, 10, 0, 0),
                items=[],
                shipment=None,
            ),
        ]

        paginated_response = PaginatedOrdersResponse(
            items=orders,
            total=2,
            page=1,
            size=10,
            has_next=False,
            has_previous=False,
        )

        mock_order_port.list_customer_orders = AsyncMock(
            return_value=paginated_response
        )

        # Both orders have shipments
        mock_delivery_port.get_shipment_by_order = AsyncMock(
            side_effect=[sample_shipment, sample_shipment]
        )

        result = await list_my_orders(
            limit=10,
            offset=0,
            order_port=mock_order_port,
            client_port=mock_client_port,
            delivery_port=mock_delivery_port,
            user=mock_user,
        )

        assert len(result.items) == 2
        assert result.items[0].shipment == sample_shipment
        assert result.items[1].shipment == sample_shipment
        assert mock_delivery_port.get_shipment_by_order.call_count == 2

    @pytest.mark.asyncio
    async def test_list_my_orders_enrichment_preserves_order_data(
        self, mock_order_port, mock_client_port, mock_delivery_port, mock_user, sample_shipment
    ):
        """Test that shipment enrichment doesn't modify order data."""
        cliente_id = uuid4()
        original_order_id = uuid4()

        mock_client_port.get_client_by_cognito_user_id = AsyncMock(
            return_value={"cliente_id": cliente_id}
        )

        order = OrderResponse(
            id=original_order_id,
            customer_id=cliente_id,
            seller_id=None,
            route_id=None,
            fecha_pedido=datetime(2025, 1, 1, 10, 0, 0),
            fecha_entrega_estimada=date(2025, 1, 20),
            metodo_creacion="app_cliente",
            direccion_entrega="Calle 123",
            ciudad_entrega="Bogota",
            pais_entrega="Colombia",
            customer_name="Test Customer",
            customer_phone="+1234567890",
            customer_email="customer@test.com",
            seller_name=None,
            seller_email=None,
            monto_total=500.0,
            created_at=datetime(2025, 1, 1, 10, 0, 0),
            updated_at=datetime(2025, 1, 1, 10, 0, 0),
            items=[],
            shipment=None,
        )

        paginated_response = PaginatedOrdersResponse(
            items=[order],
            total=1,
            page=1,
            size=10,
            has_next=False,
            has_previous=False,
        )

        mock_order_port.list_customer_orders = AsyncMock(
            return_value=paginated_response
        )

        mock_delivery_port.get_shipment_by_order = AsyncMock(
            return_value=sample_shipment
        )

        result = await list_my_orders(
            limit=10,
            offset=0,
            order_port=mock_order_port,
            client_port=mock_client_port,
            delivery_port=mock_delivery_port,
            user=mock_user,
        )

        # Order data should be preserved
        assert result.items[0].id == original_order_id
        assert result.items[0].customer_id == cliente_id
        assert result.items[0].monto_total == 500.0
        assert result.items[0].shipment == sample_shipment
