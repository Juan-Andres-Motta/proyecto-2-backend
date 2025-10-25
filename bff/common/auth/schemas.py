"""
Authentication schemas for Cognito login/signup.
"""

from pydantic import BaseModel, EmailStr, Field


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
    """Request model for user signup."""

    email: EmailStr
    password: str = Field(..., min_length=8)
    user_type: str = Field(..., description="Type of user: 'web', 'seller', or 'client'")


class SignupResponse(BaseModel):
    """Response model for successful signup."""

    user_id: str
    email: str
    message: str = "User created successfully. Please check your email for verification."


class ErrorResponse(BaseModel):
    """Generic error response."""

    error_code: str
    message: str
