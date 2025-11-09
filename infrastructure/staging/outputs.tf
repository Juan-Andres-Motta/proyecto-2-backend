# Staging Environment Outputs
# Note: EC2 and ECS compute resources have been removed from staging.
# This environment maintains IAM roles, VPC, RDS database, and CloudWatch log groups.
# S3 buckets and SQS queues are accessed via common infrastructure.

output "vpc_id" {
  description = "VPC ID for staging"
  value       = module.vpc.vpc_id
}

output "public_subnet_ids" {
  description = "Public subnet IDs"
  value       = module.vpc.public_subnet_ids
}

output "alb_security_group_id" {
  description = "ALB Security Group ID"
  value       = module.security_groups.alb_security_group_id
}

output "ecs_tasks_security_group_id" {
  description = "ECS Tasks Security Group ID"
  value       = module.security_groups.ecs_tasks_security_group_id
}

output "rds_security_group_id" {
  description = "RDS Security Group ID"
  value       = module.security_groups.rds_security_group_id
}

output "rds_endpoint" {
  description = "RDS database endpoint"
  value       = module.rds_shared.db_instance_address
}

output "rds_database_name" {
  description = "RDS database name"
  value       = "medisupply"
}

output "iam_ecs_task_execution_role_arn" {
  description = "ECS Task Execution Role ARN"
  value       = module.iam.ecs_task_execution_role_arn
}

output "iam_ecs_task_role_arn" {
  description = "ECS Task Role ARN"
  value       = module.iam.ecs_task_role_arn
}

output "shared_s3_buckets" {
  description = "Shared S3 buckets accessible from common infrastructure"
  value = {
    order_reports     = data.terraform_remote_state.common.outputs.s3_order_reports_bucket_name
    inventory_reports = data.terraform_remote_state.common.outputs.s3_inventory_reports_bucket_name
    evidence          = try(data.terraform_remote_state.common.outputs.s3_evidence_bucket_name, "not yet created")
  }
}

output "shared_sqs_queue" {
  description = "Shared SQS queue accessible from common infrastructure"
  value = {
    reports_queue_url               = data.terraform_remote_state.common.outputs.sqs_reports_queue_url
    reports_queue_arn               = data.terraform_remote_state.common.outputs.sqs_reports_queue_arn
    order_events_seller_queue_url   = data.terraform_remote_state.common.outputs.sqs_order_events_seller_queue_url
    order_events_seller_queue_arn   = data.terraform_remote_state.common.outputs.sqs_order_events_seller_queue_arn
    order_events_bff_queue_url      = data.terraform_remote_state.common.outputs.sqs_order_events_bff_queue_url
    order_events_bff_queue_arn      = data.terraform_remote_state.common.outputs.sqs_order_events_bff_queue_arn
  }
}

output "shared_sns_topics" {
  description = "Shared SNS topics accessible from common infrastructure"
  value = {
    order_events_topic_arn  = data.terraform_remote_state.common.outputs.sns_order_events_topic_arn
    order_events_topic_name = data.terraform_remote_state.common.outputs.sns_order_events_topic_name
  }
}
