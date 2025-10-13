variable "name_prefix" {
  description = "Prefix for resource names"
  type        = string
}

variable "service_name" {
  description = "Name of the service"
  type        = string
}

variable "image_uri" {
  description = "URI of the Docker image in ECR"
  type        = string
}

variable "cpu" {
  description = "CPU units for the task (256 = 0.25 vCPU)"
  type        = string
  default     = "256"
}

variable "memory" {
  description = "Memory in MB for the task"
  type        = string
  default     = "512"
}

variable "execution_role_arn" {
  description = "ARN of the task execution role"
  type        = string
}

variable "task_role_arn" {
  description = "ARN of the task role"
  type        = string
}

variable "environment_variables" {
  description = "Environment variables for the container"
  type        = map(string)
  default     = {}
}

variable "log_group_name" {
  description = "Name of the CloudWatch log group"
  type        = string
}

variable "aws_region" {
  description = "AWS region"
  type        = string
}

variable "container_port" {
  description = "Port the container listens on"
  type        = number
  default     = 8000
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default     = {}
}

variable "health_check_path" {
  description = "Health check path for the container"
  type        = string
  default     = "/health"
}
