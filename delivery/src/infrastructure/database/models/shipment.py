import uuid

from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .base import Base


class ShipmentModel(Base):
    __tablename__ = "shipments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(UUID(as_uuid=True), unique=True, nullable=False, index=True)
    customer_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    direccion_entrega = Column(String(500), nullable=False)
    ciudad_entrega = Column(String(100), nullable=False)
    pais_entrega = Column(String(100), nullable=False)
    latitude = Column(Numeric(10, 8), nullable=True)
    longitude = Column(Numeric(11, 8), nullable=True)
    geocoding_status = Column(String(20), nullable=False, default="pending", index=True)
    route_id = Column(
        UUID(as_uuid=True), ForeignKey("routes.id"), nullable=True, index=True
    )
    sequence_in_route = Column(Integer, nullable=True)
    fecha_pedido = Column(DateTime(timezone=True), nullable=False)
    fecha_entrega_estimada = Column(Date, nullable=False, index=True)
    shipment_status = Column(String(30), nullable=False, default="pending", index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    route = relationship("RouteModel", back_populates="shipments")
