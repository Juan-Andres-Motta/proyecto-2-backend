from datetime import datetime
from typing import List
from uuid import UUID

import pycountry
from pydantic import BaseModel, EmailStr, field_serializer, field_validator

from ..examples.provider_examples import provider_create_example


class ProviderCreate(BaseModel):
    name: str
    nit: str
    contact_name: str
    email: EmailStr
    phone: str
    address: str
    country: str

    model_config = {"json_schema_extra": {"examples": [provider_create_example]}}

    @field_validator("name", "contact_name", "address")
    @classmethod
    def trim_and_title(cls, v: str) -> str:
        """Trim whitespace and capitalize each word."""
        return v.strip().title()

    @field_validator("nit", "phone")
    @classmethod
    def trim_only(cls, v: str) -> str:
        """Trim whitespace only."""
        return v.strip()

    @field_validator("country")
    @classmethod
    def normalize_country(cls, v: str) -> str:
        """Normalize country name/code to alpha-2 code.

        pycountry.countries.get() returns None if not found, so no LookupError is raised.
        """
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


class ProviderResponse(BaseModel):
    id: UUID
    name: str
    nit: str
    contact_name: str
    email: str
    phone: str
    address: str
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


class PaginatedProvidersResponse(BaseModel):
    items: List[ProviderResponse]
    total: int
    page: int
    size: int
    has_next: bool
    has_previous: bool
