from datetime import datetime
from typing import List
from uuid import UUID

import pycountry
from pydantic import BaseModel, EmailStr, field_validator

from .examples import provider_create_example


class ProviderCreate(BaseModel):
    name: str
    nit: str
    contact_name: str
    email: EmailStr
    phone: str
    address: str
    country: str

    model_config = {"json_schema_extra": {"examples": [provider_create_example]}}

    @field_validator("name", "contact_name", "nit", "phone", "address", "country")
    @classmethod
    def trim_and_lower(cls, v: str) -> str:
        return v.strip().lower()

    @field_validator("country")
    @classmethod
    def normalize_country(cls, v: str) -> str:
        v = v.strip().upper()
        try:
            country = (
                pycountry.countries.get(name=v)
                or pycountry.countries.get(alpha_2=v)
                or pycountry.countries.get(alpha_3=v)
            )
            if country:
                return country.alpha_2
            else:
                raise ValueError(f"Invalid country: {v}")
        except LookupError:
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


class PaginatedProvidersResponse(BaseModel):
    items: List[ProviderResponse]
    total: int
    page: int
    size: int
    has_next: bool
    has_previous: bool
