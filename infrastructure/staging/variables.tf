variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

# Note: DB password is retrieved from AWS Secrets Manager (medisupply-staging-db-password)
# EC2 and ECS-related variables have been removed as compute resources are deleted
