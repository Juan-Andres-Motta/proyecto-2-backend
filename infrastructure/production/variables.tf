variable "aws_region" {
  description = "AWS region where resources will be created"
  type        = string
  default     = "us-east-1"
}

variable "services" {
  description = "List of microservices that need ECR repositories"
  type        = list(string)
  default = [
    "bff",
    "catalog",
    "client",
    "delivery",
    "inventory",
    "order",
    "seller"
  ]
}

variable "db_master_password" {
  description = "Master password for all RDS databases (deprecated - now using AWS Secrets Manager)"
  type        = string
  sensitive   = true
  default     = ""  # Not used - password retrieved from AWS Secrets Manager
}
