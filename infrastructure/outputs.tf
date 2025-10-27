# VPC Outputs
output "vpc_id" {
  description = "ID of the VPC"
  value       = module.vpc.vpc_id
}

output "public_subnet_ids" {
  description = "IDs of public subnets"
  value       = module.vpc.public_subnet_ids
}

output "private_subnet_ids" {
  description = "IDs of private subnets"
  value       = module.vpc.private_subnet_ids
}

# ALB Outputs
output "alb_dns_name" {
  description = "DNS name of the Application Load Balancer"
  value       = module.alb.alb_dns_name
}

output "alb_url" {
  description = "URL to access the Application Load Balancer"
  value       = "http://${module.alb.alb_dns_name}"
}

# Service URLs (via ALB)
output "service_urls" {
  description = "URLs to access each service via ALB"
  value = {
    for service in var.services : service => "http://${module.alb.alb_dns_name}/${service}/"
  }
}

# ECS Cluster Outputs
output "ecs_cluster_name" {
  description = "Name of the ECS cluster"
  value       = module.ecs_cluster.cluster_name
}

output "ecs_cluster_arn" {
  description = "ARN of the ECS cluster"
  value       = module.ecs_cluster.cluster_arn
}

# Service Connect Namespace
output "service_connect_namespace" {
  description = "Service Connect namespace for internal communication"
  value       = module.ecs_cluster.service_connect_namespace_name
}

# ECR Repository URLs
output "ecr_repository_urls" {
  description = "Map of service names to their ECR repository URLs"
  value = {
    for service, repo in module.ecr : service => repo.repository_url
  }
}

# ECS Service Names
output "ecs_service_names" {
  description = "Map of service names to ECS service names"
  value = {
    for service, svc in module.ecs_service : service => svc.service_name
  }
}

# CloudWatch Log Groups
output "log_group_names" {
  description = "Map of service names to CloudWatch log group names"
  value = {
    for service, log in module.cloudwatch : service => log.log_group_name
  }
}

# RDS Database Endpoints
output "rds_endpoints" {
  description = "Map of database names to their RDS endpoints"
  value = {
    catalog   = module.rds_catalog.db_instance_endpoint
    client    = module.rds_client.db_instance_endpoint
    delivery  = module.rds_delivery.db_instance_endpoint
    inventory = module.rds_inventory.db_instance_endpoint
    order     = module.rds_order.db_instance_endpoint
    seller    = module.rds_seller.db_instance_endpoint
  }
}

# RDS Database Connection Strings
output "rds_connection_strings" {
  description = "Map of database names to their connection strings"
  sensitive   = true
  value = {
    catalog   = module.rds_catalog.connection_string
    client    = module.rds_client.connection_string
    delivery  = module.rds_delivery.connection_string
    inventory = module.rds_inventory.connection_string
    order     = module.rds_order.connection_string
    seller    = module.rds_seller.connection_string
  }
}

# Cognito Authentication Outputs
output "cognito_user_pool_id" {
  description = "ID of the Cognito User Pool"
  value       = module.cognito.user_pool_id
}

output "cognito_web_client_id" {
  description = "Web application client ID"
  value       = module.cognito.web_client_id
}

output "cognito_mobile_client_id" {
  description = "Mobile application client ID"
  value       = module.cognito.mobile_client_id
}

output "cognito_user_pool_domain" {
  description = "Cognito User Pool domain"
  value       = module.cognito.user_pool_domain
}

output "cognito_jwt_issuer_url" {
  description = "JWT issuer URL for token validation"
  value       = module.cognito.jwt_issuer_url
}

output "cognito_jwks_url" {
  description = "JWKS URL for JWT signature verification"
  value       = module.cognito.jwks_url
}

output "cognito_user_groups" {
  description = "Configured Cognito user groups"
  value = {
    web_users    = module.cognito.web_users_group_name
    seller_users = module.cognito.seller_users_group_name
    client_users = module.cognito.client_users_group_name
  }
}

# Reports Infrastructure Outputs
output "s3_reports_buckets" {
  description = "S3 buckets for reports storage"
  value = {
    order     = module.s3_order_reports.bucket_name
    inventory = module.s3_inventory_reports.bucket_name
  }
}

output "sqs_reports_queue_url" {
  description = "URL of the SQS queue for report events"
  value       = module.sqs_reports_queue.queue_url
}

output "sqs_reports_queue_arn" {
  description = "ARN of the SQS queue for report events"
  value       = module.sqs_reports_queue.queue_arn
}

