output "user_pool_id" {
  description = "The ID of the Cognito User Pool"
  value       = aws_cognito_user_pool.main.id
}

output "user_pool_arn" {
  description = "The ARN of the Cognito User Pool"
  value       = aws_cognito_user_pool.main.arn
}

output "user_pool_endpoint" {
  description = "The endpoint of the Cognito User Pool"
  value       = aws_cognito_user_pool.main.endpoint
}

output "web_client_id" {
  description = "The ID of the web application client"
  value       = aws_cognito_user_pool_client.web_app.id
}

output "mobile_client_id" {
  description = "The ID of the mobile application client"
  value       = aws_cognito_user_pool_client.mobile_app.id
}

output "web_users_group_name" {
  description = "The name of the web users group"
  value       = aws_cognito_user_group.web_users.name
}

output "seller_users_group_name" {
  description = "The name of the seller users group"
  value       = aws_cognito_user_group.seller_users.name
}

output "client_users_group_name" {
  description = "The name of the client users group"
  value       = aws_cognito_user_group.client_users.name
}

# Output the issuer URL for JWT validation in BFF
output "jwt_issuer_url" {
  description = "The issuer URL for JWT token validation"
  value       = "https://cognito-idp.${data.aws_region.current.name}.amazonaws.com/${aws_cognito_user_pool.main.id}"
}

# Output JWKS URL for JWT signature verification
output "jwks_url" {
  description = "The JWKS URL for JWT signature verification"
  value       = "https://cognito-idp.${data.aws_region.current.name}.amazonaws.com/${aws_cognito_user_pool.main.id}/.well-known/jwks.json"
}

# Get current AWS region
data "aws_region" "current" {}
