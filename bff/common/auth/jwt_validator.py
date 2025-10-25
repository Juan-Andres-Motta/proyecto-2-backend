"""JWT token validation using AWS Cognito public keys."""

import httpx
from jose import jwt, JWTError
from typing import Dict, List, Optional
from functools import lru_cache


class CognitoJWTValidator:
    """Validates JWT tokens from AWS Cognito User Pool."""

    def __init__(
        self,
        user_pool_id: str,
        region: str,
        client_ids: List[str],
    ):
        """
        Initialize JWT validator.

        Args:
            user_pool_id: Cognito User Pool ID
            region: AWS region (e.g., 'us-east-1')
            client_ids: List of allowed client IDs (web + mobile)
        """
        self.user_pool_id = user_pool_id
        self.region = region
        self.client_ids = client_ids
        self.issuer = (
            f"https://cognito-idp.{region}.amazonaws.com/{user_pool_id}"
        )
        self.jwks_url = f"{self.issuer}/.well-known/jwks.json"
        self._jwks_cache: Optional[Dict] = None

    async def get_jwks(self) -> Dict:
        """
        Fetch JSON Web Key Set from Cognito.

        Returns:
            JWKS dictionary containing public keys

        Note:
            Results are cached to avoid repeated requests.
            In production, consider adding TTL-based cache invalidation.
        """
        if self._jwks_cache is None:
            async with httpx.AsyncClient() as client:
                response = await client.get(self.jwks_url, timeout=10.0)
                response.raise_for_status()
                self._jwks_cache = response.json()

        return self._jwks_cache

    async def validate_token(self, token: str) -> Dict:
        """
        Validate JWT token and extract claims.

        Args:
            token: JWT token string

        Returns:
            Dictionary containing token claims (user info, groups, etc.)

        Raises:
            JWTError: If token is invalid, expired, or signature verification fails
        """
        # Fetch public keys
        jwks = await self.get_jwks()

        # Decode header without verification to get key ID
        try:
            header = jwt.get_unverified_header(token)
        except JWTError as e:
            raise JWTError(f"Invalid token format: {str(e)}")

        kid = header.get("kid")
        if not kid:
            raise JWTError("Token header missing 'kid' field")

        # Find the matching public key
        key = next((k for k in jwks["keys"] if k["kid"] == kid), None)
        if not key:
            raise JWTError(f"Public key not found for kid: {kid}")

        # Validate and decode token
        # Note: Cognito access tokens use 'client_id' claim instead of 'aud'
        # So we disable audience verification and manually check client_id
        try:
            claims = jwt.decode(
                token,
                key,
                algorithms=["RS256"],
                issuer=self.issuer,
                options={
                    "verify_signature": True,
                    "verify_aud": False,  # Access tokens don't have 'aud', they have 'client_id'
                    "verify_iss": True,
                    "verify_exp": True,
                },
            )
        except JWTError as e:
            raise JWTError(f"Token validation failed: {str(e)}")

        # Manually verify client_id for access tokens (or aud for ID tokens)
        token_client_id = claims.get("client_id") or claims.get("aud")
        if token_client_id:
            # Handle both single string and list audience
            if isinstance(token_client_id, list):
                if not any(cid in self.client_ids for cid in token_client_id):
                    raise JWTError(f"Invalid client_id/audience: {token_client_id}")
            elif token_client_id not in self.client_ids:
                raise JWTError(f"Invalid client_id/audience: {token_client_id}")

        return claims

    def get_user_groups(self, claims: Dict) -> List[str]:
        """
        Extract Cognito user groups from token claims.

        Args:
            claims: Decoded JWT claims

        Returns:
            List of group names the user belongs to
        """
        return claims.get("cognito:groups", [])

    def get_user_email(self, claims: Dict) -> Optional[str]:
        """
        Extract user email from token claims.

        Args:
            claims: Decoded JWT claims

        Returns:
            User email address or None
        """
        return claims.get("email")

    def get_user_id(self, claims: Dict) -> Optional[str]:
        """
        Extract user ID (sub) from token claims.

        Args:
            claims: Decoded JWT claims

        Returns:
            Cognito user ID (UUID) or None
        """
        return claims.get("sub")

    def get_username(self, claims: Dict) -> Optional[str]:
        """
        Extract Cognito username from token claims.

        Args:
            claims: Decoded JWT claims

        Returns:
            Cognito username or None
        """
        return claims.get("cognito:username")


@lru_cache(maxsize=1)
def get_jwt_validator(
    user_pool_id: str, region: str, client_ids: tuple
) -> CognitoJWTValidator:
    """
    Factory function to get cached JWT validator instance.

    Args:
        user_pool_id: Cognito User Pool ID
        region: AWS region
        client_ids: Tuple of allowed client IDs (must be tuple for caching)

    Returns:
        CognitoJWTValidator instance
    """
    return CognitoJWTValidator(
        user_pool_id=user_pool_id,
        region=region,
        client_ids=list(client_ids),
    )
