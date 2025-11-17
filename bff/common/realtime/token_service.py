"""Service for generating Ably token requests with appropriate permissions."""

import json
import logging
import time
from typing import Dict, List, Optional, Any

from .schemas import AblyTokenRequest, AblyTokenResponse

logger = logging.getLogger(__name__)


class AblyTokenService:
    """Service for generating Ably token requests with user-specific permissions.

    This service creates token requests that allow clients to authenticate with Ably
    and subscribe to channels they're authorized for. Tokens are generated with
    subscribe-only permissions to prevent clients from publishing events.

    Channel permissions by user type:
        - web_users: Can subscribe to web:{user_id} (personal) and web:broadcasts (shared)
        - seller_users: Can subscribe to mobile:products
        - client_users: Can subscribe to mobile:products

    Attributes:
        api_key: Ably API key in format "key_id:key_secret"
    """

    def __init__(self, api_key: str):
        """Initialize the Ably token service.

        Args:
            api_key: Ably API key in format "key_id:key_secret"

        Raises:
            ValueError: If api_key is empty or invalid format
        """
        if not api_key:
            raise ValueError("Ably API key is required")

        if ":" not in api_key:
            raise ValueError("Ably API key must be in format 'key_id:key_secret'")

        self.api_key = api_key
        self._client: Optional[Any] = None

        logger.info("AblyTokenService initialized")

    def _get_client(self):
        """Lazy-load the Ably REST client.

        Returns:
            AblyRest client instance

        Raises:
            ImportError: If ably package is not installed
            Exception: If client initialization fails
        """
        if self._client is None:
            try:
                from ably import AblyRest
                self._client = AblyRest(self.api_key)
                logger.info("Ably REST client initialized for token generation")
            except ImportError:
                logger.error(
                    "Ably SDK not installed. Run: poetry add ably",
                    exc_info=True
                )
                raise
            except Exception as e:
                logger.error(
                    f"Failed to initialize Ably client: {e}",
                    exc_info=True
                )
                raise

        return self._client

    def _build_capabilities(
        self,
        user_id: str,
        user_type: str
    ) -> Dict[str, List[str]]:
        """Build channel capabilities based on user type.

        Args:
            user_id: Unique user identifier
            user_type: Type of user (web, seller, client)

        Returns:
            Dictionary mapping channel names to permission lists

        Example:
            For web user:
            {
                "web:user123": ["subscribe"],
                "web:broadcasts": ["subscribe"]
            }

            For seller/client:
            {"mobile:products": ["subscribe"]}
        """
        capabilities = {}

        if user_type == "web":
            # Web users get their personal channel for reports
            personal_channel = f"web:{user_id}"
            capabilities[personal_channel] = ["subscribe"]

            # Web users also get the shared broadcasts channel for routes
            capabilities["web:broadcasts"] = ["subscribe"]

            logger.debug(
                f"Built web user capabilities: {personal_channel}, web:broadcasts"
            )

        elif user_type in ("seller", "client"):
            # Mobile users get the shared products channel
            channel = "mobile:products"
            capabilities[channel] = ["subscribe"]
            logger.debug(f"Built mobile user capabilities: {channel}")

        else:
            logger.warning(
                f"Unknown user_type '{user_type}' for user {user_id}, "
                "defaulting to no capabilities"
            )

        return capabilities

    async def generate_token_request(
        self,
        user_id: str,
        user_type: str,
        client_id: Optional[str] = None,
        ttl: int = 3600000
    ) -> AblyTokenResponse:
        """Generate an Ably token request for the authenticated user.

        This method creates a token request that the client can use to authenticate
        with Ably. The token request is signed server-side and includes appropriate
        channel permissions based on the user type.

        Args:
            user_id: Unique identifier for the user
            user_type: Type of user (web, seller, client)
            client_id: Optional client identifier (defaults to user_id)
            ttl: Time-to-live in milliseconds (default: 3600000 = 1 hour)

        Returns:
            Dictionary containing:
                - token_request: Ably token request object with signature
                - expires_at: Unix timestamp in milliseconds when token expires
                - channels: List of channels the token has access to

        Raises:
            ValueError: If user_id or user_type is invalid
            Exception: If token generation fails

        Example:
            ```python
            service = AblyTokenService(api_key="key:secret")
            result = service.generate_token_request(
                user_id="user123",
                user_type="web",
                client_id="user123@example.com"
            )
            # Returns:
            # {
            #     "token_request": {...},
            #     "expires_at": 1640003600000,
            #     "channels": ["web:user123", "web:broadcasts"]
            # }
            ```
        """
        if not user_id:
            raise ValueError("user_id is required")

        if not user_type:
            raise ValueError("user_type is required")

        if user_type not in ("web", "seller", "client"):
            raise ValueError(
                f"Invalid user_type: {user_type}. "
                "Must be one of: web, seller, client"
            )

        # Use user_id as client_id if not provided
        effective_client_id = client_id or user_id

        # Build capabilities based on user type
        capabilities = self._build_capabilities(user_id, user_type)

        if not capabilities:
            raise ValueError(
                f"No capabilities could be determined for user_type: {user_type}"
            )

        # Convert capabilities to JSON string (compact format, no spaces)
        # This is important for MAC signature calculation
        capability_json = json.dumps(capabilities, separators=(',', ':'))

        logger.info(
            f"Generating token request for user {user_id} ({user_type}) "
            f"with capabilities: {capability_json}"
        )

        try:
            # Get Ably client
            client = self._get_client()

            # Create token request with capabilities
            token_request_obj = await client.auth.create_token_request({
                "client_id": effective_client_id,
                "ttl": ttl,
                "capability": capability_json
            })

            # Create typed token request
            token_request = AblyTokenRequest(
                keyName=token_request_obj.key_name,
                clientId=token_request_obj.client_id,
                ttl=token_request_obj.ttl,
                timestamp=token_request_obj.timestamp,
                capability=token_request_obj.capability,
                nonce=token_request_obj.nonce,
                mac=token_request_obj.mac
            )

            # Calculate expiration time
            current_time = int(time.time() * 1000)
            expires_at = current_time + ttl

            # Get list of channels
            channels = list(capabilities.keys())

            # Create typed response
            response = AblyTokenResponse(
                token_request=token_request,
                expires_at=expires_at,
                channels=channels
            )

            logger.info(
                f"Successfully generated token request for user {user_id}",
                extra={
                    "user_id": user_id,
                    "user_type": user_type,
                    "client_id": effective_client_id,
                    "channels": channels,
                    "ttl_minutes": ttl / 60000
                }
            )

            return response

        except Exception as e:
            logger.error(
                f"Failed to generate token request for user {user_id}: {e}",
                exc_info=True
            )
            raise
