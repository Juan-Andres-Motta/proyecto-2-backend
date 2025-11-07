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

    @pytest.mark.asyncio
    async def test_validate_token_test_mode_returns_mock_claims(self, jwt_validator):
        """Test TEST_MODE skips validation and returns mock claims."""
        import os
        with patch.dict(os.environ, {"TEST_MODE": "true"}):
            # Create a new validator after setting TEST_MODE
            validator = CognitoJWTValidator(
                user_pool_id="us-east-1_TestPool",
                region="us-east-1",
                client_ids=["test-client"],
            )
            result = await validator.validate_token("any-token")

            assert result is not None
            assert "sub" in result
            assert "cognito:username" in result
            assert "cognito:groups" in result

    @pytest.mark.asyncio
    async def test_validate_token_test_mode_with_email_in_token(self, jwt_validator):
        """Test TEST_MODE extracts email from token payload if present."""
        import os
        import json
        import base64

        # Create a token with email in payload
        payload = {"email": "test@example.com", "sub": "test-user-id"}
        encoded_payload = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
        token = f"header.{encoded_payload}.signature"

        with patch.dict(os.environ, {"TEST_MODE": "true"}):
            validator = CognitoJWTValidator(
                user_pool_id="us-east-1_TestPool",
                region="us-east-1",
                client_ids=["test-client"],
            )
            result = await validator.validate_token(token)

            # Should extract email from payload
            assert result["email"] == "test@example.com"
            assert result["sub"] == "test-user-id"

    @pytest.mark.asyncio
    async def test_validate_token_invalid_token_format(self, jwt_validator, mock_jwks):
        """Test validation fails for invalid token format."""
        jwt_validator.get_jwks = AsyncMock(return_value=mock_jwks)

        with patch("jose.jwt.get_unverified_header") as mock_get_header:
            mock_get_header.side_effect = JWTError("Invalid token format")

            with pytest.raises(JWTError) as exc_info:
                await jwt_validator.validate_token("invalid-format-token")

            assert "Invalid token format" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_validate_token_missing_kid_in_header(self, jwt_validator, mock_jwks):
        """Test validation fails when token header missing kid field."""
        jwt_validator.get_jwks = AsyncMock(return_value=mock_jwks)

        with patch("jose.jwt.get_unverified_header") as mock_get_header:
            mock_get_header.return_value = {}  # No 'kid' field

            with pytest.raises(JWTError) as exc_info:
                await jwt_validator.validate_token("no-kid-token")

            assert "missing 'kid' field" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_validate_token_with_list_audience(self, jwt_validator, mock_jwks):
        """Test validation succeeds with list audience containing valid client_id."""
        jwt_validator.get_jwks = AsyncMock(return_value=mock_jwks)

        mock_claims = {
            "sub": "user-123",
            "email": "test@example.com",
            "aud": ["test-client-id-1", "other-client"],
            "iss": jwt_validator.issuer,
            "exp": 9999999999,
        }

        with patch("jose.jwt.get_unverified_header") as mock_get_header:
            with patch("jose.jwt.decode") as mock_decode:
                mock_get_header.return_value = {"kid": "test-key-id-1"}
                mock_decode.return_value = mock_claims

                result = await jwt_validator.validate_token("valid-token")

                assert result == mock_claims

    @pytest.mark.asyncio
    async def test_validate_token_with_client_id_claim(self, jwt_validator, mock_jwks):
        """Test validation with client_id claim instead of aud."""
        jwt_validator.get_jwks = AsyncMock(return_value=mock_jwks)

        mock_claims = {
            "sub": "user-123",
            "email": "test@example.com",
            "client_id": "test-client-id-1",
            "iss": jwt_validator.issuer,
            "exp": 9999999999,
        }

        with patch("jose.jwt.get_unverified_header") as mock_get_header:
            with patch("jose.jwt.decode") as mock_decode:
                mock_get_header.return_value = {"kid": "test-key-id-1"}
                mock_decode.return_value = mock_claims

                result = await jwt_validator.validate_token("valid-token")

                assert result == mock_claims

    @pytest.mark.asyncio
    async def test_validate_token_invalid_client_id_in_list(self, jwt_validator, mock_jwks):
        """Test validation fails when no valid client_id in list."""
        jwt_validator.get_jwks = AsyncMock(return_value=mock_jwks)

        with patch("jose.jwt.get_unverified_header") as mock_get_header:
            with patch("jose.jwt.decode") as mock_decode:
                mock_claims = {
                    "sub": "user-123",
                    "aud": ["invalid-client-1", "invalid-client-2"],
                    "iss": jwt_validator.issuer,
                    "exp": 9999999999,
                }
                mock_get_header.return_value = {"kid": "test-key-id-1"}
                mock_decode.return_value = mock_claims
                # Need to mock the validation to trigger client_id check
                mock_decode.side_effect = JWTError("Invalid audience")

                with pytest.raises(JWTError):
                    await jwt_validator.validate_token("invalid-client-token")


class TestGetUserGroups:
    """Tests for get_user_groups() method."""

    def test_get_user_groups_returns_groups(self, jwt_validator):
        """Test get_user_groups extracts cognito:groups from claims."""
        claims = {
            "sub": "user-123",
            "cognito:groups": ["group1", "group2", "group3"],
        }

        result = jwt_validator.get_user_groups(claims)

        assert result == ["group1", "group2", "group3"]

    def test_get_user_groups_empty_list(self, jwt_validator):
        """Test get_user_groups returns empty list when no groups."""
        claims = {"sub": "user-123"}

        result = jwt_validator.get_user_groups(claims)

        assert result == []

    def test_get_user_groups_with_empty_groups(self, jwt_validator):
        """Test get_user_groups with empty cognito:groups."""
        claims = {
            "sub": "user-123",
            "cognito:groups": [],
        }

        result = jwt_validator.get_user_groups(claims)

        assert result == []


class TestGetUserEmail:
    """Tests for get_user_email() method."""

    def test_get_user_email_returns_email(self, jwt_validator):
        """Test get_user_email extracts email from claims."""
        claims = {
            "sub": "user-123",
            "email": "test@example.com",
        }

        result = jwt_validator.get_user_email(claims)

        assert result == "test@example.com"

    def test_get_user_email_returns_none_when_missing(self, jwt_validator):
        """Test get_user_email returns None when email not in claims."""
        claims = {"sub": "user-123"}

        result = jwt_validator.get_user_email(claims)

        assert result is None


class TestGetUserId:
    """Tests for get_user_id() method."""

    def test_get_user_id_returns_sub(self, jwt_validator):
        """Test get_user_id extracts sub (user ID) from claims."""
        user_id = "12345678-1234-5678-1234-567812345678"
        claims = {"sub": user_id}

        result = jwt_validator.get_user_id(claims)

        assert result == user_id

    def test_get_user_id_returns_none_when_missing(self, jwt_validator):
        """Test get_user_id returns None when sub not in claims."""
        claims = {"email": "test@example.com"}

        result = jwt_validator.get_user_id(claims)

        assert result is None


class TestGetUsername:
    """Tests for get_username() method."""

    def test_get_username_returns_username(self, jwt_validator):
        """Test get_username extracts cognito:username from claims."""
        claims = {
            "sub": "user-123",
            "cognito:username": "testuser",
        }

        result = jwt_validator.get_username(claims)

        assert result == "testuser"

    def test_get_username_returns_none_when_missing(self, jwt_validator):
        """Test get_username returns None when not in claims."""
        claims = {"sub": "user-123"}

        result = jwt_validator.get_username(claims)

        assert result is None


class TestLocalStackEndpoint:
    """Tests for LocalStack endpoint handling."""

    def test_init_uses_localstack_endpoint_when_set(self, monkeypatch):
        """Test issuer and JWKS URL use LocalStack endpoint when AWS_ENDPOINT_URL set."""
        monkeypatch.setenv("AWS_ENDPOINT_URL", "http://localhost:4566")

        validator = CognitoJWTValidator(
            user_pool_id="us-east-1_TestPool",
            region="us-east-1",
            client_ids=["test-client"],
        )

        assert validator.issuer == "http://localhost:4566/us-east-1_TestPool"
        assert validator.jwks_url == "http://localhost:4566/us-east-1_TestPool/.well-known/jwks.json"

    def test_init_strips_trailing_slash_from_localstack_endpoint(self, monkeypatch):
        """Test trailing slash is removed from LocalStack endpoint."""
        monkeypatch.setenv("AWS_ENDPOINT_URL", "http://localhost:4566/")

        validator = CognitoJWTValidator(
            user_pool_id="us-east-1_TestPool",
            region="us-east-1",
            client_ids=["test-client"],
        )

        assert validator.issuer == "http://localhost:4566/us-east-1_TestPool"
        assert not validator.jwks_url.startswith("http://localhost:4566//")

    def test_init_uses_aws_endpoint_when_not_set(self):
        """Test uses real AWS endpoint when AWS_ENDPOINT_URL not set."""
        validator = CognitoJWTValidator(
            user_pool_id="us-east-1_TestPool",
            region="us-east-1",
            client_ids=["test-client"],
        )

        assert "cognito-idp" in validator.issuer
        assert "amazonaws.com" in validator.issuer


class TestValidateTokenClientIdValidation:
    """Tests for client_id validation in validate_token."""

    @pytest.mark.asyncio
    async def test_validate_token_invalid_single_client_id(self, jwt_validator, mock_jwks):
        """Test validation fails when single client_id doesn't match allowed clients."""
        jwt_validator.get_jwks = AsyncMock(return_value=mock_jwks)

        mock_claims = {
            "sub": "user-123",
            "client_id": "invalid-client-id",
            "iss": jwt_validator.issuer,
            "exp": 9999999999,
        }

        with patch("jose.jwt.get_unverified_header") as mock_get_header:
            with patch("jose.jwt.decode") as mock_decode:
                mock_get_header.return_value = {"kid": "test-key-id-1"}
                mock_decode.return_value = mock_claims

                with pytest.raises(JWTError) as exc_info:
                    await jwt_validator.validate_token("invalid-client-id-token")

                assert "Invalid client_id" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_validate_token_no_client_id_and_no_aud(self, jwt_validator, mock_jwks):
        """Test validation succeeds when token has neither client_id nor aud (valid case)."""
        jwt_validator.get_jwks = AsyncMock(return_value=mock_jwks)

        mock_claims = {
            "sub": "user-123",
            "email": "test@example.com",
            "iss": jwt_validator.issuer,
            "exp": 9999999999,
        }

        with patch("jose.jwt.get_unverified_header") as mock_get_header:
            with patch("jose.jwt.decode") as mock_decode:
                mock_get_header.return_value = {"kid": "test-key-id-1"}
                mock_decode.return_value = mock_claims

                result = await jwt_validator.validate_token("token-without-audience")

                assert result == mock_claims
                assert "client_id" not in result
                assert "aud" not in result


class TestGetMockClaims:
    """Tests for _get_mock_claims method in TEST_MODE."""

    @pytest.mark.asyncio
    async def test_get_mock_claims_with_multiple_groups(self, jwt_validator):
        """Test mock claims with multiple groups in token."""
        import os
        import json
        import base64

        # Create token with multiple groups
        payload = {
            "email": "seller@example.com",
            "sub": "seller-user-id",
            "cognito:groups": ["seller_users", "admin"],
        }
        encoded_payload = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
        token = f"header.{encoded_payload}.signature"

        with patch.dict(os.environ, {"TEST_MODE": "true"}):
            validator = CognitoJWTValidator(
                user_pool_id="us-east-1_TestPool",
                region="us-east-1",
                client_ids=["test-client"],
            )
            result = await validator.validate_token(token)

            assert result["cognito:groups"] == ["seller_users", "admin"]
            assert result["email"] == "seller@example.com"
            assert result["sub"] == "seller-user-id"

    @pytest.mark.asyncio
    async def test_get_mock_claims_with_invalid_base64(self, jwt_validator):
        """Test mock claims falls back to defaults with invalid base64 in token."""
        import os

        # Token with invalid base64
        token = "header.invalid!!!base64.signature"

        with patch.dict(os.environ, {"TEST_MODE": "true"}):
            validator = CognitoJWTValidator(
                user_pool_id="us-east-1_TestPool",
                region="us-east-1",
                client_ids=["test-client"],
            )
            result = await validator.validate_token(token)

            # Should return defaults
            assert result["sub"] is not None
            assert result["cognito:username"] == "testwebuser"
            assert result["cognito:groups"] == ["web_users"]

    @pytest.mark.asyncio
    async def test_get_mock_claims_partial_payload_extraction(self, jwt_validator):
        """Test mock claims extracts only available fields from payload."""
        import os
        import json
        import base64

        # Create token with only email (no sub, no groups)
        payload = {"email": "partial@example.com"}
        encoded_payload = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
        token = f"header.{encoded_payload}.signature"

        with patch.dict(os.environ, {"TEST_MODE": "true"}):
            validator = CognitoJWTValidator(
                user_pool_id="us-east-1_TestPool",
                region="us-east-1",
                client_ids=["test-client"],
            )
            result = await validator.validate_token(token)

            # Should have extracted email, but other fields are defaults
            assert result["email"] == "partial@example.com"
            assert result["cognito:username"] == "testwebuser"  # Default
            assert result["cognito:groups"] == ["web_users"]  # Default
