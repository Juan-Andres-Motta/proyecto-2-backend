# Staging Environment Outputs
# Note: EC2 and ECS compute resources have been removed from staging.
# This environment maintains IAM roles, VPC, RDS database, and CloudWatch log groups.
# S3 buckets and SQS queues are accessed via common infrastructure.

output "vpc_id" {
  description = "VPC ID for staging"
  value       = module.vpc.vpc_id
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
    reports_queue_url = data.terraform_remote_state.common.outputs.sqs_reports_queue_url
    reports_queue_arn = data.terraform_remote_state.common.outputs.sqs_reports_queue_arn
  }
}
