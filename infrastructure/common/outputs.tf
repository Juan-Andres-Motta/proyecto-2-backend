# Cognito Outputs
output "cognito_user_pool_id" {
  description = "Cognito User Pool ID"
  value       = module.cognito.user_pool_id
}

output "cognito_web_client_id" {
  description = "Cognito Web Client ID"
  value       = module.cognito.web_client_id
}

output "cognito_mobile_client_id" {
  description = "Cognito Mobile Client ID"
  value       = module.cognito.mobile_client_id
}

output "cognito_jwt_issuer_url" {
  description = "Cognito JWT Issuer URL"
  value       = module.cognito.jwt_issuer_url
}

output "cognito_jwks_url" {
  description = "Cognito JWKS URL"
  value       = module.cognito.jwks_url
}

# ECR Outputs
output "ecr_repository_urls" {
  description = "ECR repository URLs for all services"
  value = {
    for service in var.services : service => module.ecr[service].repository_url
  }
}

output "ecr_repository_arns" {
  description = "ECR repository ARNs for all services"
  value = {
    for service in var.services : service => module.ecr[service].repository_arn
  }
}

# S3 Reports Buckets Outputs
output "s3_order_reports_bucket_name" {
  description = "S3 bucket name for order reports"
  value       = module.s3_order_reports.bucket_name
}

output "s3_inventory_reports_bucket_name" {
  description = "S3 bucket name for inventory reports"
  value       = module.s3_inventory_reports.bucket_name
}

# SQS Reports Queue Outputs
output "sqs_reports_queue_url" {
  description = "SQS queue URL for reports"
  value       = module.sqs_reports_queue.queue_url
}

output "sqs_reports_queue_arn" {
  description = "SQS queue ARN for reports"
  value       = module.sqs_reports_queue.queue_arn
}
