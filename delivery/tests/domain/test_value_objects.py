import pytest
from decimal import Decimal

from src.domain.value_objects import (
    Coordinates,
    GeocodingStatus,
    RouteStatus,
    ShipmentStatus,
)


class TestShipmentStatus:
    def test_all_status_values(self):
        assert ShipmentStatus.PENDING == "pending"
        assert ShipmentStatus.ASSIGNED_TO_ROUTE == "assigned_to_route"
        assert ShipmentStatus.IN_TRANSIT == "in_transit"
        assert ShipmentStatus.DELIVERED == "delivered"

    def test_status_string_representation(self):
        assert ShipmentStatus.PENDING.value == "pending"
        # str() on a string enum returns "EnumClass.MEMBER"
        assert str(ShipmentStatus.PENDING) == "ShipmentStatus.PENDING"


class TestRouteStatus:
    def test_all_status_values(self):
        assert RouteStatus.PLANEADA == "planeada"
        assert RouteStatus.EN_PROGRESO == "en_progreso"
        assert RouteStatus.COMPLETADA == "completada"
        assert RouteStatus.CANCELADA == "cancelada"


class TestGeocodingStatus:
    def test_all_status_values(self):
        assert GeocodingStatus.PENDING == "pending"
        assert GeocodingStatus.SUCCESS == "success"
        assert GeocodingStatus.FAILED == "failed"


class TestCoordinates:
    def test_create_coordinates(self):
        coords = Coordinates(Decimal("4.60971"), Decimal("-74.08175"))
        assert coords.latitude == Decimal("4.60971")
        assert coords.longitude == Decimal("-74.08175")

    def test_coordinates_immutable(self):
        coords = Coordinates(Decimal("4.60971"), Decimal("-74.08175"))
        with pytest.raises(AttributeError):
            coords.latitude = Decimal("5.0")

    def test_distance_to_same_point(self):
        coords = Coordinates(Decimal("4.60971"), Decimal("-74.08175"))
        distance = coords.distance_to(coords)
        assert distance == 0.0

    def test_distance_to_different_point(self):
        # Bogota to Medellin approximately 250 km
        bogota = Coordinates(Decimal("4.60971"), Decimal("-74.08175"))
        medellin = Coordinates(Decimal("6.25184"), Decimal("-75.56359"))
        distance = bogota.distance_to(medellin)

        # Should be around 250 km
        assert 200 < distance < 300

    def test_distance_calculation_haversine(self):
        # Known distance: approximately 111 km per degree of latitude
        point1 = Coordinates(Decimal("0.0"), Decimal("0.0"))
        point2 = Coordinates(Decimal("1.0"), Decimal("0.0"))
        distance = point1.distance_to(point2)

        # Should be approximately 111 km
        assert 110 < distance < 112

    def test_coordinates_equality(self):
        coords1 = Coordinates(Decimal("4.60971"), Decimal("-74.08175"))
        coords2 = Coordinates(Decimal("4.60971"), Decimal("-74.08175"))
        assert coords1 == coords2

    def test_coordinates_hash(self):
        coords1 = Coordinates(Decimal("4.60971"), Decimal("-74.08175"))
        coords2 = Coordinates(Decimal("4.60971"), Decimal("-74.08175"))
        assert hash(coords1) == hash(coords2)
