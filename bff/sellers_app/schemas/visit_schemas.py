"""Pydantic schemas for visit operations in BFF."""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


# ========== Request Schemas ==========


class CreateVisitRequestBFF(BaseModel):
    """Request schema for creating a visit (BFF)."""

    client_id: UUID = Field(..., description="ID of the client to visit")
    fecha_visita: datetime = Field(..., description="Visit date and time (ISO 8601, timezone-aware)")
    notas_visita: Optional[str] = Field(None, max_length=500, description="Visit notes")


class UpdateVisitStatusRequestBFF(BaseModel):
    """Request schema for updating visit status (BFF)."""

    status: str = Field(..., description="New visit status (programada, completada, cancelada)")
    recomendaciones: Optional[str] = Field(None, max_length=1000, description="Product recommendations")


class GenerateEvidenceUploadURLRequestBFF(BaseModel):
    """Request schema for generating S3 upload URL (BFF)."""

    filename: str = Field(..., max_length=255, description="Original filename")
    content_type: str = Field(..., description="MIME type (image/jpeg, video/mp4, etc.)")


class ConfirmEvidenceUploadRequestBFF(BaseModel):
    """Request schema for confirming evidence upload (BFF)."""

    s3_url: str = Field(..., description="Final S3 URL where file was uploaded")


# ========== Response Schemas ==========


class VisitResponseBFF(BaseModel):
    """Response schema for a single visit (BFF)."""

    id: UUID
    seller_id: UUID
    client_id: UUID
    fecha_visita: datetime
    status: str
    notas_visita: Optional[str]
    recomendaciones: Optional[str]
    archivos_evidencia: Optional[str]

    # Denormalized client data
    client_nombre_institucion: str
    client_direccion: str
    client_ciudad: str
    client_pais: str

    # Timestamps
    created_at: datetime
    updated_at: datetime


class PreSignedUploadURLResponseBFF(BaseModel):
    """Response schema for pre-signed S3 upload URL (BFF)."""

    upload_url: str
    fields: dict[str, str]
    s3_url: str
    expires_at: datetime


class ListVisitsResponseBFF(BaseModel):
    """Response schema for listing visits (BFF)."""

    visits: list[VisitResponseBFF]
    count: int
