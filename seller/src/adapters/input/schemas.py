from datetime import datetime
from typing import Annotated, List
from uuid import UUID

import pycountry
from pydantic import BaseModel, EmailStr, Field, field_serializer, field_validator

from .examples import sales_plan_create_example, seller_create_example


class SellerCreate(BaseModel):
    cognito_user_id: str
    name: str
    email: EmailStr
    phone: str
    city: str
    country: str

    model_config = {"json_schema_extra": {"examples": [seller_create_example]}}

    @field_validator("name", "city")
    @classmethod
    def trim_and_title(cls, v: str) -> str:
        """Trim whitespace and capitalize each word."""
        return v.strip().title()

    @field_validator("phone")
    @classmethod
    def trim_only(cls, v: str) -> str:
        """Trim whitespace only."""
        return v.strip()

    @field_validator("country")
    @classmethod
    def normalize_country(cls, v: str) -> str:
        v = v.strip().upper()
        country = (
            pycountry.countries.get(name=v)
            or pycountry.countries.get(alpha_2=v)
            or pycountry.countries.get(alpha_3=v)
        )
        if country:
            return country.alpha_2
        else:
            raise ValueError(f"Invalid country: {v}")


class SellerResponse(BaseModel):
    id: UUID
    cognito_user_id: str
    name: str
    email: str
    phone: str
    city: str
    country: str
    created_at: datetime
    updated_at: datetime

    @field_serializer('country')
    def serialize_country(self, country_code: str) -> str:
        """Convert country code to full country name."""
        try:
            country = pycountry.countries.get(alpha_2=country_code.upper())
            return country.name if country else country_code
        except (LookupError, AttributeError):
            return country_code


class PaginatedSellersResponse(BaseModel):
    items: List[SellerResponse]
    total: int
    page: int
    size: int
    has_next: bool
    has_previous: bool


class SalesPlanCreate(BaseModel):
    """Thin DTO for creating sales plan - NO validation decorators."""
    seller_id: UUID
    sales_period: str
    goal: Annotated[float, Field(gt=0, description="Sales goal amount")]
    # Note: accumulate is NOT in input - always starts at 0
    # Note: status is NOT in input - calculated dynamically
    # Note: goal_type removed

    model_config = {"json_schema_extra": {"examples": [sales_plan_create_example]}}


class SalesPlanResponse(BaseModel):
    """Response DTO with nested seller and calculated status."""
    id: UUID
    seller: SellerResponse  # Nested seller object
    sales_period: str
    goal: float
    accumulate: float
    status: str  # Calculated by domain entity
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_domain(cls, domain_plan) -> "SalesPlanResponse":
        """Map domain entity to DTO.

        Args:
            domain_plan: SalesPlan domain entity

        Returns:
            SalesPlanResponse DTO
        """
        from src.domain.entities.sales_plan import SalesPlan

        return cls(
            id=domain_plan.id,
            seller=SellerResponse(
                id=domain_plan.seller.id,
                cognito_user_id=domain_plan.seller.cognito_user_id,
                name=domain_plan.seller.name,
                email=domain_plan.seller.email,
                phone=domain_plan.seller.phone,
                city=domain_plan.seller.city,
                country=domain_plan.seller.country,
                created_at=domain_plan.seller.created_at,
                updated_at=domain_plan.seller.updated_at
            ),
            sales_period=domain_plan.sales_period,
            goal=domain_plan.goal,
            accumulate=domain_plan.accumulate,
            status=domain_plan.status,  # Uses @property from domain
            created_at=domain_plan.created_at,
            updated_at=domain_plan.updated_at
        )


class PaginatedSalesPlansResponse(BaseModel):
    items: List[SalesPlanResponse]
    total: int
    page: int
    size: int
    has_next: bool
    has_previous: bool


# ========== Visit Schemas ==========

from typing import Optional
from src.domain.entities.visit import VisitStatus


class CreateVisitRequest(BaseModel):
    """Request schema for creating a new visit."""

    seller_id: UUID = Field(
        ..., description="ID of the seller (provided by BFF after JWT authentication)", example="550e8400-e29b-41d4-a716-446655440000"
    )
    client_id: UUID = Field(
        ..., description="ID of the client to visit", example="550e8400-e29b-41d4-a716-446655440000"
    )
    fecha_visita: datetime = Field(
        ...,
        description="Visit date and time (ISO 8601, timezone-aware)",
        example="2025-11-16T10:00:00-05:00",
    )
    notas_visita: Optional[str] = Field(
        None, max_length=500, description="Visit notes", example="Follow-up on product demo"
    )
    # Denormalized client data (passed by BFF after client fetch)
    client_nombre_institucion: str = Field(
        ..., description="Client institution name", example="Hospital Central"
    )
    client_direccion: str = Field(
        ..., description="Client address", example="Av. Principal 123"
    )
    client_ciudad: str = Field(
        ..., description="Client city", example="Bogotá"
    )
    client_pais: str = Field(
        ..., description="Client country", example="Colombia"
    )

    @field_validator("fecha_visita")
    @classmethod
    def validate_timezone_aware(cls, v: datetime) -> datetime:
        """Ensure fecha_visita is timezone-aware."""
        if v.tzinfo is None:
            raise ValueError("fecha_visita must be timezone-aware (include timezone offset)")
        return v


class UpdateVisitStatusRequest(BaseModel):
    """Request schema for updating visit status."""

    status: VisitStatus = Field(
        ..., description="New visit status", example="completada"
    )
    recomendaciones: Optional[str] = Field(
        None, max_length=1000, description="Product recommendations", example="Recommend ordering 50 units of Product X"
    )


class GenerateEvidenceUploadURLRequest(BaseModel):
    """Request schema for generating S3 pre-signed upload URL."""

    filename: str = Field(
        ..., max_length=255, description="Original filename", example="visit-photo-001.jpg"
    )
    content_type: str = Field(
        ..., description="MIME type of the file", example="image/jpeg"
    )


class ConfirmEvidenceUploadRequest(BaseModel):
    """Request schema for confirming evidence upload."""

    s3_url: str = Field(
        ..., description="Final S3 URL where file was uploaded", example="https://medisupply-evidence.s3.us-east-1.amazonaws.com/visits/123/abc-photo.jpg"
    )


class VisitResponse(BaseModel):
    """Response schema for a single visit."""

    id: UUID = Field(..., description="Visit ID")
    seller_id: UUID = Field(..., description="Seller ID")
    client_id: UUID = Field(..., description="Client ID")
    fecha_visita: datetime = Field(..., description="Visit date and time")
    status: VisitStatus = Field(..., description="Visit status")
    notas_visita: Optional[str] = Field(None, description="Visit notes")
    recomendaciones: Optional[str] = Field(None, description="Product recommendations")
    archivos_evidencia: Optional[str] = Field(None, description="S3 URL of evidence file")

    # Denormalized client data
    client_nombre_institucion: str = Field(..., description="Client institution name")
    client_direccion: str = Field(..., description="Client address")
    client_ciudad: str = Field(..., description="Client city")
    client_pais: str = Field(..., description="Client country")

    # Timestamps
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        """Pydantic config."""
        from_attributes = True  # Allows creating from ORM models


class PreSignedUploadURLResponse(BaseModel):
    """Response schema for pre-signed S3 upload URL."""

    upload_url: str = Field(..., description="S3 bucket URL for POST request")
    fields: dict[str, str] = Field(..., description="Form fields to include in multipart upload")
    s3_url: str = Field(..., description="Final URL where file will be accessible after upload")
    expires_at: datetime = Field(..., description="URL expiration timestamp")


class ListVisitsResponse(BaseModel):
    """Response schema for listing visits."""

    visits: list[VisitResponse] = Field(..., description="List of visits")
    count: int = Field(..., description="Total number of visits")


class ErrorDetail(BaseModel):
    """Generic error detail schema."""

    field: Optional[str] = Field(None, description="Field that caused the error")
    message: str = Field(..., description="Error message")


class ErrorResponse(BaseModel):
    """Generic error response schema."""

    error: str = Field(..., description="Error code", example="VisitNotFound")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[dict] = Field(None, description="Additional error details")
