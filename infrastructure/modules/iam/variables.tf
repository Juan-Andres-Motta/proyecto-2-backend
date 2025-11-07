variable "name_prefix" {
  description = "Prefix for resource names"
  type        = string
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default     = {}
}

variable "ecr_repository_arns" {
  description = "List of ECR repository ARNs for CI/CD push access"
  type        = list(string)
  default     = []
}
