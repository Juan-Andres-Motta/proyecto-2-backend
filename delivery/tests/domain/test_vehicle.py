import pytest
from uuid import uuid4

from src.domain.entities import Vehicle


class TestVehicle:
    def test_create_valid_vehicle(self):
        vehicle = Vehicle(
            id=uuid4(),
            placa="ABC-123",
            driver_name="Juan Perez",
        )
        assert vehicle.placa == "ABC-123"
        assert vehicle.driver_name == "Juan Perez"
        assert vehicle.is_active is True
        assert vehicle.driver_phone is None

    def test_create_vehicle_with_phone(self):
        vehicle = Vehicle(
            id=uuid4(),
            placa="ABC-123",
            driver_name="Juan Perez",
            driver_phone="+57 300 123 4567",
        )
        assert vehicle.driver_phone == "+57 300 123 4567"

    def test_create_vehicle_empty_placa_fails(self):
        with pytest.raises(ValueError) as exc_info:
            Vehicle(
                id=uuid4(),
                placa="",
                driver_name="Juan Perez",
            )
        assert "placa is required" in str(exc_info.value)

    def test_create_vehicle_empty_driver_name_fails(self):
        with pytest.raises(ValueError) as exc_info:
            Vehicle(
                id=uuid4(),
                placa="ABC-123",
                driver_name="",
            )
        assert "driver_name is required" in str(exc_info.value)

    def test_deactivate_vehicle(self, sample_vehicle):
        assert sample_vehicle.is_active is True
        sample_vehicle.deactivate()
        assert sample_vehicle.is_active is False

    def test_activate_vehicle(self, sample_vehicle):
        sample_vehicle.deactivate()
        sample_vehicle.activate()
        assert sample_vehicle.is_active is True

    def test_update_driver_name(self, sample_vehicle):
        sample_vehicle.update(driver_name="Carlos Garcia")
        assert sample_vehicle.driver_name == "Carlos Garcia"

    def test_update_driver_phone(self, sample_vehicle):
        sample_vehicle.update(driver_phone="+57 300 999 8888")
        assert sample_vehicle.driver_phone == "+57 300 999 8888"

    def test_update_both_fields(self, sample_vehicle):
        sample_vehicle.update(
            driver_name="Carlos Garcia",
            driver_phone="+57 300 999 8888",
        )
        assert sample_vehicle.driver_name == "Carlos Garcia"
        assert sample_vehicle.driver_phone == "+57 300 999 8888"

    def test_update_empty_driver_name_fails(self, sample_vehicle):
        with pytest.raises(ValueError) as exc_info:
            sample_vehicle.update(driver_name="")
        assert "driver_name cannot be empty" in str(exc_info.value)

    def test_update_none_values_ignored(self, sample_vehicle):
        original_name = sample_vehicle.driver_name
        original_phone = sample_vehicle.driver_phone
        sample_vehicle.update(driver_name=None, driver_phone=None)
        assert sample_vehicle.driver_name == original_name
        assert sample_vehicle.driver_phone == original_phone
