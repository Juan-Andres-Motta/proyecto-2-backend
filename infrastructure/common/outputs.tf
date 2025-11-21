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

# S3 Evidence Bucket Outputs
output "s3_evidence_bucket_name" {
  description = "S3 bucket name for visit evidence"
  value       = module.s3_evidence.bucket_name
}

output "s3_evidence_bucket_arn" {
  description = "S3 bucket ARN for visit evidence"
  value       = module.s3_evidence.bucket_arn
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

# SNS Order Events Topic Outputs
output "sns_order_events_topic_arn" {
  description = "SNS topic ARN for order events"
  value       = module.sns_order_events_topic.topic_arn
}

output "sns_order_events_topic_name" {
  description = "SNS topic name for order events"
  value       = module.sns_order_events_topic.topic_name
}

# SQS Order Events Queue Outputs - Seller Consumer
output "sqs_order_events_seller_queue_url" {
  description = "SQS queue URL for order events (Seller service consumer)"
  value       = module.sqs_order_events_seller_queue.queue_url
}

output "sqs_order_events_seller_queue_arn" {
  description = "SQS queue ARN for order events (Seller service consumer)"
  value       = module.sqs_order_events_seller_queue.queue_arn
}

# SQS Order Events Queue Outputs - BFF Consumer
output "sqs_order_events_bff_queue_url" {
  description = "SQS queue URL for order events (BFF service consumer)"
  value       = module.sqs_order_events_bff_queue.queue_url
}

output "sqs_order_events_bff_queue_arn" {
  description = "SQS queue ARN for order events (BFF service consumer)"
  value       = module.sqs_order_events_bff_queue.queue_arn
}

# DEPRECATED: Old single queue outputs (for backward compatibility during migration)
output "sqs_order_events_queue_url" {
  description = "DEPRECATED - SQS queue URL for order events (use service-specific queues)"
  value       = module.sqs_order_events_queue.queue_url
}

output "sqs_order_events_queue_arn" {
  description = "DEPRECATED - SQS queue ARN for order events (use service-specific queues)"
  value       = module.sqs_order_events_queue.queue_arn
}

# SQS Order Events Queue Outputs - Delivery Consumer
output "sqs_order_events_delivery_queue_url" {
  description = "SQS queue URL for order events (Delivery service consumer)"
  value       = module.sqs_order_events_delivery_queue.queue_url
}

output "sqs_order_events_delivery_queue_arn" {
  description = "SQS queue ARN for order events (Delivery service consumer)"
  value       = module.sqs_order_events_delivery_queue.queue_arn
}

# SQS Delivery Routes Generated Queue Outputs - BFF Consumer
output "sqs_delivery_routes_generated_queue_url" {
  description = "SQS queue URL for delivery routes generated events (BFF service consumer)"
  value       = module.sqs_delivery_routes_generated_queue.queue_url
}

output "sqs_delivery_routes_generated_queue_arn" {
  description = "SQS queue ARN for delivery routes generated events (BFF service consumer)"
  value       = module.sqs_delivery_routes_generated_queue.queue_arn
}

# IAM CI/CD User Outputs
output "cicd_user_name" {
  description = "IAM user name for CI/CD ECR push operations"
  value       = module.iam.cicd_user_name
}

output "cicd_user_arn" {
  description = "IAM user ARN for CI/CD ECR push operations"
  value       = module.iam.cicd_user_arn
}

# IAM ECS Task Role Outputs
output "ecs_task_execution_role_arn" {
  description = "ECS task execution role ARN"
  value       = module.iam.ecs_task_execution_role_arn
}

output "ecs_task_role_arn" {
  description = "ECS task role ARN"
  value       = module.iam.ecs_task_role_arn
}
