import pytest
from datetime import datetime, date, timedelta
from decimal import Decimal
from uuid import uuid4

from src.domain.entities import Vehicle, Shipment, Route, ProcessedEvent
from src.domain.value_objects import ShipmentStatus, RouteStatus, GeocodingStatus, Coordinates


@pytest.fixture
def sample_vehicle():
    return Vehicle(
        id=uuid4(),
        placa="ABC-123",
        driver_name="Juan Perez",
        driver_phone="+57 300 123 4567",
    )


@pytest.fixture
def sample_shipment():
    return Shipment(
        id=uuid4(),
        order_id=uuid4(),
        customer_id=uuid4(),
        direccion_entrega="Calle 123 #45-67",
        ciudad_entrega="Bogota",
        pais_entrega="Colombia",
        fecha_pedido=datetime.now(),
        fecha_entrega_estimada=(datetime.now() + timedelta(days=1)).date(),
    )


@pytest.fixture
def geocoded_shipment(sample_shipment):
    sample_shipment.set_coordinates(Decimal("4.60"), Decimal("-74.08"))
    return sample_shipment


@pytest.fixture
def sample_route():
    return Route(
        id=uuid4(),
        vehicle_id=uuid4(),
        fecha_ruta=date.today(),
    )


@pytest.fixture
def sample_coordinates():
    return Coordinates(Decimal("4.60971"), Decimal("-74.08175"))
