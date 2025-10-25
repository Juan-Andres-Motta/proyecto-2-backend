# AWS Cognito User Pool for MediSupply Authentication
# Sprint 1: Email-Password authentication only
# Sprint 2+: MFA/OTP will be added later

# Cognito User Pool
resource "aws_cognito_user_pool" "main" {
  name = "${var.name_prefix}-user-pool"

  # User attributes configuration
  alias_attributes         = ["email"]
  auto_verified_attributes = ["email"]

  # Password policy
  password_policy {
    minimum_length                   = 8
    require_lowercase                = true
    require_numbers                  = true
    require_symbols                  = false  # More flexible for MVP
    require_uppercase                = true
    temporary_password_validity_days = 7
  }

  # Account recovery settings
  account_recovery_setting {
    recovery_mechanism {
      name     = "verified_email"
      priority = 1
    }
  }

  # User pool schema - required attributes
  schema {
    name                = "email"
    attribute_data_type = "String"
    mutable             = true
    required            = true

    string_attribute_constraints {
      min_length = 1
      max_length = 256
    }
  }

  schema {
    name                = "name"
    attribute_data_type = "String"
    mutable             = true
    required            = true

    string_attribute_constraints {
      min_length = 1
      max_length = 256
    }
  }

  # Custom attribute for user type (web/seller/client)
  schema {
    name                     = "user_type"
    attribute_data_type      = "String"
    mutable                  = true
    required                 = false
    developer_only_attribute = false

    string_attribute_constraints {
      min_length = 1
      max_length = 50
    }
  }

  # MFA configuration - DISABLED for Sprint 1 (email-password only)
  mfa_configuration = "OFF"

  # Email configuration (using Cognito default for MVP)
  email_configuration {
    email_sending_account = "COGNITO_DEFAULT"
  }

  # User pool add-ons for security
  user_pool_add_ons {
    advanced_security_mode = "ENFORCED"
  }

  # Prevent accidental deletion
  lifecycle {
    prevent_destroy = false # Set to true in production
  }

  tags = var.tags
}

# Cognito User Pool Domain
resource "aws_cognito_user_pool_domain" "main" {
  domain       = "${var.name_prefix}-auth"
  user_pool_id = aws_cognito_user_pool.main.id
}

# Cognito User Pool Client for Web Application
resource "aws_cognito_user_pool_client" "web_app" {
  name         = "${var.name_prefix}-web-client"
  user_pool_id = aws_cognito_user_pool.main.id

  # Token validity
  access_token_validity  = 60  # 60 minutes
  id_token_validity      = 60  # 60 minutes
  refresh_token_validity = 30  # 30 days

  token_validity_units {
    access_token  = "minutes"
    id_token      = "minutes"
    refresh_token = "days"
  }

  # Authentication flows - email/password only
  explicit_auth_flows = [
    "ALLOW_USER_PASSWORD_AUTH",
    "ALLOW_REFRESH_TOKEN_AUTH",
    "ALLOW_USER_SRP_AUTH"
  ]

  # No secret for public clients (SPA/web apps)
  generate_secret = false

  # OAuth settings
  allowed_oauth_flows_user_pool_client = true
  allowed_oauth_flows                  = ["code", "implicit"]
  allowed_oauth_scopes                 = ["email", "openid", "profile"]

  # Callback URLs (update with actual frontend URLs)
  callback_urls = var.web_callback_urls
  logout_urls   = var.web_logout_urls

  # Enable token revocation
  enable_token_revocation = true

  # Prevent user existence errors (security best practice)
  prevent_user_existence_errors = "ENABLED"

  # Read and write attributes
  read_attributes = [
    "email",
    "email_verified",
    "name",
    "custom:user_type"
  ]

  write_attributes = [
    "email",
    "name",
    "custom:user_type"
  ]
}

# Cognito User Pool Client for Mobile Application
resource "aws_cognito_user_pool_client" "mobile_app" {
  name         = "${var.name_prefix}-mobile-client"
  user_pool_id = aws_cognito_user_pool.main.id

  # Token validity
  access_token_validity  = 60  # 60 minutes
  id_token_validity      = 60  # 60 minutes
  refresh_token_validity = 30  # 30 days

  token_validity_units {
    access_token  = "minutes"
    id_token      = "minutes"
    refresh_token = "days"
  }

  # Authentication flows - email/password only
  explicit_auth_flows = [
    "ALLOW_USER_PASSWORD_AUTH",
    "ALLOW_REFRESH_TOKEN_AUTH",
    "ALLOW_USER_SRP_AUTH"
  ]

  # No secret for public clients (mobile apps)
  generate_secret = false

  # OAuth settings
  allowed_oauth_flows_user_pool_client = true
  allowed_oauth_flows                  = ["code"]
  allowed_oauth_scopes                 = ["email", "openid", "profile"]

  # Callback URLs (update with actual mobile app deep links)
  callback_urls = var.mobile_callback_urls
  logout_urls   = var.mobile_logout_urls

  # Enable token revocation
  enable_token_revocation = true

  # Prevent user existence errors
  prevent_user_existence_errors = "ENABLED"

  # Read and write attributes
  read_attributes = [
    "email",
    "email_verified",
    "name",
    "custom:user_type"
  ]

  write_attributes = [
    "email",
    "name",
    "custom:user_type"
  ]
}

# User Group: Web Users
# These users have access to web application endpoints only
resource "aws_cognito_user_group" "web_users" {
  name         = "web_users"
  user_pool_id = aws_cognito_user_pool.main.id
  description  = "Users with access to web application endpoints"
  precedence   = 10
}

# User Group: Seller Users
# These users have access to seller mobile app endpoints
resource "aws_cognito_user_group" "seller_users" {
  name         = "seller_users"
  user_pool_id = aws_cognito_user_pool.main.id
  description  = "Sellers with access to mobile seller app endpoints"
  precedence   = 20
}

# User Group: Client Users
# These users have access to client mobile app endpoints
resource "aws_cognito_user_group" "client_users" {
  name         = "client_users"
  user_pool_id = aws_cognito_user_pool.main.id
  description  = "Institutional clients with access to mobile client app endpoints"
  precedence   = 30
}

# Identity Pool (optional for future AWS service access)
resource "aws_cognito_identity_pool" "main" {
  identity_pool_name               = "${var.name_prefix}-identity-pool"
  allow_unauthenticated_identities = false
  allow_classic_flow               = false

  cognito_identity_providers {
    client_id               = aws_cognito_user_pool_client.web_app.id
    provider_name           = aws_cognito_user_pool.main.endpoint
    server_side_token_check = true
  }

  cognito_identity_providers {
    client_id               = aws_cognito_user_pool_client.mobile_app.id
    provider_name           = aws_cognito_user_pool.main.endpoint
    server_side_token_check = true
  }

  tags = var.tags
}
