output "ecs_task_execution_role_arn" {
  description = "ARN of the ECS task execution role"
  value       = aws_iam_role.ecs_task_execution.arn
}

output "ecs_task_role_arn" {
  description = "ARN of the ECS task role"
  value       = aws_iam_role.ecs_task.arn
}

output "cicd_user_name" {
  description = "Name of the CI/CD IAM user for ECR push"
  value       = aws_iam_user.cicd_ecr_push.name
}

output "cicd_user_arn" {
  description = "ARN of the CI/CD IAM user for ECR push"
  value       = aws_iam_user.cicd_ecr_push.arn
}
