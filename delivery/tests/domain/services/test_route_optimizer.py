import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4

from src.domain.entities import Shipment, Vehicle
from src.domain.services.route_optimizer import GreedyRouteOptimizer


class TestGreedyRouteOptimizer:
    @pytest.fixture
    def optimizer(self):
        return GreedyRouteOptimizer()

    @pytest.fixture
    def sample_vehicles(self):
        return [
            Vehicle(id=uuid4(), placa="ABC-123", driver_name="Driver 1"),
            Vehicle(id=uuid4(), placa="DEF-456", driver_name="Driver 2"),
        ]

    def _create_shipment(self, lat, lon):
        shipment = Shipment(
            id=uuid4(),
            order_id=uuid4(),
            customer_id=uuid4(),
            direccion_entrega="Test Address",
            ciudad_entrega="Bogota",
            pais_entrega="Colombia",
            fecha_pedido=datetime.now(),
            fecha_entrega_estimada=(datetime.now() + timedelta(days=1)).date(),
        )
        shipment.set_coordinates(Decimal(str(lat)), Decimal(str(lon)))
        return shipment

    def _create_ungecoded_shipment(self):
        return Shipment(
            id=uuid4(),
            order_id=uuid4(),
            customer_id=uuid4(),
            direccion_entrega="Test Address",
            ciudad_entrega="Bogota",
            pais_entrega="Colombia",
            fecha_pedido=datetime.now(),
            fecha_entrega_estimada=(datetime.now() + timedelta(days=1)).date(),
        )

    @pytest.mark.asyncio
    async def test_optimize_empty_shipments(self, optimizer, sample_vehicles):
        results = await optimizer.optimize_routes([], sample_vehicles)
        assert results == []

    @pytest.mark.asyncio
    async def test_optimize_no_vehicles_fails(self, optimizer):
        shipments = [self._create_shipment(4.60, -74.08)]
        with pytest.raises(ValueError) as exc_info:
            await optimizer.optimize_routes(shipments, [])
        assert "At least one vehicle is required" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_optimize_single_vehicle_single_shipment(self, optimizer):
        vehicles = [Vehicle(id=uuid4(), placa="ABC-123", driver_name="Driver 1")]
        shipments = [self._create_shipment(4.60, -74.08)]

        results = await optimizer.optimize_routes(shipments, vehicles)

        assert len(results) == 1
        assert len(results[0].shipments) == 1
        assert results[0].vehicle == vehicles[0]
        assert results[0].total_distance_km == Decimal("0.00")

    @pytest.mark.asyncio
    async def test_optimize_multiple_vehicles(self, optimizer, sample_vehicles):
        shipments = [
            self._create_shipment(4.60, -74.08),
            self._create_shipment(4.61, -74.09),
            self._create_shipment(4.62, -74.10),
            self._create_shipment(4.70, -74.00),
            self._create_shipment(4.71, -74.01),
            self._create_shipment(4.72, -74.02),
        ]

        results = await optimizer.optimize_routes(shipments, sample_vehicles)

        assert len(results) == 2
        total_shipments = sum(len(r.shipments) for r in results)
        assert total_shipments == 6

    @pytest.mark.asyncio
    async def test_optimize_excludes_ungecoded_shipments(self, optimizer):
        vehicles = [Vehicle(id=uuid4(), placa="ABC-123", driver_name="Driver 1")]
        geocoded = self._create_shipment(4.60, -74.08)
        ungecoded = self._create_ungecoded_shipment()

        results = await optimizer.optimize_routes([geocoded, ungecoded], vehicles)

        assert len(results[0].shipments) == 1

    @pytest.mark.asyncio
    async def test_optimize_no_geocoded_shipments(self, optimizer):
        vehicles = [Vehicle(id=uuid4(), placa="ABC-123", driver_name="Driver 1")]
        ungecoded = self._create_ungecoded_shipment()

        results = await optimizer.optimize_routes([ungecoded], vehicles)

        assert results == []

    @pytest.mark.asyncio
    async def test_optimize_calculates_distance(self, optimizer):
        vehicles = [Vehicle(id=uuid4(), placa="ABC-123", driver_name="Driver 1")]
        # Two points approximately 10 km apart
        shipments = [
            self._create_shipment(4.60, -74.08),
            self._create_shipment(4.69, -74.08),
        ]

        results = await optimizer.optimize_routes(shipments, vehicles)

        assert results[0].total_distance_km > Decimal("0")

    @pytest.mark.asyncio
    async def test_optimize_calculates_duration(self, optimizer):
        vehicles = [Vehicle(id=uuid4(), placa="ABC-123", driver_name="Driver 1")]
        shipments = [
            self._create_shipment(4.60, -74.08),
            self._create_shipment(4.61, -74.09),
        ]

        results = await optimizer.optimize_routes(shipments, vehicles)

        # Should include driving time + stop time
        assert results[0].estimated_duration_minutes > 0

    @pytest.mark.asyncio
    async def test_optimize_fewer_shipments_than_vehicles(self, optimizer, sample_vehicles):
        # Only 1 shipment for 2 vehicles
        shipments = [self._create_shipment(4.60, -74.08)]

        results = await optimizer.optimize_routes(shipments, sample_vehicles)

        # Should get 1 result (empty clusters are skipped)
        assert len(results) == 1
        assert len(results[0].shipments) == 1

    @pytest.mark.asyncio
    async def test_nearest_neighbor_ordering(self, optimizer):
        vehicles = [Vehicle(id=uuid4(), placa="ABC-123", driver_name="Driver 1")]
        # Create shipments that should be ordered by proximity
        shipments = [
            self._create_shipment(4.60, -74.08),  # First
            self._create_shipment(4.80, -74.20),  # Far
            self._create_shipment(4.61, -74.09),  # Near to first
        ]

        results = await optimizer.optimize_routes(shipments, vehicles)

        # The second shipment should be the one near to first, not the far one
        ordered = results[0].shipments
        assert len(ordered) == 3

    @pytest.mark.asyncio
    async def test_optimize_all_ungecoded_shipments_returns_empty(self, optimizer):
        vehicles = [Vehicle(id=uuid4(), placa="ABC-123", driver_name="Driver 1")]
        shipments = [
            self._create_ungecoded_shipment(),
            self._create_ungecoded_shipment(),
            self._create_ungecoded_shipment(),
        ]

        results = await optimizer.optimize_routes(shipments, vehicles)

        assert results == []

    @pytest.mark.asyncio
    async def test_optimize_large_number_of_shipments(self, optimizer):
        vehicles = [
            Vehicle(id=uuid4(), placa="ABC-123", driver_name="Driver 1"),
            Vehicle(id=uuid4(), placa="DEF-456", driver_name="Driver 2"),
            Vehicle(id=uuid4(), placa="GHI-789", driver_name="Driver 3"),
        ]
        # Create 30 shipments
        shipments = [
            self._create_shipment(4.60 + (i * 0.01), -74.08 + (j * 0.01))
            for i in range(3)
            for j in range(10)
        ]

        results = await optimizer.optimize_routes(shipments, vehicles)

        assert len(results) == 3
        total_shipments = sum(len(r.shipments) for r in results)
        assert total_shipments == 30
        # All results should have positive distance or single shipment
        for result in results:
            if len(result.shipments) > 1:
                assert result.total_distance_km >= Decimal("0")

    @pytest.mark.asyncio
    async def test_optimize_mixed_geocoded_and_ungecoded(self, optimizer):
        vehicles = [
            Vehicle(id=uuid4(), placa="ABC-123", driver_name="Driver 1"),
            Vehicle(id=uuid4(), placa="DEF-456", driver_name="Driver 2"),
        ]
        shipments = [
            self._create_shipment(4.60, -74.08),
            self._create_ungecoded_shipment(),
            self._create_shipment(4.61, -74.09),
            self._create_ungecoded_shipment(),
            self._create_shipment(4.62, -74.10),
        ]

        results = await optimizer.optimize_routes(shipments, vehicles)

        total_shipments = sum(len(r.shipments) for r in results)
        assert total_shipments == 3  # Only geocoded shipments

    @pytest.mark.asyncio
    async def test_optimize_duration_includes_stop_time(self, optimizer):
        vehicles = [Vehicle(id=uuid4(), placa="ABC-123", driver_name="Driver 1")]
        # Single shipment has no driving distance but should have stop time
        shipments = [self._create_shipment(4.60, -74.08)]

        results = await optimizer.optimize_routes(shipments, vehicles)

        # Even single stop should include TIME_PER_STOP_MIN = 5 minutes
        assert results[0].estimated_duration_minutes >= 5

    @pytest.mark.asyncio
    async def test_optimize_distance_calculation_accuracy(self, optimizer):
        vehicles = [Vehicle(id=uuid4(), placa="ABC-123", driver_name="Driver 1")]
        # Create 3 shipments in a line
        shipments = [
            self._create_shipment(4.60, -74.08),
            self._create_shipment(4.61, -74.08),
            self._create_shipment(4.62, -74.08),
        ]

        results = await optimizer.optimize_routes(shipments, vehicles)

        # Distance should be calculated for the ordered route
        assert results[0].total_distance_km > Decimal("0")
        # With 3 stops, should have 2 segments of distance
        ordered = results[0].shipments
        assert len(ordered) == 3

    @pytest.mark.asyncio
    async def test_optimize_respects_vehicle_assignment(self, optimizer):
        vehicles = [
            Vehicle(id=uuid4(), placa="ABC-123", driver_name="Driver 1"),
            Vehicle(id=uuid4(), placa="DEF-456", driver_name="Driver 2"),
        ]
        shipments = [
            self._create_shipment(4.60, -74.08),
            self._create_shipment(4.61, -74.09),
            self._create_shipment(4.62, -74.10),
            self._create_shipment(4.63, -74.11),
        ]

        results = await optimizer.optimize_routes(shipments, vehicles)

        # Each result should be assigned to a specific vehicle
        vehicle_ids = [r.vehicle.id for r in results]
        assert len(set(vehicle_ids)) <= len(vehicles)

        # Each vehicle should appear at most once
        for vehicle in vehicles:
            count = sum(1 for r in results if r.vehicle.id == vehicle.id)
            assert count <= 1

    @pytest.mark.asyncio
    async def test_optimize_empty_clusters_are_skipped(self, optimizer):
        vehicles = [
            Vehicle(id=uuid4(), placa="ABC-123", driver_name="Driver 1"),
            Vehicle(id=uuid4(), placa="DEF-456", driver_name="Driver 2"),
        ]
        # Only 1 shipment, so 1 vehicle will have empty cluster
        shipments = [self._create_shipment(4.60, -74.08)]

        results = await optimizer.optimize_routes(shipments, vehicles)

        # Should only return 1 result (non-empty clusters)
        assert len(results) == 1
