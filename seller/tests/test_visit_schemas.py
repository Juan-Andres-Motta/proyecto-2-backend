"""Unit tests for visit request schemas."""
import pytest
from datetime import datetime, timezone, timedelta
from uuid import uuid4
from pydantic import ValidationError

from src.adapters.input.schemas import CreateVisitRequest


class TestCreateVisitRequestValidation:
    """Test CreateVisitRequest schema validation."""

    def test_create_visit_request_timezone_aware_valid(self):
        """Test CreateVisitRequest with timezone-aware datetime is valid."""
        future_date = datetime.now(timezone.utc) + timedelta(days=2)
        request = CreateVisitRequest(
            seller_id=uuid4(),
            client_id=uuid4(),
            fecha_visita=future_date,
            notas_visita="Test visit",
            client_nombre_institucion="Hospital",
            client_direccion="Address",
            client_ciudad="City",
            client_pais="Country",
        )

        assert request.fecha_visita == future_date
        assert request.fecha_visita.tzinfo is not None

    def test_create_visit_request_timezone_aware_with_offset(self):
        """Test CreateVisitRequest with explicit timezone offset."""
        from datetime import timezone as tz

        future_date = datetime.now(tz.utc) + timedelta(days=2)
        future_date_offset = future_date.replace(tzinfo=tz(timedelta(hours=-5)))

        request = CreateVisitRequest(
            seller_id=uuid4(),
            client_id=uuid4(),
            fecha_visita=future_date_offset,
            notas_visita="Test visit",
            client_nombre_institucion="Hospital",
            client_direccion="Address",
            client_ciudad="City",
            client_pais="Country",
        )

        assert request.fecha_visita.tzinfo is not None
        assert request.fecha_visita.tzinfo.utcoffset(None) == timedelta(hours=-5)

    def test_create_visit_request_naive_datetime_invalid(self):
        """Test CreateVisitRequest with naive datetime (no timezone) raises ValueError (line 170)."""
        future_date = datetime.now() + timedelta(days=2)  # No timezone info

        with pytest.raises(ValidationError) as exc_info:
            CreateVisitRequest(
                seller_id=uuid4(),
                client_id=uuid4(),
                fecha_visita=future_date,
                notas_visita="Test visit",
                client_nombre_institucion="Hospital",
                client_direccion="Address",
                client_ciudad="City",
                client_pais="Country",
            )

        # Check that the error is about timezone-aware requirement
        errors = exc_info.value.errors()
        assert len(errors) > 0
        assert "timezone" in str(errors[0]).lower()

    def test_create_visit_request_with_none_timezone(self):
        """Test CreateVisitRequest with explicitly None tzinfo raises ValueError."""
        future_date = datetime(2025, 12, 1, 10, 0, 0, tzinfo=None)

        with pytest.raises(ValidationError) as exc_info:
            CreateVisitRequest(
                seller_id=uuid4(),
                client_id=uuid4(),
                fecha_visita=future_date,
                notas_visita="Test visit",
                client_nombre_institucion="Hospital",
                client_direccion="Address",
                client_ciudad="City",
                client_pais="Country",
            )

        errors = exc_info.value.errors()
        assert len(errors) > 0
        assert "timezone" in str(errors[0]).lower()

    def test_create_visit_request_optional_notes(self):
        """Test CreateVisitRequest with optional notes field."""
        future_date = datetime.now(timezone.utc) + timedelta(days=2)
        request = CreateVisitRequest(
            seller_id=uuid4(),
            client_id=uuid4(),
            fecha_visita=future_date,
            notas_visita=None,
            client_nombre_institucion="Hospital",
            client_direccion="Address",
            client_ciudad="City",
            client_pais="Country",
        )

        assert request.notas_visita is None

    def test_create_visit_request_empty_string_notes(self):
        """Test CreateVisitRequest with empty string notes."""
        future_date = datetime.now(timezone.utc) + timedelta(days=2)
        request = CreateVisitRequest(
            seller_id=uuid4(),
            client_id=uuid4(),
            fecha_visita=future_date,
            notas_visita="",
            client_nombre_institucion="Hospital",
            client_direccion="Address",
            client_ciudad="City",
            client_pais="Country",
        )

        assert request.notas_visita == ""

    def test_create_visit_request_max_length_notes(self):
        """Test CreateVisitRequest with maximum length notes."""
        future_date = datetime.now(timezone.utc) + timedelta(days=2)
        long_notes = "x" * 500  # Max length is 500

        request = CreateVisitRequest(
            seller_id=uuid4(),
            client_id=uuid4(),
            fecha_visita=future_date,
            notas_visita=long_notes,
            client_nombre_institucion="Hospital",
            client_direccion="Address",
            client_ciudad="City",
            client_pais="Country",
        )

        assert request.notas_visita == long_notes
        assert len(request.notas_visita) == 500

    def test_create_visit_request_exceeds_max_length_notes(self):
        """Test CreateVisitRequest with notes exceeding max length."""
        future_date = datetime.now(timezone.utc) + timedelta(days=2)
        long_notes = "x" * 501  # Exceeds max length of 500

        with pytest.raises(ValidationError) as exc_info:
            CreateVisitRequest(
                seller_id=uuid4(),
                client_id=uuid4(),
                fecha_visita=future_date,
                notas_visita=long_notes,
                client_nombre_institucion="Hospital",
                client_direccion="Address",
                client_ciudad="City",
                client_pais="Country",
            )

        errors = exc_info.value.errors()
        assert len(errors) > 0
