import uuid

from sqlalchemy import Boolean, Column, DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .base import Base


class VehicleModel(Base):
    __tablename__ = "vehicles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    placa = Column(String(20), unique=True, nullable=False, index=True)
    driver_name = Column(String(100), nullable=False)
    driver_phone = Column(String(30), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    routes = relationship("RouteModel", back_populates="vehicle")
