import pytest
from datetime import datetime, date, timedelta
from decimal import Decimal
from uuid import uuid4

from src.domain.entities import Route, Shipment
from src.domain.value_objects import RouteStatus, ShipmentStatus, GeocodingStatus


class TestRouteCreation:
    def test_create_valid_route(self, sample_route):
        """Test creating a valid route with required fields."""
        assert sample_route.id is not None
        assert sample_route.vehicle_id is not None
        assert sample_route.fecha_ruta == date.today()
        assert sample_route.estado_ruta == RouteStatus.PLANEADA
        assert sample_route.duracion_estimada_minutos == 0
        assert sample_route.total_distance_km == Decimal("0.00")
        assert sample_route.total_orders == 0

    def test_create_route_with_specific_date(self):
        """Test creating a route with a specific date."""
        route_date = date(2025, 1, 20)
        route = Route(
            id=uuid4(),
            vehicle_id=uuid4(),
            fecha_ruta=route_date,
        )

        assert route.fecha_ruta == route_date

    def test_create_route_with_metrics(self):
        """Test creating a route with initial metrics."""
        route = Route(
            id=uuid4(),
            vehicle_id=uuid4(),
            fecha_ruta=date.today(),
            duracion_estimada_minutos=120,
            total_distance_km=Decimal("50.50"),
            total_orders=5,
        )

        assert route.duracion_estimada_minutos == 120
        assert route.total_distance_km == Decimal("50.50")
        assert route.total_orders == 5

    def test_create_route_with_initial_status(self):
        """Test creating a route with non-default status."""
        route = Route(
            id=uuid4(),
            vehicle_id=uuid4(),
            fecha_ruta=date.today(),
            estado_ruta=RouteStatus.EN_PROGRESO,
        )

        assert route.estado_ruta == RouteStatus.EN_PROGRESO


class TestRouteShipmentManagement:
    def test_add_single_shipment(self, sample_route, sample_shipment):
        """Test adding a shipment to a route."""
        sample_route.add_shipment(sample_shipment, 1)

        assert sample_shipment.route_id == sample_route.id
        assert sample_shipment.sequence_in_route == 1
        assert sample_shipment.shipment_status == ShipmentStatus.ASSIGNED_TO_ROUTE
        assert sample_route.total_orders == 1

    def test_add_multiple_shipments(self, sample_route):
        """Test adding multiple shipments to a route."""
        shipment1 = Shipment(
            id=uuid4(),
            order_id=uuid4(),
            customer_id=uuid4(),
            direccion_entrega="Calle 1 #2-3",
            ciudad_entrega="Bogota",
            pais_entrega="Colombia",
            fecha_pedido=datetime.now(),
            fecha_entrega_estimada=(datetime.now() + timedelta(days=1)).date(),
        )

        shipment2 = Shipment(
            id=uuid4(),
            order_id=uuid4(),
            customer_id=uuid4(),
            direccion_entrega="Calle 2 #3-4",
            ciudad_entrega="Bogota",
            pais_entrega="Colombia",
            fecha_pedido=datetime.now(),
            fecha_entrega_estimada=(datetime.now() + timedelta(days=1)).date(),
        )

        sample_route.add_shipment(shipment1, 1)
        sample_route.add_shipment(shipment2, 2)

        assert sample_route.total_orders == 2
        assert shipment1.shipment_status == ShipmentStatus.ASSIGNED_TO_ROUTE
        assert shipment2.shipment_status == ShipmentStatus.ASSIGNED_TO_ROUTE

    def test_shipments_property_returns_ordered_list(self, sample_route):
        """Test that shipments property returns shipments in sequence order."""
        shipment1 = Shipment(
            id=uuid4(),
            order_id=uuid4(),
            customer_id=uuid4(),
            direccion_entrega="Calle 1",
            ciudad_entrega="Bogota",
            pais_entrega="Colombia",
            fecha_pedido=datetime.now(),
            fecha_entrega_estimada=(datetime.now() + timedelta(days=1)).date(),
        )

        shipment2 = Shipment(
            id=uuid4(),
            order_id=uuid4(),
            customer_id=uuid4(),
            direccion_entrega="Calle 2",
            ciudad_entrega="Bogota",
            pais_entrega="Colombia",
            fecha_pedido=datetime.now(),
            fecha_entrega_estimada=(datetime.now() + timedelta(days=1)).date(),
        )

        shipment3 = Shipment(
            id=uuid4(),
            order_id=uuid4(),
            customer_id=uuid4(),
            direccion_entrega="Calle 3",
            ciudad_entrega="Bogota",
            pais_entrega="Colombia",
            fecha_pedido=datetime.now(),
            fecha_entrega_estimada=(datetime.now() + timedelta(days=1)).date(),
        )

        # Add in non-sequential order
        sample_route.add_shipment(shipment3, 3)
        sample_route.add_shipment(shipment1, 1)
        sample_route.add_shipment(shipment2, 2)

        # Should be returned in sequence order
        ordered_shipments = sample_route.shipments
        assert len(ordered_shipments) == 3
        assert ordered_shipments[0].sequence_in_route == 1
        assert ordered_shipments[1].sequence_in_route == 2
        assert ordered_shipments[2].sequence_in_route == 3

    def test_set_shipments_directly(self, sample_route):
        """Test setting shipments directly (as when loading from database)."""
        shipment1 = Shipment(
            id=uuid4(),
            order_id=uuid4(),
            customer_id=uuid4(),
            direccion_entrega="Calle 1",
            ciudad_entrega="Bogota",
            pais_entrega="Colombia",
            fecha_pedido=datetime.now(),
            fecha_entrega_estimada=(datetime.now() + timedelta(days=1)).date(),
            route_id=sample_route.id,
            sequence_in_route=1,
            shipment_status=ShipmentStatus.ASSIGNED_TO_ROUTE,
        )

        shipment2 = Shipment(
            id=uuid4(),
            order_id=uuid4(),
            customer_id=uuid4(),
            direccion_entrega="Calle 2",
            ciudad_entrega="Bogota",
            pais_entrega="Colombia",
            fecha_pedido=datetime.now(),
            fecha_entrega_estimada=(datetime.now() + timedelta(days=1)).date(),
            route_id=sample_route.id,
            sequence_in_route=2,
            shipment_status=ShipmentStatus.ASSIGNED_TO_ROUTE,
        )

        sample_route.set_shipments([shipment1, shipment2])

        assert sample_route.total_orders == 2
        assert len(sample_route.shipments) == 2

    def test_set_shipments_updates_total_orders(self, sample_route):
        """Test that set_shipments properly updates total_orders count."""
        shipments = [
            Shipment(
                id=uuid4(),
                order_id=uuid4(),
                customer_id=uuid4(),
                direccion_entrega=f"Calle {i}",
                ciudad_entrega="Bogota",
                pais_entrega="Colombia",
                fecha_pedido=datetime.now(),
                fecha_entrega_estimada=(datetime.now() + timedelta(days=1)).date(),
            )
            for i in range(5)
        ]

        sample_route.set_shipments(shipments)

        assert sample_route.total_orders == 5

    def test_set_empty_shipments_list(self, sample_route):
        """Test setting an empty shipments list."""
        sample_route.set_shipments([])

        assert sample_route.total_orders == 0
        assert len(sample_route.shipments) == 0


class TestRouteStatusTransitions:
    def test_start_route_success(self, sample_route):
        """Test successfully starting a route."""
        assert sample_route.estado_ruta == RouteStatus.PLANEADA

        sample_route.start()

        assert sample_route.estado_ruta == RouteStatus.EN_PROGRESO

    def test_start_route_only_from_planeada(self, sample_route):
        """Test that can only start a route from PLANEADA status."""
        sample_route.estado_ruta = RouteStatus.COMPLETADA

        with pytest.raises(ValueError) as exc_info:
            sample_route.start()
        assert "Cannot start route" in str(exc_info.value)
        assert "COMPLETADA" in str(exc_info.value)

    def test_start_route_marks_shipments_in_transit(self, sample_route):
        """Test that starting a route marks shipments as in transit."""
        shipment1 = Shipment(
            id=uuid4(),
            order_id=uuid4(),
            customer_id=uuid4(),
            direccion_entrega="Calle 1",
            ciudad_entrega="Bogota",
            pais_entrega="Colombia",
            fecha_pedido=datetime.now(),
            fecha_entrega_estimada=(datetime.now() + timedelta(days=1)).date(),
        )

        shipment2 = Shipment(
            id=uuid4(),
            order_id=uuid4(),
            customer_id=uuid4(),
            direccion_entrega="Calle 2",
            ciudad_entrega="Bogota",
            pais_entrega="Colombia",
            fecha_pedido=datetime.now(),
            fecha_entrega_estimada=(datetime.now() + timedelta(days=1)).date(),
        )

        sample_route.add_shipment(shipment1, 1)
        sample_route.add_shipment(shipment2, 2)

        sample_route.start()

        assert sample_route.estado_ruta == RouteStatus.EN_PROGRESO
        assert shipment1.shipment_status == ShipmentStatus.IN_TRANSIT
        assert shipment2.shipment_status == ShipmentStatus.IN_TRANSIT

    def test_start_route_skips_non_assigned_shipments(self, sample_route):
        """Test that start() only marks ASSIGNED_TO_ROUTE shipments as in transit."""
        # Add a shipment that's already been assigned to route
        shipment1 = Shipment(
            id=uuid4(),
            order_id=uuid4(),
            customer_id=uuid4(),
            direccion_entrega="Calle 1",
            ciudad_entrega="Bogota",
            pais_entrega="Colombia",
            fecha_pedido=datetime.now(),
            fecha_entrega_estimada=(datetime.now() + timedelta(days=1)).date(),
        )
        sample_route.add_shipment(shipment1, 1)

        # Manually add a shipment with PENDING status (bypassing add_shipment to test edge case)
        shipment2 = Shipment(
            id=uuid4(),
            order_id=uuid4(),
            customer_id=uuid4(),
            direccion_entrega="Calle 2",
            ciudad_entrega="Bogota",
            pais_entrega="Colombia",
            fecha_pedido=datetime.now(),
            fecha_entrega_estimada=(datetime.now() + timedelta(days=1)).date(),
            shipment_status=ShipmentStatus.PENDING,  # Not ASSIGNED_TO_ROUTE
        )
        sample_route._shipments.append(shipment2)

        sample_route.start()

        assert sample_route.estado_ruta == RouteStatus.EN_PROGRESO
        # shipment1 was ASSIGNED_TO_ROUTE, so it should be IN_TRANSIT
        assert shipment1.shipment_status == ShipmentStatus.IN_TRANSIT
        # shipment2 was PENDING, so it should remain PENDING (not updated)
        assert shipment2.shipment_status == ShipmentStatus.PENDING

    def test_complete_route_success(self, sample_route):
        """Test successfully completing a route."""
        sample_route.estado_ruta = RouteStatus.EN_PROGRESO

        sample_route.complete()

        assert sample_route.estado_ruta == RouteStatus.COMPLETADA

    def test_complete_route_only_from_en_progreso(self, sample_route):
        """Test that can only complete a route from EN_PROGRESO status."""
        assert sample_route.estado_ruta == RouteStatus.PLANEADA

        with pytest.raises(ValueError) as exc_info:
            sample_route.complete()
        assert "Cannot complete route" in str(exc_info.value)
        assert "PLANEADA" in str(exc_info.value)

    def test_cancel_route_success_from_planeada(self, sample_route):
        """Test successfully canceling a route from PLANEADA status."""
        assert sample_route.estado_ruta == RouteStatus.PLANEADA

        sample_route.cancel()

        assert sample_route.estado_ruta == RouteStatus.CANCELADA

    def test_cancel_route_success_from_en_progreso(self, sample_route):
        """Test successfully canceling a route from EN_PROGRESO status."""
        sample_route.estado_ruta = RouteStatus.EN_PROGRESO

        sample_route.cancel()

        assert sample_route.estado_ruta == RouteStatus.CANCELADA

    def test_cancel_route_fails_from_completada(self, sample_route):
        """Test that cannot cancel a completed route."""
        sample_route.estado_ruta = RouteStatus.COMPLETADA

        with pytest.raises(ValueError) as exc_info:
            sample_route.cancel()
        assert "Cannot cancel route" in str(exc_info.value)

    def test_cancel_route_fails_from_cancelada(self, sample_route):
        """Test that cannot cancel an already canceled route."""
        sample_route.estado_ruta = RouteStatus.CANCELADA

        with pytest.raises(ValueError) as exc_info:
            sample_route.cancel()
        assert "Cannot cancel route" in str(exc_info.value)


class TestRouteWorkflows:
    def test_complete_route_workflow(self, sample_route):
        """Test complete route workflow from PLANEADA to COMPLETADA."""
        shipment = Shipment(
            id=uuid4(),
            order_id=uuid4(),
            customer_id=uuid4(),
            direccion_entrega="Calle 1",
            ciudad_entrega="Bogota",
            pais_entrega="Colombia",
            fecha_pedido=datetime.now(),
            fecha_entrega_estimada=(datetime.now() + timedelta(days=1)).date(),
        )

        # PLANEADA - add shipment
        sample_route.add_shipment(shipment, 1)
        assert sample_route.total_orders == 1
        assert shipment.shipment_status == ShipmentStatus.ASSIGNED_TO_ROUTE

        # PLANEADA -> EN_PROGRESO
        sample_route.start()
        assert sample_route.estado_ruta == RouteStatus.EN_PROGRESO
        assert shipment.shipment_status == ShipmentStatus.IN_TRANSIT

        # Mark shipment as delivered
        shipment.mark_delivered()
        assert shipment.shipment_status == ShipmentStatus.DELIVERED

        # EN_PROGRESO -> COMPLETADA
        sample_route.complete()
        assert sample_route.estado_ruta == RouteStatus.COMPLETADA

    def test_cancel_route_workflow(self, sample_route):
        """Test canceling a route with shipments."""
        shipment = Shipment(
            id=uuid4(),
            order_id=uuid4(),
            customer_id=uuid4(),
            direccion_entrega="Calle 1",
            ciudad_entrega="Bogota",
            pais_entrega="Colombia",
            fecha_pedido=datetime.now(),
            fecha_entrega_estimada=(datetime.now() + timedelta(days=1)).date(),
        )

        sample_route.add_shipment(shipment, 1)
        assert sample_route.estado_ruta == RouteStatus.PLANEADA

        sample_route.cancel()
        assert sample_route.estado_ruta == RouteStatus.CANCELADA


class TestRouteEdgeCases:
    def test_route_with_zero_metrics(self):
        """Test route creation with explicit zero values."""
        route = Route(
            id=uuid4(),
            vehicle_id=uuid4(),
            fecha_ruta=date.today(),
            duracion_estimada_minutos=0,
            total_distance_km=Decimal("0.00"),
            total_orders=0,
        )

        assert route.duracion_estimada_minutos == 0
        assert route.total_distance_km == Decimal("0.00")
        assert route.total_orders == 0

    def test_route_large_distance_value(self):
        """Test route with very large distance value."""
        route = Route(
            id=uuid4(),
            vehicle_id=uuid4(),
            fecha_ruta=date.today(),
            total_distance_km=Decimal("9999.99"),
        )

        assert route.total_distance_km == Decimal("9999.99")

    def test_route_with_large_duration(self):
        """Test route with large estimated duration."""
        route = Route(
            id=uuid4(),
            vehicle_id=uuid4(),
            fecha_ruta=date.today(),
            duracion_estimada_minutos=1440,  # 24 hours
        )

        assert route.duracion_estimada_minutos == 1440

    def test_shipments_ordering_with_gaps_in_sequence(self, sample_route):
        """Test shipments ordering when sequences have gaps."""
        shipments_data = [
            (Shipment(
                id=uuid4(),
                order_id=uuid4(),
                customer_id=uuid4(),
                direccion_entrega=f"Calle {i}",
                ciudad_entrega="Bogota",
                pais_entrega="Colombia",
                fecha_pedido=datetime.now(),
                fecha_entrega_estimada=(datetime.now() + timedelta(days=1)).date(),
            ), seq) for i, seq in enumerate([1, 5, 3, 10])
        ]

        for shipment, seq in shipments_data:
            sample_route.add_shipment(shipment, seq)

        ordered = sample_route.shipments
        sequences = [s.sequence_in_route for s in ordered]
        assert sequences == [1, 3, 5, 10]

    def test_shipments_with_none_sequence(self, sample_route):
        """Test shipments ordering when sequence is None."""
        shipment1 = Shipment(
            id=uuid4(),
            order_id=uuid4(),
            customer_id=uuid4(),
            direccion_entrega="Calle 1",
            ciudad_entrega="Bogota",
            pais_entrega="Colombia",
            fecha_pedido=datetime.now(),
            fecha_entrega_estimada=(datetime.now() + timedelta(days=1)).date(),
            sequence_in_route=None,  # None sequence
        )

        sample_route._shipments.append(shipment1)  # Direct append to bypass validation

        # Should still work without throwing
        ordered = sample_route.shipments
        assert shipment1 in ordered
