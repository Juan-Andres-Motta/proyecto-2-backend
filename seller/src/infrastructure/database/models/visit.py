import uuid
from datetime import datetime

from sqlalchemy import UUID, CheckConstraint, DateTime, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class Visit(Base):
    __tablename__ = "visits"

    # Primary Key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # Foreign Keys (reference only, cross-service)
    seller_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    client_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)

    # Visit Details
    fecha_visita: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False)

    # Visit Content Fields
    notas_visita: Mapped[str | None] = mapped_column(Text, nullable=True)
    recomendaciones: Mapped[str | None] = mapped_column(Text, nullable=True)
    archivos_evidencia: Mapped[str | None] = mapped_column(String, nullable=True)

    # Denormalized Client Information (snapshot at time of visit creation)
    client_nombre_institucion: Mapped[str] = mapped_column(String, nullable=False)
    client_direccion: Mapped[str] = mapped_column(String, nullable=False)
    client_ciudad: Mapped[str] = mapped_column(String, nullable=False)
    client_pais: Mapped[str] = mapped_column(String, nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Constraints and Indexes
    __table_args__ = (
        CheckConstraint(
            "status IN ('programada', 'completada', 'cancelada')",
            name="check_visit_status",
        ),
        Index("idx_visits_seller_id", "seller_id"),
        Index("idx_visits_seller_date", "seller_id", "fecha_visita"),
        Index("idx_visits_client_id", "client_id"),
        Index("idx_visits_status", "status"),
        Index("idx_visits_seller_date_status", "seller_id", "fecha_visita", "status"),
    )
