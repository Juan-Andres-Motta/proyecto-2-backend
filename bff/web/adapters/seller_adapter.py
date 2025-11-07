"""
Seller adapter implementation.

This adapter implements the SellerPort interface using HTTP communication.
Implements saga pattern for seller creation: Cognito -> Seller microservice.
"""

import logging
import re
from uuid import UUID

from common.auth.cognito_service import CognitoService
from common.http_client import HttpClient
from fastapi import HTTPException, status

from ..ports.seller_port import SellerPort
from ..schemas.seller_schemas import (
    PaginatedSalesPlansResponse,
    PaginatedSellersResponse,
    SalesPlanCreate,
    SalesPlanCreateResponse,
    SellerCreate,
    SellerCreateResponse,
)

logger = logging.getLogger(__name__)


class SellerAdapter(SellerPort):
    """
    HTTP adapter for seller microservice operations.

    This adapter implements the SellerPort interface and handles
    communication with the seller microservice via HTTP.
    Implements saga pattern for seller creation with Cognito integration.
    """

    def __init__(self, http_client: HttpClient, cognito_service: CognitoService):
        """
        Initialize the seller adapter.

        Args:
            http_client: Configured HTTP client for the seller service
            cognito_service: Cognito service for authentication operations
        """
        self.client = http_client
        self.cognito_service = cognito_service

    async def create_seller(self, seller_data: SellerCreate) -> SellerCreateResponse:
        """
        Create a new seller using saga pattern.

        Saga steps:
        1. Create user in Cognito with auto-generated password
        2. Create seller record in seller microservice with cognito_user_id
        3. If step 2 fails, rollback step 1 by deleting Cognito user

        Args:
            seller_data: Seller creation data

        Returns:
            SellerCreateResponse with seller ID and message

        Raises:
            HTTPException: If saga fails (with proper rollback)
        """
        logger.info(f"Starting seller creation saga: name='{seller_data.name}', email='{seller_data.email}'")

        cognito_user_id = None
        username = None

        # Generate default password: {SellerName}@Password123
        # Remove spaces and special characters from name
        clean_name = re.sub(r'[^a-zA-Z0-9]', '', seller_data.name)
        default_password = f"{clean_name}@Password123"

        # Step 1: Create user in Cognito
        logger.info("Saga Step 1: Creating seller user in Cognito")
        try:
            cognito_result = await self.cognito_service.create_user(
                email=seller_data.email,
                password=default_password,
                name=seller_data.name,
                user_type="seller",
            )
            cognito_user_id = cognito_result["user_id"]
            username = cognito_result["username"]
            logger.info(f"Saga Step 1 SUCCESS: Cognito seller user created with ID: {cognito_user_id}")
        except Exception as cognito_error:
            logger.error(f"Saga Step 1 FAILED: Cognito seller user creation failed. Error: {str(cognito_error)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create seller authentication: {str(cognito_error)}",
            )

        # Step 1.5: Add user to seller_users Cognito group
        logger.info("Saga Step 1.5: Adding seller user to seller_users group")
        try:
            await self.cognito_service.add_user_to_group(
                username=username,
                group_name="seller_users",
            )
            logger.info(f"Saga Step 1.5 SUCCESS: Seller user added to seller_users group")
        except Exception as group_error:
            logger.error(f"Saga Step 1.5 FAILED: Failed to add seller to group. Error: {str(group_error)}")
            # Rollback: Delete Cognito user
            logger.info("Saga Step 1.5 ROLLBACK: Deleting Cognito user")
            try:
                await self.cognito_service.delete_user(username)
                logger.info("Saga Step 1.5 ROLLBACK SUCCESS: Cognito user deleted")
            except Exception as delete_error:
                logger.error(f"Saga Step 1.5 ROLLBACK FAILED: Could not delete Cognito user. Error: {str(delete_error)}")

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to assign seller permissions: {str(group_error)}",
            )

        # Step 2: Create seller record in seller microservice
        try:
            logger.info("Saga Step 2: Creating seller record in seller microservice")

            # Add cognito_user_id to seller data
            seller_data_with_cognito = seller_data.model_dump(mode="json")
            seller_data_with_cognito["cognito_user_id"] = cognito_user_id

            response_data = await self.client.post(
                "/seller/sellers",
                json=seller_data_with_cognito,
            )
            logger.info(f"Saga Step 2 SUCCESS: Seller record created with ID: {response_data.get('id')}")

            # Saga completed successfully
            logger.info(f"Seller creation saga completed successfully for {seller_data.email}")
            return SellerCreateResponse(**response_data)

        except Exception as seller_error:
            # Saga compensation: rollback Cognito user creation
            logger.error(
                f"Saga Step 2 FAILED: Seller record creation failed. "
                f"Error: {str(seller_error)}. Initiating rollback for Cognito user {username}"
            )

            # Attempt rollback
            rollback_successful = await self._rollback_cognito_user(username)

            if not rollback_successful:
                logger.critical(
                    f"MANUAL INTERVENTION REQUIRED: Cognito seller user {username} ({cognito_user_id}) "
                    f"exists but seller record was not created. Please delete manually."
                )

            # Determine appropriate error response
            # Import here to avoid circular imports
            from common.exceptions import MicroserviceValidationError

            # Extract validation details if available
            error_detail = "Failed to complete seller creation. Please check your input data."
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

            if isinstance(seller_error, MicroserviceValidationError):
                # This is a validation error (422) - return validation details
                status_code = status.HTTP_422_UNPROCESSABLE_ENTITY

                # Try to extract actual validation error from response
                if seller_error.details and "response" in seller_error.details:
                    try:
                        import json
                        response_data = json.loads(seller_error.details["response"])
                        # Try different error message fields (FastAPI uses 'detail', seller service uses 'message')
                        error_detail = response_data.get("detail") or response_data.get("message", error_detail)
                    except (json.JSONDecodeError, KeyError):
                        error_detail = str(seller_error)
                else:
                    error_detail = str(seller_error)

            # Return appropriate error
            raise HTTPException(
                status_code=status_code,
                detail=error_detail,
            )

    async def _rollback_cognito_user(self, username: str) -> bool:
        """
        Rollback helper: Delete Cognito seller user.

        Args:
            username: Username to delete

        Returns:
            bool: True if rollback succeeded, False otherwise
        """
        try:
            await self.cognito_service.delete_user(username)
            logger.info(f"Saga ROLLBACK SUCCESS: Cognito seller user {username} deleted")
            return True
        except Exception as rollback_error:
            logger.error(
                f"Saga ROLLBACK FAILED: Could not delete Cognito seller user {username}. "
                f"Error: {str(rollback_error)}"
            )
            return False

    async def get_sellers(
        self, limit: int = 10, offset: int = 0
    ) -> PaginatedSellersResponse:
        """Retrieve a paginated list of sellers."""
        logger.info(f"Getting sellers: limit={limit}, offset={offset}")
        response_data = await self.client.get(
            "/seller/sellers",
            params={"limit": limit, "offset": offset},
        )
        return PaginatedSellersResponse(**response_data)

    async def create_sales_plan(
        self, sales_plan_data: SalesPlanCreate
    ) -> SalesPlanCreateResponse:
        """Create a new sales plan for a seller."""
        logger.info(f"Creating sales plan: seller_id={sales_plan_data.seller_id}, sales_period={sales_plan_data.sales_period}, goal={sales_plan_data.goal}")
        response_data = await self.client.post(
            "/seller/sales-plans",
            json=sales_plan_data.model_dump(mode="json"),
        )
        # Seller service returns full sales plan object, extract id
        return SalesPlanCreateResponse(
            id=response_data["id"],
            message="Sales plan created successfully"
        )

    async def get_sales_plans(
        self, limit: int = 10, offset: int = 0
    ) -> PaginatedSalesPlansResponse:
        """Retrieve a paginated list of sales plans."""
        logger.info(f"Getting sales plans: limit={limit}, offset={offset}")
        response_data = await self.client.get(
            "/seller/sales-plans",
            params={"limit": limit, "offset": offset},
        )
        return PaginatedSalesPlansResponse(**response_data)

    async def get_seller_sales_plans(
        self, seller_id: UUID, limit: int = 10, offset: int = 0
    ) -> PaginatedSalesPlansResponse:
        """Retrieve sales plans for a specific seller."""
        logger.info(f"Getting seller sales plans: seller_id={seller_id}, limit={limit}, offset={offset}")
        response_data = await self.client.get(
            f"/seller/sellers/{seller_id}/sales-plans",
            params={"limit": limit, "offset": offset},
        )
        return PaginatedSalesPlansResponse(**response_data)
