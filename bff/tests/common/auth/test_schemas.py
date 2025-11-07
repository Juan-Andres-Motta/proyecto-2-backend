"""Unit tests for authentication schemas."""

import pytest
from pydantic import ValidationError

from common.auth.schemas import (
    LoginRequest,
    SignupRequest,
    RefreshTokenRequest,
)


class TestLoginRequest:
    """Test LoginRequest schema."""

    def test_valid_login_request(self):
        """Test creating a valid login request."""
        login = LoginRequest(
            email="user@example.com",
            password="SecurePassword123"
        )
        assert login.email == "user@example.com"
        assert login.password == "SecurePassword123"

    def test_invalid_email_format(self):
        """Test that invalid email format is rejected."""
        with pytest.raises(ValidationError):
            LoginRequest(
                email="invalid-email",
                password="SecurePassword123"
            )

    def test_password_too_short(self):
        """Test that password shorter than 8 characters is rejected."""
        with pytest.raises(ValidationError):
            LoginRequest(
                email="user@example.com",
                password="Short1"
            )


class TestSignupRequest:
    """Test SignupRequest schema."""

    def test_valid_signup_request(self):
        """Test creating a valid signup request."""
        signup = SignupRequest(
            email="newuser@example.com",
            password="SecurePassword123",
            name="John Doe",
            telefono="+1234567890",
            nombre_institucion="Hospital Central",
            tipo_institucion="hospital",
            nit="123456789",
            direccion="123 Main St",
            ciudad="New York",
            pais="USA",
            representante="Jane Smith"
        )
        assert signup.email == "newuser@example.com"
        assert signup.user_type == "client"

    def test_invalid_user_type_seller(self):
        """Test that non-client user_type is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            SignupRequest(
                email="user@example.com",
                password="SecurePassword123",
                name="John Doe",
                telefono="+1234567890",
                nombre_institucion="Hospital Central",
                tipo_institucion="hospital",
                nit="123456789",
                direccion="123 Main St",
                ciudad="New York",
                pais="USA",
                representante="Jane Smith",
                user_type="seller"
            )
        assert "only clients can self-register" in str(exc_info.value).lower()

    def test_invalid_user_type_web_user(self):
        """Test that web_user type is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            SignupRequest(
                email="user@example.com",
                password="SecurePassword123",
                name="John Doe",
                telefono="+1234567890",
                nombre_institucion="Hospital Central",
                tipo_institucion="hospital",
                nit="123456789",
                direccion="123 Main St",
                ciudad="New York",
                pais="USA",
                representante="Jane Smith",
                user_type="web_user"
            )
        assert "only clients can self-register" in str(exc_info.value).lower()

    def test_missing_required_field(self):
        """Test that missing required field raises validation error."""
        with pytest.raises(ValidationError):
            SignupRequest(
                email="user@example.com",
                password="SecurePassword123",
                name="John Doe",
                # Missing telefono and other required fields
            )

    def test_empty_name_invalid(self):
        """Test that empty name is invalid."""
        with pytest.raises(ValidationError):
            SignupRequest(
                email="user@example.com",
                password="SecurePassword123",
                name="",  # Empty name
                telefono="+1234567890",
                nombre_institucion="Hospital Central",
                tipo_institucion="hospital",
                nit="123456789",
                direccion="123 Main St",
                ciudad="New York",
                pais="USA",
                representante="Jane Smith"
            )


class TestRefreshTokenRequest:
    """Test RefreshTokenRequest schema."""

    def test_valid_refresh_token_request(self):
        """Test creating a valid refresh token request."""
        refresh = RefreshTokenRequest(
            refresh_token="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
        )
        assert refresh.refresh_token.startswith("eyJ")
