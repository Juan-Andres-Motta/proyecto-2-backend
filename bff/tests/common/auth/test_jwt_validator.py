"""Unit tests for CognitoJWTValidator."""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from jose import jwt
from jose.exceptions import JWTError

from common.auth.jwt_validator import CognitoJWTValidator


@pytest.fixture
def jwt_validator():
    """Fixture providing JWT validator instance."""
    return CognitoJWTValidator(
        user_pool_id="us-east-1_TestPool",
        region="us-east-1",
        client_ids=["test-client-id-1", "test-client-id-2"],
    )


@pytest.fixture
def mock_jwks():
    """Fixture providing mock JWKS response."""
    return {
        "keys": [
            {
                "kid": "test-key-id-1",
                "kty": "RSA",
                "use": "sig",
                "n": "test-modulus",
                "e": "AQAB",
            },
            {
                "kid": "test-key-id-2",
                "kty": "RSA",
                "use": "sig",
                "n": "test-modulus-2",
                "e": "AQAB",
            },
        ]
    }


class TestCognitoJWTValidatorInit:
    """Tests for CognitoJWTValidator initialization."""

    def test_init_sets_correct_issuer_url(self, jwt_validator):
        """Test issuer URL is correctly constructed."""
        expected_issuer = "https://cognito-idp.us-east-1.amazonaws.com/us-east-1_TestPool"
        assert jwt_validator.issuer == expected_issuer

    def test_init_sets_correct_jwks_url(self, jwt_validator):
        """Test JWKS URL is correctly constructed."""
        expected_jwks_url = (
            "https://cognito-idp.us-east-1.amazonaws.com/"
            "us-east-1_TestPool/.well-known/jwks.json"
        )
        assert jwt_validator.jwks_url == expected_jwks_url

    def test_init_accepts_single_client_id(self):
        """Test validator accepts single client ID."""
        validator = CognitoJWTValidator(
            user_pool_id="us-east-1_TestPool",
            region="us-east-1",
            client_ids="single-client-id",
        )
        assert validator.client_ids == "single-client-id"

    def test_init_accepts_multiple_client_ids(self):
        """Test validator accepts list of client IDs."""
        validator = CognitoJWTValidator(
            user_pool_id="us-east-1_TestPool",
            region="us-east-1",
            client_ids=["client-1", "client-2"],
        )
        assert validator.client_ids == ["client-1", "client-2"]


class TestGetJWKS:
    """Tests for get_jwks() method."""

    @pytest.mark.asyncio
    async def test_get_jwks_success(self, jwt_validator, mock_jwks):
        """Test successful JWKS retrieval."""
        mock_response = Mock()
        mock_response.json.return_value = mock_jwks

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            result = await jwt_validator.get_jwks()

            assert result == mock_jwks
            assert "keys" in result
            assert len(result["keys"]) == 2

    @pytest.mark.asyncio
    async def test_get_jwks_caches_result(self, jwt_validator, mock_jwks):
        """Test JWKS response is cached."""
        mock_response = Mock()
        mock_response.json.return_value = mock_jwks

        with patch("httpx.AsyncClient") as mock_client:
            mock_get = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__.return_value.get = mock_get

            # First call
            result1 = await jwt_validator.get_jwks()
            # Second call
            result2 = await jwt_validator.get_jwks()

            # HTTP request should only be made once (cached)
            assert mock_get.call_count == 1
            assert result1 == result2
            assert result1 is result2  # Same object reference

    @pytest.mark.asyncio
    async def test_get_jwks_http_error(self, jwt_validator):
        """Test JWKS retrieval handles HTTP errors."""
        import httpx

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=httpx.HTTPError("Network error")
            )

            with pytest.raises(httpx.HTTPError):
                await jwt_validator.get_jwks()


class TestValidateToken:
    """Tests for validate_token() method."""

    @pytest.mark.asyncio
    async def test_validate_token_success(self, jwt_validator, mock_jwks):
        """Test successful token validation."""
        # Mock JWKS retrieval
        jwt_validator.get_jwks = AsyncMock(return_value=mock_jwks)

        # Mock JWT decoding
        mock_claims = {
            "sub": "user-123",
            "email": "test@example.com",
            "cognito:groups": ["web_users"],
            "aud": "test-client-id-1",
            "iss": jwt_validator.issuer,
            "exp": 9999999999,
        }

        with patch("jose.jwt.get_unverified_header") as mock_get_header:
            with patch("jose.jwt.decode") as mock_decode:
                mock_get_header.return_value = {"kid": "test-key-id-1"}
                mock_decode.return_value = mock_claims

                result = await jwt_validator.validate_token("valid-token")

                assert result == mock_claims
                assert result["sub"] == "user-123"
                assert result["email"] == "test@example.com"

    @pytest.mark.asyncio
    async def test_validate_token_kid_not_found(self, jwt_validator, mock_jwks):
        """Test validation fails when key ID not in JWKS."""
        jwt_validator.get_jwks = AsyncMock(return_value=mock_jwks)

        with patch("jose.jwt.get_unverified_header") as mock_get_header:
            mock_get_header.return_value = {"kid": "unknown-key-id"}

            with pytest.raises(JWTError) as exc_info:
                await jwt_validator.validate_token("token-with-unknown-kid")

            assert "Public key not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_validate_token_expired(self, jwt_validator, mock_jwks):
        """Test validation fails for expired token."""
        jwt_validator.get_jwks = AsyncMock(return_value=mock_jwks)

        with patch("jose.jwt.get_unverified_header") as mock_get_header:
            with patch("jose.jwt.decode") as mock_decode:
                mock_get_header.return_value = {"kid": "test-key-id-1"}
                mock_decode.side_effect = JWTError("Signature has expired")

                with pytest.raises(JWTError):
                    await jwt_validator.validate_token("expired-token")

    @pytest.mark.asyncio
    async def test_validate_token_invalid_signature(self, jwt_validator, mock_jwks):
        """Test validation fails for invalid signature."""
        jwt_validator.get_jwks = AsyncMock(return_value=mock_jwks)

        with patch("jose.jwt.get_unverified_header") as mock_get_header:
            with patch("jose.jwt.decode") as mock_decode:
                mock_get_header.return_value = {"kid": "test-key-id-1"}
                mock_decode.side_effect = JWTError("Signature verification failed")

                with pytest.raises(JWTError):
                    await jwt_validator.validate_token("invalid-signature-token")

    @pytest.mark.asyncio
    async def test_validate_token_invalid_issuer(self, jwt_validator, mock_jwks):
        """Test validation fails for invalid issuer."""
        jwt_validator.get_jwks = AsyncMock(return_value=mock_jwks)

        with patch("jose.jwt.get_unverified_header") as mock_get_header:
            with patch("jose.jwt.decode") as mock_decode:
                mock_get_header.return_value = {"kid": "test-key-id-1"}
                mock_decode.side_effect = JWTError("Invalid issuer")

                with pytest.raises(JWTError):
                    await jwt_validator.validate_token("invalid-issuer-token")

    @pytest.mark.asyncio
    async def test_validate_token_invalid_audience(self, jwt_validator, mock_jwks):
        """Test validation fails for invalid audience."""
        jwt_validator.get_jwks = AsyncMock(return_value=mock_jwks)

        with patch("jose.jwt.get_unverified_header") as mock_get_header:
            with patch("jose.jwt.decode") as mock_decode:
                mock_get_header.return_value = {"kid": "test-key-id-1"}
                mock_decode.side_effect = JWTError("Invalid audience")

                with pytest.raises(JWTError):
                    await jwt_validator.validate_token("invalid-audience-token")
