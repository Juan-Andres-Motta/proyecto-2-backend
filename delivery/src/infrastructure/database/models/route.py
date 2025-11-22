import uuid

from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .base import Base


class RouteModel(Base):
    __tablename__ = "routes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    vehicle_id = Column(
        UUID(as_uuid=True), ForeignKey("vehicles.id"), nullable=False, index=True
    )
    fecha_ruta = Column(Date, nullable=False, index=True)
    estado_ruta = Column(String(30), nullable=False, default="planeada", index=True)
    duracion_estimada_minutos = Column(Integer, nullable=False, default=0)
    total_distance_km = Column(Numeric(10, 2), nullable=False, default=0)
    total_orders = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    vehicle = relationship("VehicleModel", back_populates="routes")
    shipments = relationship("ShipmentModel", back_populates="route")
