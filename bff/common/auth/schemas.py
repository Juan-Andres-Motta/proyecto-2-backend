"""
Authentication schemas for Cognito login/signup.
"""

from pydantic import BaseModel, EmailStr, Field, field_validator


class LoginRequest(BaseModel):
    """Request model for user login."""

    email: EmailStr
    password: str = Field(..., min_length=8)


class LoginResponse(BaseModel):
    """Response model for successful login."""

    access_token: str
    id_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int
    user_groups: list[str] = []


class RefreshTokenRequest(BaseModel):
    """Request model for refreshing access token."""

    refresh_token: str


class RefreshTokenResponse(BaseModel):
    """Response model for token refresh."""

    access_token: str
    id_token: str
    token_type: str = "Bearer"
    expires_in: int


class SignupRequest(BaseModel):
    """Request model for user signup - only clients can self-register."""

    # Cognito fields
    email: EmailStr
    password: str = Field(..., min_length=8)
    name: str = Field(..., min_length=1, description="Representative's full name")

    # Client-specific fields (required for creating client in client microservice)
    telefono: str = Field(..., min_length=1)
    nombre_institucion: str = Field(..., min_length=1)
    tipo_institucion: str = Field(
        ...,
        description="Tipo de institución: hospital, clinica, laboratorio, centro_diagnostico"
    )
    nit: str = Field(..., min_length=1)
    direccion: str = Field(..., min_length=1)
    ciudad: str = Field(..., min_length=1)
    pais: str = Field(..., min_length=1)
    representante: str = Field(..., min_length=1)

    # user_type is fixed to "client" - only clients can self-register
    user_type: str = Field(default="client", description="Must be 'client' - only clients can self-register")

    @field_validator("user_type")
    @classmethod
    def validate_user_type(cls, v: str) -> str:
        if v != "client":
            raise ValueError("Only clients can self-register. user_type must be 'client'")
        return v


class SignupResponse(BaseModel):
    """Response model for successful signup."""

    user_id: str
    email: str
    message: str = "User created successfully. Please check your email for verification."


class ErrorResponse(BaseModel):
    """Generic error response."""

    error_code: str
    message: str


class UserMeResponse(BaseModel):
    """Response model for /me endpoint with complete user information."""

    user_id: str
    name: str
    email: str
    groups: list[str] = []
    user_type: str | None = None
    user_details: dict | None = None
