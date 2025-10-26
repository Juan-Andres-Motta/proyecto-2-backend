"""
Authentication schemas for Cognito login/signup.
"""

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    """Request model for user login.

    Web users can only login with client_type='web'.
    Seller and client users can only login with client_type='mobile'.
    """

    email: EmailStr
    password: str
    client_type: str = Field(..., description="Client type: 'web' or 'mobile'")


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
    """Request model for user signup. Only 'client' user type is allowed."""

    email: EmailStr
    password: str = Field(..., min_length=8)
    user_type: str = Field(..., description="Type of user: must be 'client'. Web and seller users are created by administrators.")

    # Client-specific required fields
    telefono: str = Field(..., description="Phone number with country code (e.g., +1234567890)")
    nombre_institucion: str = Field(..., description="Institution name")
    tipo_institucion: str = Field(
        ...,
        description="Institution type: hospital, clinica, laboratorio, centro_diagnostico"
    )
    nit: str = Field(..., description="Tax identification number (NIT)")
    direccion: str = Field(..., description="Institution address")
    ciudad: str = Field(..., description="City")
    pais: str = Field(..., description="Country")
    representante: str = Field(..., description="Legal representative name")


class SignupResponse(BaseModel):
    """Response model for successful signup."""

    user_id: str
    email: str
    cliente_id: str
    nombre_institucion: str
    message: str = "User created successfully. Please check your email for verification."


class ErrorResponse(BaseModel):
    """Generic error response."""

    error_code: str
    message: str
