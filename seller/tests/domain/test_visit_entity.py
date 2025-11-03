"""Unit tests for Visit domain entity."""
import pytest
from datetime import datetime, timezone
from uuid import uuid4

from src.domain.entities.visit import Visit, VisitStatus


class TestVisitStatus:
    """Test VisitStatus enum."""

    def test_visit_status_programada(self):
        """Test PROGRAMADA status value."""
        assert VisitStatus.PROGRAMADA.value == "programada"
        assert VisitStatus.PROGRAMADA == "programada"

    def test_visit_status_completada(self):
        """Test COMPLETADA status value."""
        assert VisitStatus.COMPLETADA.value == "completada"
        assert VisitStatus.COMPLETADA == "completada"

    def test_visit_status_cancelada(self):
        """Test CANCELADA status value."""
        assert VisitStatus.CANCELADA.value == "cancelada"
        assert VisitStatus.CANCELADA == "cancelada"

    def test_visit_status_from_string(self):
        """Test creating VisitStatus from string."""
        status = VisitStatus("programada")
        assert status == VisitStatus.PROGRAMADA

    def test_visit_status_all_values(self):
        """Test all valid status values are enumerated."""
        valid_statuses = {
            VisitStatus.PROGRAMADA.value,
            VisitStatus.COMPLETADA.value,
            VisitStatus.CANCELADA.value,
        }
        assert len(valid_statuses) == 3
        assert "programada" in valid_statuses
        assert "completada" in valid_statuses
        assert "cancelada" in valid_statuses


class TestVisitEntity:
    """Test Visit domain entity."""

    @pytest.fixture
    def base_visit_data(self):
        """Base visit data for creating test visits."""
        return {
            "id": uuid4(),
            "seller_id": uuid4(),
            "client_id": uuid4(),
            "fecha_visita": datetime(2025, 11, 16, 10, 0, tzinfo=timezone.utc),
            "status": VisitStatus.PROGRAMADA,
            "notas_visita": "Test visit notes",
            "recomendaciones": None,
            "archivos_evidencia": "https://s3.amazonaws.com/bucket/visit-evidence/uuid",
            "client_nombre_institucion": "Hospital Central",
            "client_direccion": "Calle 123 #45",
            "client_ciudad": "Bogotá",
            "client_pais": "Colombia",
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }

    def test_visit_instantiation(self, base_visit_data):
        """Test creating a Visit instance with all required fields."""
        visit = Visit(**base_visit_data)

        assert visit.id == base_visit_data["id"]
        assert visit.seller_id == base_visit_data["seller_id"]
        assert visit.client_id == base_visit_data["client_id"]
        assert visit.fecha_visita == base_visit_data["fecha_visita"]
        assert visit.status == VisitStatus.PROGRAMADA
        assert visit.notas_visita == "Test visit notes"
        assert visit.archivos_evidencia == "https://s3.amazonaws.com/bucket/visit-evidence/uuid"

    def test_visit_field_types(self, base_visit_data):
        """Test that Visit fields have correct types."""
        visit = Visit(**base_visit_data)

        # Check UUID fields
        assert isinstance(visit.id, type(uuid4()))
        assert isinstance(visit.seller_id, type(uuid4()))
        assert isinstance(visit.client_id, type(uuid4()))

        # Check datetime fields
        assert isinstance(visit.fecha_visita, datetime)
        assert isinstance(visit.created_at, datetime)
        assert isinstance(visit.updated_at, datetime)

        # Check enum field
        assert isinstance(visit.status, VisitStatus)

        # Check string fields
        assert isinstance(visit.client_nombre_institucion, str)
        assert isinstance(visit.client_direccion, str)
        assert isinstance(visit.client_ciudad, str)
        assert isinstance(visit.client_pais, str)

    def test_visit_optional_fields_accept_none(self, base_visit_data):
        """Test that optional fields accept None values."""
        base_visit_data["notas_visita"] = None
        base_visit_data["recomendaciones"] = None
        base_visit_data["archivos_evidencia"] = None

        visit = Visit(**base_visit_data)

        assert visit.notas_visita is None
        assert visit.recomendaciones is None
        assert visit.archivos_evidencia is None

    def test_visit_optional_fields_with_values(self, base_visit_data):
        """Test that optional fields accept non-None values."""
        base_visit_data["notas_visita"] = "Important notes"
        base_visit_data["recomendaciones"] = "Product recommendations"
        base_visit_data["archivos_evidencia"] = "https://s3.amazonaws.com/bucket/evidence.pdf"

        visit = Visit(**base_visit_data)

        assert visit.notas_visita == "Important notes"
        assert visit.recomendaciones == "Product recommendations"
        assert visit.archivos_evidencia == "https://s3.amazonaws.com/bucket/evidence.pdf"

    def test_visit_status_programada(self, base_visit_data):
        """Test visit with programada status."""
        base_visit_data["status"] = VisitStatus.PROGRAMADA
        visit = Visit(**base_visit_data)

        assert visit.status == VisitStatus.PROGRAMADA
        assert visit.status.value == "programada"

    def test_visit_status_completada(self, base_visit_data):
        """Test visit with completada status."""
        base_visit_data["status"] = VisitStatus.COMPLETADA
        visit = Visit(**base_visit_data)

        assert visit.status == VisitStatus.COMPLETADA
        assert visit.status.value == "completada"

    def test_visit_status_cancelada(self, base_visit_data):
        """Test visit with cancelada status."""
        base_visit_data["status"] = VisitStatus.CANCELADA
        visit = Visit(**base_visit_data)

        assert visit.status == VisitStatus.CANCELADA
        assert visit.status.value == "cancelada"

    def test_visit_denormalized_client_data(self, base_visit_data):
        """Test that denormalized client data is preserved."""
        client_data = {
            "client_nombre_institucion": "Clinica San José",
            "client_direccion": "Carrera 7 #100",
            "client_ciudad": "Medellín",
            "client_pais": "Colombia",
        }
        base_visit_data.update(client_data)

        visit = Visit(**base_visit_data)

        assert visit.client_nombre_institucion == "Clinica San José"
        assert visit.client_direccion == "Carrera 7 #100"
        assert visit.client_ciudad == "Medellín"
        assert visit.client_pais == "Colombia"

    def test_visit_single_evidence_url(self, base_visit_data):
        """Test that archivos_evidencia accepts single S3 URL (not comma-separated)."""
        evidence_url = "https://s3.amazonaws.com/bucket/visit-evidence/123e4567-e89b-12d3-a456-426614174000"
        base_visit_data["archivos_evidencia"] = evidence_url

        visit = Visit(**base_visit_data)

        assert visit.archivos_evidencia == evidence_url
        # Verify it's a single URL string, not comma-separated
        assert "," not in visit.archivos_evidencia

    def test_visit_timestamps(self, base_visit_data):
        """Test that visit preserves timestamp information."""
        now = datetime.now(timezone.utc)
        base_visit_data["created_at"] = now
        base_visit_data["updated_at"] = now

        visit = Visit(**base_visit_data)

        assert visit.created_at == now
        assert visit.updated_at == now

    def test_visit_is_dataclass(self, base_visit_data):
        """Test that Visit is a dataclass with proper behavior."""
        visit1 = Visit(**base_visit_data)
        visit2 = Visit(**base_visit_data)

        # Dataclass equality should work based on field values
        assert visit1.id == visit2.id
        assert visit1.seller_id == visit2.seller_id

    def test_visit_immutability_not_enforced(self, base_visit_data):
        """Test that Visit fields can be modified (dataclass without frozen=True)."""
        visit = Visit(**base_visit_data)
        original_status = visit.status

        # Dataclass is not frozen, so modification should be possible
        visit.status = VisitStatus.CANCELADA

        assert visit.status != original_status
        assert visit.status == VisitStatus.CANCELADA

    def test_visit_repr_contains_key_info(self, base_visit_data):
        """Test that Visit has useful string representation."""
        visit = Visit(**base_visit_data)
        repr_str = repr(visit)

        # Should contain class name
        assert "Visit" in repr_str
        # Should contain key attributes
        assert "id" in repr_str or base_visit_data["id"].hex in repr_str

    def test_visit_with_different_timezones(self):
        """Test visit handles different timezone-aware datetimes."""
        from datetime import timezone as tz, timedelta

        # Create timestamps in different timezones
        utc_time = datetime(2025, 11, 16, 10, 0, tzinfo=timezone.utc)
        cet_tz = timezone(timedelta(hours=1))
        cet_time = datetime(2025, 11, 16, 11, 0, tzinfo=cet_tz)

        visit_utc = Visit(
            id=uuid4(),
            seller_id=uuid4(),
            client_id=uuid4(),
            fecha_visita=utc_time,
            status=VisitStatus.PROGRAMADA,
            notas_visita=None,
            recomendaciones=None,
            archivos_evidencia=None,
            client_nombre_institucion="Hospital",
            client_direccion="Address",
            client_ciudad="City",
            client_pais="Country",
            created_at=utc_time,
            updated_at=utc_time,
        )

        visit_cet = Visit(
            id=uuid4(),
            seller_id=uuid4(),
            client_id=uuid4(),
            fecha_visita=cet_time,
            status=VisitStatus.PROGRAMADA,
            notas_visita=None,
            recomendaciones=None,
            archivos_evidencia=None,
            client_nombre_institucion="Hospital",
            client_direccion="Address",
            client_ciudad="City",
            client_pais="Country",
            created_at=cet_time,
            updated_at=cet_time,
        )

        # Both should store their respective times
        assert visit_utc.fecha_visita.tzinfo == timezone.utc
        assert visit_cet.fecha_visita.tzinfo == cet_tz

    def test_visit_multiple_instances_independent(self, base_visit_data):
        """Test that multiple visit instances are independent."""
        visit1_data = base_visit_data.copy()
        visit2_data = base_visit_data.copy()
        visit2_data["id"] = uuid4()
        visit2_data["status"] = VisitStatus.COMPLETADA

        visit1 = Visit(**visit1_data)
        visit2 = Visit(**visit2_data)

        assert visit1.id != visit2.id
        assert visit1.status == VisitStatus.PROGRAMADA
        assert visit2.status == VisitStatus.COMPLETADA
        # Changing one should not affect the other
        visit1.status = VisitStatus.CANCELADA
        assert visit2.status == VisitStatus.COMPLETADA
