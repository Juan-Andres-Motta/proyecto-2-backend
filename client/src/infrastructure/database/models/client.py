import uuid
from datetime import datetime

from sqlalchemy import UUID, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class Client(Base):
    __tablename__ = "clients"

    cliente_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    cognito_user_id: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    telefono: Mapped[str] = mapped_column(String(50), nullable=False)
    nombre_institucion: Mapped[str] = mapped_column(String(255), nullable=False)
    tipo_institucion: Mapped[str] = mapped_column(String(100), nullable=False)
    nit: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    direccion: Mapped[str] = mapped_column(String(255), nullable=False)
    ciudad: Mapped[str] = mapped_column(String(100), nullable=False)
    pais: Mapped[str] = mapped_column(String(100), nullable=False)
    representante: Mapped[str] = mapped_column(String(255), nullable=False)
    vendedor_asignado_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
