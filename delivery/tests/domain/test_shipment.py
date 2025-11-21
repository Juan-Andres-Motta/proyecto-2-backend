import pytest
from datetime import datetime, date, timedelta
from decimal import Decimal
from uuid import uuid4

from src.domain.entities import Shipment
from src.domain.value_objects import ShipmentStatus, GeocodingStatus, Coordinates


class TestShipmentCreation:
    def test_create_valid_shipment(self, sample_shipment):
        """Test creating a valid shipment with required fields."""
        assert sample_shipment.id is not None
        assert sample_shipment.order_id is not None
        assert sample_shipment.customer_id is not None
        assert sample_shipment.direccion_entrega == "Calle 123 #45-67"
        assert sample_shipment.ciudad_entrega == "Bogota"
        assert sample_shipment.pais_entrega == "Colombia"
        assert sample_shipment.shipment_status == ShipmentStatus.PENDING
        assert sample_shipment.geocoding_status == GeocodingStatus.PENDING

    def test_create_shipment_with_coordinates(self):
        """Test creating a shipment with initial coordinates."""
        shipment = Shipment(
            id=uuid4(),
            order_id=uuid4(),
            customer_id=uuid4(),
            direccion_entrega="Calle 1 #2-3",
            ciudad_entrega="Medellin",
            pais_entrega="Colombia",
            fecha_pedido=datetime.now(),
            fecha_entrega_estimada=(datetime.now() + timedelta(days=1)).date(),
            latitude=Decimal("6.25"),
            longitude=Decimal("-75.56"),
            geocoding_status=GeocodingStatus.SUCCESS,
        )
        assert shipment.latitude == Decimal("6.25")
        assert shipment.longitude == Decimal("-75.56")
        assert shipment.is_geocoded is True

    def test_create_shipment_with_route_assignment(self):
        """Test creating a shipment with route assignment."""
        route_id = uuid4()
        shipment = Shipment(
            id=uuid4(),
            order_id=uuid4(),
            customer_id=uuid4(),
            direccion_entrega="Calle 1 #2-3",
            ciudad_entrega="Cali",
            pais_entrega="Colombia",
            fecha_pedido=datetime.now(),
            fecha_entrega_estimada=(datetime.now() + timedelta(days=1)).date(),
            route_id=route_id,
            sequence_in_route=1,
            shipment_status=ShipmentStatus.ASSIGNED_TO_ROUTE,
        )
        assert shipment.route_id == route_id
        assert shipment.sequence_in_route == 1

    def test_create_shipment_missing_direccion_fails(self):
        """Test that creating a shipment without delivery address fails."""
        with pytest.raises(ValueError) as exc_info:
            Shipment(
                id=uuid4(),
                order_id=uuid4(),
                customer_id=uuid4(),
                direccion_entrega="",
                ciudad_entrega="Bogota",
                pais_entrega="Colombia",
                fecha_pedido=datetime.now(),
                fecha_entrega_estimada=(datetime.now() + timedelta(days=1)).date(),
            )
        assert "direccion_entrega is required" in str(exc_info.value)

    def test_create_shipment_missing_ciudad_fails(self):
        """Test that creating a shipment without city fails."""
        with pytest.raises(ValueError) as exc_info:
            Shipment(
                id=uuid4(),
                order_id=uuid4(),
                customer_id=uuid4(),
                direccion_entrega="Calle 123",
                ciudad_entrega="",
                pais_entrega="Colombia",
                fecha_pedido=datetime.now(),
                fecha_entrega_estimada=(datetime.now() + timedelta(days=1)).date(),
            )
        assert "ciudad_entrega is required" in str(exc_info.value)

    def test_create_shipment_missing_pais_fails(self):
        """Test that creating a shipment without country fails."""
        with pytest.raises(ValueError) as exc_info:
            Shipment(
                id=uuid4(),
                order_id=uuid4(),
                customer_id=uuid4(),
                direccion_entrega="Calle 123",
                ciudad_entrega="Bogota",
                pais_entrega="",
                fecha_pedido=datetime.now(),
                fecha_entrega_estimada=(datetime.now() + timedelta(days=1)).date(),
            )
        assert "pais_entrega is required" in str(exc_info.value)


class TestShipmentGeocoding:
    def test_set_coordinates_updates_status(self, sample_shipment):
        """Test that setting coordinates updates geocoding status to SUCCESS."""
        assert sample_shipment.geocoding_status == GeocodingStatus.PENDING

        sample_shipment.set_coordinates(Decimal("4.70"), Decimal("-74.15"))

        assert sample_shipment.latitude == Decimal("4.70")
        assert sample_shipment.longitude == Decimal("-74.15")
        assert sample_shipment.geocoding_status == GeocodingStatus.SUCCESS

    def test_mark_geocoding_failed(self, sample_shipment):
        """Test marking geocoding as failed."""
        assert sample_shipment.geocoding_status == GeocodingStatus.PENDING

        sample_shipment.mark_geocoding_failed()

        assert sample_shipment.geocoding_status == GeocodingStatus.FAILED

    def test_coordinates_property_with_values(self, geocoded_shipment):
        """Test coordinates property returns Coordinates object when values exist."""
        coords = geocoded_shipment.coordinates

        assert coords is not None
        assert isinstance(coords, Coordinates)
        assert coords.latitude == Decimal("4.60")
        assert coords.longitude == Decimal("-74.08")

    def test_coordinates_property_without_values(self, sample_shipment):
        """Test coordinates property returns None when no coordinates are set."""
        assert sample_shipment.coordinates is None

    def test_coordinates_property_partial_values(self):
        """Test coordinates property returns None when only one coordinate is set."""
        shipment = Shipment(
            id=uuid4(),
            order_id=uuid4(),
            customer_id=uuid4(),
            direccion_entrega="Calle 1",
            ciudad_entrega="Bogota",
            pais_entrega="Colombia",
            fecha_pedido=datetime.now(),
            fecha_entrega_estimada=(datetime.now() + timedelta(days=1)).date(),
            latitude=Decimal("4.60"),
        )
        assert shipment.coordinates is None

    def test_is_geocoded_true_when_successful(self, geocoded_shipment):
        """Test is_geocoded property returns True when geocoding is successful."""
        assert geocoded_shipment.is_geocoded is True

    def test_is_geocoded_false_when_pending(self, sample_shipment):
        """Test is_geocoded property returns False when geocoding is pending."""
        assert sample_shipment.is_geocoded is False

    def test_is_geocoded_false_when_failed(self, sample_shipment):
        """Test is_geocoded property returns False when geocoding failed."""
        sample_shipment.mark_geocoding_failed()
        assert sample_shipment.is_geocoded is False


class TestShipmentRouteAssignment:
    def test_assign_to_route_success(self, sample_shipment):
        """Test successfully assigning a shipment to a route."""
        route_id = uuid4()
        sequence = 1

        sample_shipment.assign_to_route(route_id, sequence)

        assert sample_shipment.route_id == route_id
        assert sample_shipment.sequence_in_route == sequence
        assert sample_shipment.shipment_status == ShipmentStatus.ASSIGNED_TO_ROUTE

    def test_assign_to_route_only_when_pending(self, sample_shipment):
        """Test that can only assign to route when status is PENDING."""
        route_id = uuid4()

        # First assignment should work
        sample_shipment.assign_to_route(route_id, 1)
        assert sample_shipment.shipment_status == ShipmentStatus.ASSIGNED_TO_ROUTE

        # Second assignment should fail
        with pytest.raises(ValueError) as exc_info:
            sample_shipment.assign_to_route(uuid4(), 2)
        assert "Cannot assign shipment to route" in str(exc_info.value)
        assert "ASSIGNED_TO_ROUTE" in str(exc_info.value)

    def test_assign_to_route_different_statuses_fail(self, sample_shipment):
        """Test that assignment fails for non-PENDING statuses."""
        sample_shipment.shipment_status = ShipmentStatus.IN_TRANSIT

        with pytest.raises(ValueError) as exc_info:
            sample_shipment.assign_to_route(uuid4(), 1)
        assert "Cannot assign shipment to route" in str(exc_info.value)
        assert "IN_TRANSIT" in str(exc_info.value)

    def test_assign_to_route_updates_sequence(self, sample_shipment):
        """Test that sequence is properly updated during assignment."""
        route_id = uuid4()

        sample_shipment.assign_to_route(route_id, 5)
        assert sample_shipment.sequence_in_route == 5


class TestShipmentStatusTransitions:
    def test_mark_in_transit_success(self, sample_shipment):
        """Test successfully marking shipment as in transit."""
        sample_shipment.shipment_status = ShipmentStatus.ASSIGNED_TO_ROUTE

        sample_shipment.mark_in_transit()

        assert sample_shipment.shipment_status == ShipmentStatus.IN_TRANSIT

    def test_mark_in_transit_only_from_assigned_status(self, sample_shipment):
        """Test that can only mark as in transit from ASSIGNED_TO_ROUTE status."""
        with pytest.raises(ValueError) as exc_info:
            sample_shipment.mark_in_transit()
        assert "Cannot mark as in transit" in str(exc_info.value)
        assert "PENDING" in str(exc_info.value)

    def test_mark_in_transit_invalid_from_delivered(self, sample_shipment):
        """Test that cannot mark as in transit from DELIVERED status."""
        sample_shipment.shipment_status = ShipmentStatus.DELIVERED

        with pytest.raises(ValueError) as exc_info:
            sample_shipment.mark_in_transit()
        assert "Cannot mark as in transit" in str(exc_info.value)

    def test_mark_delivered_success(self, sample_shipment):
        """Test successfully marking shipment as delivered."""
        sample_shipment.shipment_status = ShipmentStatus.IN_TRANSIT

        sample_shipment.mark_delivered()

        assert sample_shipment.shipment_status == ShipmentStatus.DELIVERED

    def test_mark_delivered_only_from_in_transit(self, sample_shipment):
        """Test that can only mark as delivered from IN_TRANSIT status."""
        with pytest.raises(ValueError) as exc_info:
            sample_shipment.mark_delivered()
        assert "Cannot mark as delivered" in str(exc_info.value)
        assert "PENDING" in str(exc_info.value)

    def test_mark_delivered_invalid_from_assigned(self, sample_shipment):
        """Test that cannot mark as delivered from ASSIGNED_TO_ROUTE status."""
        sample_shipment.shipment_status = ShipmentStatus.ASSIGNED_TO_ROUTE

        with pytest.raises(ValueError) as exc_info:
            sample_shipment.mark_delivered()
        assert "Cannot mark as delivered" in str(exc_info.value)

    def test_complete_workflow(self, sample_shipment):
        """Test complete shipment workflow from PENDING to DELIVERED."""
        # PENDING -> ASSIGNED_TO_ROUTE
        sample_shipment.assign_to_route(uuid4(), 1)
        assert sample_shipment.shipment_status == ShipmentStatus.ASSIGNED_TO_ROUTE

        # ASSIGNED_TO_ROUTE -> IN_TRANSIT
        sample_shipment.mark_in_transit()
        assert sample_shipment.shipment_status == ShipmentStatus.IN_TRANSIT

        # IN_TRANSIT -> DELIVERED
        sample_shipment.mark_delivered()
        assert sample_shipment.shipment_status == ShipmentStatus.DELIVERED


class TestShipmentClassMethods:
    def test_calculate_estimated_delivery_from_today(self):
        """Test estimating delivery date is 1 day after order."""
        order_time = datetime(2025, 1, 15, 10, 30, 0)
        estimated = Shipment.calculate_estimated_delivery(order_time)

        assert estimated == date(2025, 1, 16)

    def test_calculate_estimated_delivery_from_different_date(self):
        """Test estimated delivery calculation for various dates."""
        order_time = datetime(2025, 12, 31, 23, 59, 59)
        estimated = Shipment.calculate_estimated_delivery(order_time)

        assert estimated == date(2026, 1, 1)

    def test_calculate_estimated_delivery_month_end(self):
        """Test estimated delivery calculation across month boundaries."""
        order_time = datetime(2025, 2, 28, 12, 0, 0)
        estimated = Shipment.calculate_estimated_delivery(order_time)

        assert estimated == date(2025, 3, 1)

    def test_calculate_estimated_delivery_leap_year(self):
        """Test estimated delivery calculation across leap day."""
        order_time = datetime(2024, 2, 28, 15, 0, 0)
        estimated = Shipment.calculate_estimated_delivery(order_time)

        assert estimated == date(2024, 2, 29)


class TestShipmentEdgeCases:
    def test_shipment_with_none_optional_fields(self):
        """Test shipment creation with explicit None values."""
        shipment = Shipment(
            id=uuid4(),
            order_id=uuid4(),
            customer_id=uuid4(),
            direccion_entrega="Calle 1",
            ciudad_entrega="Bogota",
            pais_entrega="Colombia",
            fecha_pedido=datetime.now(),
            fecha_entrega_estimada=(datetime.now() + timedelta(days=1)).date(),
            latitude=None,
            longitude=None,
            route_id=None,
            sequence_in_route=None,
        )

        assert shipment.latitude is None
        assert shipment.longitude is None
        assert shipment.route_id is None
        assert shipment.sequence_in_route is None

    def test_shipment_sequence_zero(self):
        """Test shipment with sequence number 0."""
        shipment = Shipment(
            id=uuid4(),
            order_id=uuid4(),
            customer_id=uuid4(),
            direccion_entrega="Calle 1",
            ciudad_entrega="Bogota",
            pais_entrega="Colombia",
            fecha_pedido=datetime.now(),
            fecha_entrega_estimada=(datetime.now() + timedelta(days=1)).date(),
            sequence_in_route=0,
        )

        assert shipment.sequence_in_route == 0

    def test_coordinates_with_negative_values(self, sample_shipment):
        """Test setting coordinates with negative longitude (Western hemisphere)."""
        sample_shipment.set_coordinates(Decimal("4.60971"), Decimal("-74.08175"))

        assert sample_shipment.latitude == Decimal("4.60971")
        assert sample_shipment.longitude == Decimal("-74.08175")
        assert sample_shipment.coordinates is not None

    def test_multiple_geocoding_attempts(self, sample_shipment):
        """Test updating coordinates multiple times."""
        # First geocoding
        sample_shipment.set_coordinates(Decimal("4.70"), Decimal("-74.15"))
        assert sample_shipment.geocoding_status == GeocodingStatus.SUCCESS
        assert sample_shipment.latitude == Decimal("4.70")

        # Failed then try again
        sample_shipment.mark_geocoding_failed()
        assert sample_shipment.geocoding_status == GeocodingStatus.FAILED

        # Successfully geocode again
        sample_shipment.set_coordinates(Decimal("4.80"), Decimal("-74.20"))
        assert sample_shipment.geocoding_status == GeocodingStatus.SUCCESS
        assert sample_shipment.latitude == Decimal("4.80")
