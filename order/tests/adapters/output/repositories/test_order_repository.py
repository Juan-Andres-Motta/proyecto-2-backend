"""Tests for OrderRepository."""

import uuid
from datetime import date, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, Mock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.adapters.output.repositories.order_repository import OrderRepository
from src.domain.entities import Order as OrderEntity, OrderItem as OrderItemEntity
from src.domain.value_objects import CreationMethod
from src.infrastructure.database.models.order import Order as OrderModel
from src.infrastructure.database.models.order_item import OrderItem as OrderItemModel


@pytest.fixture
def mock_session():
    """Create a mock database session."""
    session = AsyncMock(spec=AsyncSession)
    return session


@pytest.fixture
def order_repository(mock_session):
    """Create an order repository with mock session."""
    return OrderRepository(mock_session)


@pytest.fixture
def sample_order_entity():
    """Create a sample order entity for testing."""
    order = OrderEntity(
        id=uuid.uuid4(),
        customer_id=uuid.uuid4(),
        fecha_pedido=datetime.now(),
        fecha_entrega_estimada=date.today(),
        metodo_creacion=CreationMethod.APP_CLIENTE,
        direccion_entrega="123 Test St",
        ciudad_entrega="Test City",
        pais_entrega="Test Country",
        customer_name="Test Customer",
        customer_phone="123456789",
        customer_email="test@example.com",
        monto_total=Decimal("100.00"),
    )

    # Add an item
    item = OrderItemEntity(
        id=uuid.uuid4(),
        pedido_id=order.id,
        producto_id=uuid.uuid4(),
        inventario_id=uuid.uuid4(),
        cantidad=5,
        precio_unitario=Decimal("20.00"),
        precio_total=Decimal("100.00"),
        product_name="Test Product",
        product_sku="TEST-SKU",
        warehouse_id=uuid.uuid4(),
        warehouse_name="Test Warehouse",
        warehouse_city="Test City",
        warehouse_country="Test Country",
        batch_number="BATCH-001",
        expiration_date=date.today(),
    )
    order._items.append(item)

    return order


@pytest.fixture
def sample_order_model():
    """Create a sample order model for testing."""
    order_model = OrderModel(
        id=uuid.uuid4(),
        customer_id=uuid.uuid4(),
        fecha_pedido=datetime.now(),
        fecha_entrega_estimada=date.today(),
        metodo_creacion="app_cliente",  # String in DB
        direccion_entrega="123 Test St",
        ciudad_entrega="Test City",
        pais_entrega="Test Country",
        customer_name="Test Customer",
        customer_phone="123456789",
        customer_email="test@example.com",
        monto_total=Decimal("100.00"),
    )

    # Add an item
    item_model = OrderItemModel(
        id=uuid.uuid4(),
        pedido_id=order_model.id,
        producto_id=uuid.uuid4(),
        inventario_id=uuid.uuid4(),
        cantidad=5,
        precio_unitario=Decimal("20.00"),
        precio_total=Decimal("100.00"),
        product_name="Test Product",
        product_sku="TEST-SKU",
        warehouse_id=uuid.uuid4(),
        warehouse_name="Test Warehouse",
        warehouse_city="Test City",
        warehouse_country="Test Country",
        batch_number="BATCH-001",
        expiration_date=date.today(),
    )
    order_model.items = [item_model]

    return order_model


class TestOrderRepositoryToEntity:
    """Test _to_entity conversion from model to entity."""

    def test_converts_app_cliente_metodo_creacion_correctly(
        self, order_repository, sample_order_model
    ):
        """Test that metodo_creacion is converted from string to enum correctly for app_cliente."""
        sample_order_model.metodo_creacion = "app_cliente"

        entity = order_repository._to_entity(sample_order_model)

        assert entity.metodo_creacion == CreationMethod.APP_CLIENTE
        assert isinstance(entity.metodo_creacion, CreationMethod)

    def test_converts_app_vendedor_metodo_creacion_correctly(
        self, order_repository, sample_order_model
    ):
        """Test that metodo_creacion is converted from string to enum correctly for app_vendedor."""
        sample_order_model.metodo_creacion = "app_vendedor"
        sample_order_model.seller_id = uuid.uuid4()
        sample_order_model.seller_name = "Test Seller"
        sample_order_model.seller_email = "seller@example.com"

        entity = order_repository._to_entity(sample_order_model)

        assert entity.metodo_creacion == CreationMethod.APP_VENDEDOR
        assert isinstance(entity.metodo_creacion, CreationMethod)

    def test_converts_visita_vendedor_metodo_creacion_correctly(
        self, order_repository, sample_order_model
    ):
        """Test that metodo_creacion is converted from string to enum correctly for visita_vendedor."""
        sample_order_model.metodo_creacion = "visita_vendedor"
        sample_order_model.seller_id = uuid.uuid4()
        sample_order_model.visit_id = uuid.uuid4()
        sample_order_model.seller_name = "Test Seller"
        sample_order_model.seller_email = "seller@example.com"

        entity = order_repository._to_entity(sample_order_model)

        assert entity.metodo_creacion == CreationMethod.VISITA_VENDEDOR
        assert isinstance(entity.metodo_creacion, CreationMethod)

    def test_converts_all_order_fields_correctly(
        self, order_repository, sample_order_model
    ):
        """Test that all order fields are converted correctly."""
        entity = order_repository._to_entity(sample_order_model)

        assert entity.id == sample_order_model.id
        assert entity.customer_id == sample_order_model.customer_id
        assert entity.fecha_pedido == sample_order_model.fecha_pedido
        assert entity.fecha_entrega_estimada == sample_order_model.fecha_entrega_estimada
        assert entity.direccion_entrega == sample_order_model.direccion_entrega
        assert entity.ciudad_entrega == sample_order_model.ciudad_entrega
        assert entity.pais_entrega == sample_order_model.pais_entrega
        assert entity.customer_name == sample_order_model.customer_name
        assert entity.customer_phone == sample_order_model.customer_phone
        assert entity.customer_email == sample_order_model.customer_email
        assert entity.monto_total == sample_order_model.monto_total

    def test_converts_order_items_correctly(
        self, order_repository, sample_order_model
    ):
        """Test that order items are converted correctly."""
        entity = order_repository._to_entity(sample_order_model)

        assert len(entity.items) == 1
        item = entity.items[0]
        item_model = sample_order_model.items[0]

        assert item.id == item_model.id
        assert item.pedido_id == item_model.pedido_id
        assert item.producto_id == item_model.producto_id
        assert item.inventario_id == item_model.inventario_id
        assert item.cantidad == item_model.cantidad
        assert item.precio_unitario == item_model.precio_unitario
        assert item.precio_total == item_model.precio_total
        assert item.product_name == item_model.product_name
        assert item.product_sku == item_model.product_sku
        assert item.warehouse_id == item_model.warehouse_id
        assert item.warehouse_name == item_model.warehouse_name
        assert item.warehouse_city == item_model.warehouse_city
        assert item.warehouse_country == item_model.warehouse_country
        assert item.batch_number == item_model.batch_number
        assert item.expiration_date == item_model.expiration_date

    def test_handles_optional_seller_fields(
        self, order_repository, sample_order_model
    ):
        """Test that optional seller fields are handled correctly when None."""
        sample_order_model.seller_id = None
        sample_order_model.seller_name = None
        sample_order_model.seller_email = None
        sample_order_model.visit_id = None

        entity = order_repository._to_entity(sample_order_model)

        assert entity.seller_id is None
        assert entity.seller_name is None
        assert entity.seller_email is None
        assert entity.visit_id is None

    def test_handles_optional_route_field(
        self, order_repository, sample_order_model
    ):
        """Test that optional route_id field is handled correctly when None."""
        sample_order_model.route_id = None

        entity = order_repository._to_entity(sample_order_model)

        assert entity.route_id is None

    def test_handles_optional_fecha_entrega_estimada(
        self, order_repository, sample_order_model
    ):
        """Test that optional fecha_entrega_estimada is handled correctly when None."""
        sample_order_model.fecha_entrega_estimada = None

        entity = order_repository._to_entity(sample_order_model)

        assert entity.fecha_entrega_estimada is None


class TestOrderRepositorySave:
    """Test save method."""

    @pytest.mark.asyncio
    async def test_saves_order_entity_successfully(
        self, order_repository, sample_order_entity, sample_order_model, mock_session
    ):
        """Test that save method successfully saves an order entity."""
        # Mock session operations
        mock_session.flush = AsyncMock()
        mock_session.commit = AsyncMock()

        # Mock the query result for reload
        mock_result = AsyncMock()
        mock_result.scalar_one = Mock(return_value=sample_order_model)
        mock_session.execute = AsyncMock(return_value=mock_result)

        # Call save
        result = await order_repository.save(sample_order_entity)

        # Verify session operations were called
        assert mock_session.add.call_count >= 1  # Order + items
        mock_session.flush.assert_called_once()
        mock_session.commit.assert_called_once()
        mock_session.execute.assert_called_once()

        # Verify returned entity is correct type
        assert isinstance(result, OrderEntity)

    @pytest.mark.asyncio
    async def test_saves_order_with_multiple_items(
        self, order_repository, sample_order_entity, sample_order_model, mock_session
    ):
        """Test that save method handles orders with multiple items."""
        # Add another item to the order
        item2 = OrderItemEntity(
            id=uuid.uuid4(),
            pedido_id=sample_order_entity.id,
            producto_id=uuid.uuid4(),
            inventario_id=uuid.uuid4(),
            cantidad=3,
            precio_unitario=Decimal("30.00"),
            precio_total=Decimal("90.00"),
            product_name="Test Product 2",
            product_sku="TEST-SKU-2",
            warehouse_id=uuid.uuid4(),
            warehouse_name="Test Warehouse",
            warehouse_city="Test City",
            warehouse_country="Test Country",
            batch_number="BATCH-002",
            expiration_date=date.today(),
        )
        sample_order_entity._items.append(item2)

        # Mock session operations
        mock_session.flush = AsyncMock()
        mock_session.commit = AsyncMock()

        # Add second item to model
        item_model2 = OrderItemModel(
            id=item2.id,
            pedido_id=sample_order_model.id,
            producto_id=item2.producto_id,
            inventario_id=item2.inventario_id,
            cantidad=item2.cantidad,
            precio_unitario=item2.precio_unitario,
            precio_total=item2.precio_total,
            product_name=item2.product_name,
            product_sku=item2.product_sku,
            warehouse_id=item2.warehouse_id,
            warehouse_name=item2.warehouse_name,
            warehouse_city=item2.warehouse_city,
            warehouse_country=item2.warehouse_country,
            batch_number=item2.batch_number,
            expiration_date=item2.expiration_date,
        )
        sample_order_model.items.append(item_model2)

        mock_result = AsyncMock()
        mock_result.scalar_one = Mock(return_value=sample_order_model)
        mock_session.execute = AsyncMock(return_value=mock_result)

        # Call save
        result = await order_repository.save(sample_order_entity)

        # Verify session.add was called for order + 2 items = 3 times
        assert mock_session.add.call_count == 3
        assert isinstance(result, OrderEntity)
        assert len(result.items) == 2


class TestOrderRepositoryFindById:
    """Test find_by_id method."""

    @pytest.mark.asyncio
    async def test_finds_order_by_id_successfully(
        self, order_repository, sample_order_model, mock_session
    ):
        """Test that find_by_id returns order when found."""
        order_id = sample_order_model.id

        # Mock session execute to return the order
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = Mock(return_value=sample_order_model)
        mock_session.execute = AsyncMock(return_value=mock_result)

        # Call find_by_id
        result = await order_repository.find_by_id(order_id)

        # Verify result
        assert result is not None
        assert isinstance(result, OrderEntity)
        assert result.id == order_id
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_returns_none_when_order_not_found(
        self, order_repository, mock_session
    ):
        """Test that find_by_id returns None when order not found."""
        order_id = uuid.uuid4()

        # Mock session execute to return None
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = Mock(return_value=None)
        mock_session.execute = AsyncMock(return_value=mock_result)

        # Call find_by_id
        result = await order_repository.find_by_id(order_id)

        # Verify result is None
        assert result is None
        mock_session.execute.assert_called_once()


class TestOrderRepositoryFindAll:
    """Test find_all method."""

    @pytest.mark.asyncio
    async def test_finds_all_orders_with_pagination(
        self, order_repository, sample_order_model, mock_session
    ):
        """Test that find_all returns paginated orders."""
        # Mock count query
        mock_count_result = AsyncMock()
        mock_count_result.scalar = Mock(return_value=5)

        # Mock data query
        mock_data_result = AsyncMock()
        mock_scalars = Mock()
        mock_scalars.all = Mock(return_value=[sample_order_model])
        mock_data_result.scalars = Mock(return_value=mock_scalars)

        # Configure session.execute to return different results for count and data queries
        mock_session.execute = AsyncMock(
            side_effect=[mock_count_result, mock_data_result]
        )

        # Call find_all
        orders, total = await order_repository.find_all(limit=10, offset=0)

        # Verify results
        assert len(orders) == 1
        assert isinstance(orders[0], OrderEntity)
        assert total == 5
        assert mock_session.execute.call_count == 2

    @pytest.mark.asyncio
    async def test_handles_empty_result(self, order_repository, mock_session):
        """Test that find_all handles empty result correctly."""
        # Mock count query
        mock_count_result = AsyncMock()
        mock_count_result.scalar = Mock(return_value=0)

        # Mock data query
        mock_data_result = AsyncMock()
        mock_scalars = Mock()
        mock_scalars.all = Mock(return_value=[])
        mock_data_result.scalars = Mock(return_value=mock_scalars)

        mock_session.execute = AsyncMock(
            side_effect=[mock_count_result, mock_data_result]
        )

        # Call find_all
        orders, total = await order_repository.find_all(limit=10, offset=0)

        # Verify results
        assert len(orders) == 0
        assert total == 0
        assert mock_session.execute.call_count == 2

    @pytest.mark.asyncio
    async def test_respects_pagination_parameters(
        self, order_repository, sample_order_model, mock_session
    ):
        """Test that find_all respects limit and offset parameters."""
        # Mock count query
        mock_count_result = AsyncMock()
        mock_count_result.scalar = Mock(return_value=100)

        # Mock data query
        mock_data_result = AsyncMock()
        mock_scalars = Mock()
        mock_scalars.all = Mock(return_value=[sample_order_model])
        mock_data_result.scalars = Mock(return_value=mock_scalars)

        mock_session.execute = AsyncMock(
            side_effect=[mock_count_result, mock_data_result]
        )

        # Call find_all with specific pagination
        orders, total = await order_repository.find_all(limit=5, offset=10)

        # Verify total is correct (should be total count, not page count)
        assert total == 100
        assert len(orders) == 1
        assert mock_session.execute.call_count == 2


class TestOrderRepositoryFindByCustomer:
    """Test find_by_customer method."""

    @pytest.mark.asyncio
    async def test_finds_orders_by_customer_with_pagination(
        self, order_repository, sample_order_model, mock_session
    ):
        """Test that find_by_customer returns paginated orders for a specific customer (covers lines 181-198)."""
        customer_id = uuid.uuid4()

        # Mock count query
        mock_count_result = AsyncMock()
        mock_count_result.scalar = Mock(return_value=3)

        # Mock data query
        mock_data_result = AsyncMock()
        mock_scalars = Mock()
        mock_scalars.all = Mock(return_value=[sample_order_model])
        mock_data_result.scalars = Mock(return_value=mock_scalars)

        # Configure session.execute to return different results for count and data queries
        mock_session.execute = AsyncMock(
            side_effect=[mock_count_result, mock_data_result]
        )

        # Call find_by_customer
        orders, total = await order_repository.find_by_customer(
            customer_id=customer_id, limit=10, offset=0
        )

        # Verify results
        assert len(orders) == 1
        assert isinstance(orders[0], OrderEntity)
        assert total == 3
        assert mock_session.execute.call_count == 2

    @pytest.mark.asyncio
    async def test_find_by_customer_handles_empty_result(
        self, order_repository, mock_session
    ):
        """Test that find_by_customer handles empty result correctly."""
        customer_id = uuid.uuid4()

        # Mock count query
        mock_count_result = AsyncMock()
        mock_count_result.scalar = Mock(return_value=0)

        # Mock data query
        mock_data_result = AsyncMock()
        mock_scalars = Mock()
        mock_scalars.all = Mock(return_value=[])
        mock_data_result.scalars = Mock(return_value=mock_scalars)

        mock_session.execute = AsyncMock(
            side_effect=[mock_count_result, mock_data_result]
        )

        # Call find_by_customer
        orders, total = await order_repository.find_by_customer(
            customer_id=customer_id, limit=10, offset=0
        )

        # Verify results
        assert len(orders) == 0
        assert total == 0
        assert mock_session.execute.call_count == 2
